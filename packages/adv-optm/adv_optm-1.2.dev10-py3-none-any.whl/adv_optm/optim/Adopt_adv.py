import torch
from typing import Callable, Optional

from ..util.BF16_Stochastic_Rounding import add_stochastic_
from ..util.Effective_Shape import _get_effective_shape
from ..util.NNMF import _nnmf, _unnmf
from ..util.OrthoGrad import _orthogonalize_gradient
from ..util.One_Bit_Boolean import _pack_bools, _unpack_bools
from ..util.Kourkoutas import KourkoutasHelper

class Adopt_adv(torch.optim.Optimizer):
    """
    Implements an advanced ADOPT algorithm.

    The ADOPT update rule modifies Adam by:
    1.  **Initialization:** The second moment `v` is initialized as `v₀ = g₀²`.
    2.  **Decorrelation:** The current gradient is normalized using the second-moment estimate
        from the *previous* step (`v_{t-1}`).
    3.  **Order of Operations:** This normalization occurs *before* updating the
        first-moment (momentum) estimate.

    Args:
        params (iterable): iterable of parameters to optimize or dicts defining
            parameter groups
        lr (float): learning rate (default: 1e-4)
        betas (tuple[float, float]): coefficients used for computing running
            averages of momentum and variance (default: (0.9, 0.9999))
        eps (float): term added to the denominator to improve
            numerical stability (default: 1e-6)
        weight_decay (float): weight decay (L2 penalty) (default: 0)
        clip_lambda (Callable, optional): A function that takes the current step
            and returns a value to clip the normalized gradient. Only used when
            `use_atan2` is False. (default: `lambda step: step**0.25`)
        vector_reshape (bool): whether to reshape 1D vectors into 2D
            matrices for low-rank compression (default: True).
        stochastic_rounding (bool): whether to use stochastic
            rounding for BF16 parameter updates (default: True).
        use_atan2 (bool): whether to use an atan2-based normalization, which can
            improve stability by removing the need for `eps`. (default: False)
        cautious_mask (bool):  whether to use cautious masking to align the gradient's
            direction with the first moment's.  (default: False)
        grams_moment (bool): whether to combine the gradient's direction with the
            first moment's magnitude (default: False).
        orthogonal_gradient (bool): whether to use OrthoGrad. (default: False)
        use_AdEMAMix (bool): whether to enable the AdEMAMix feature. This adds
            a second, slow-moving average of the momentum (`mt_slow`) which is
            combined with the primary momentum (`mt`) to stabilize updates,
            especially in noisy, small-batch settings. If `False`, the
            optimizer behaves as standard ADOPT. (default: False)
        beta3_ema (float): The decay rate for the slow exponential moving average of
            the momentum (only used when `use_AdEMAMix` is `True`). A higher
            value (e.g., 0.9999) gives the EMA a longer memory, making it more
            stable but slower to adapt. A lower value (e.g., 0.999) is often
            better for shorter training runs. (default: 0.9999)
        alpha (float): The mixing coefficient that scales the slow momentum term
            before it is added to the fast momentum term (`update = mt + alpha * mt_slow`).
            A higher value increases the stabilizing influence of the slow
            momentum. (default: 5.0)
        t_alpha (Optional[int]): The number of steps for a linear warmup of the
            `alpha` parameter (only used when `use_AdEMAMix` is `True`). This is
            highly recommended to prevent instability at the beginning of training,
            as it gradually introduces the stabilizing slow momentum term. During
            the warmup, `alpha` ramps from 0 to its target value. If `None`,
            the scheduler is disabled and the full `alpha` value is used from
            the start. (default: None)
        Simplified_AdEMAMix (bool): whether to use the Simplified AdEMAMix update rule.
            This changes the EMA to accumulator and the update numerator to `alpha_grad * grad + mt`, which can be
            more responsive, especially for small batch sizes. Enabling this will
            automatically disable `use_AdEMAMix`, `cautious_mask`, `grams_moment`,
            and `use_atan2`. (default: False)
        alpha_grad (float): Mixing coefficient for the Simplified AdEMAMix update rule
            (only used when `Simplified_AdEMAMix` is `True`). Controls the weight of the
            current gradient. For small batch sizes, use high values (e.g., 10-100) to be
            more responsive. For large batch sizes, use low values (e.g., 0-1) for
            stability. (default: 100.0)
        kourkoutas_beta (bool): whether to enable the layer-wise dynamic β₂ logic.
            If `False`, the optimizer behaves as standard Adopt. (default: False)
        beta2_min (float): The minimum value for dynamic β₂, used during periods of
            high gradient variance ("sunspikes"). Must be less than `betas[1]`.
            (default: 0.88)
        ema_alpha (float): The decay rate for the Exponential Moving Average (EMA) of
            the pooled gradient norms. Corresponds to `α` in the paper.
            (default: 0.93)
        tiny_spike (float): A small constant added to the denominator of the
            "sunspike" ratio calculation to prevent division by zero. Corresponds
            to `ε_spike` in the paper. (default: 1e-9)
        k_warmup_steps (int): The number of initial steps during which β₂ is held
            at a fixed beta2 value before the
            dynamic logic activates. (default: 0)
        k_logging (int): if > 0 and kourkoutas_beta=True, enables periodic console
            logging of Kourkoutas-β statistics (min, max, mean of `β₂` across layers)
            every logging steps. Useful for debugging and tuning. Set to 0 to disable
            logging (default: 0). 
        layer_key_fn (Optional[Callable]): A function that takes a parameter `p`
            and returns a unique, hashable key representing its "layer" or "bucket".
            If `None`, parameters are bucketed by their memory ID (tensor-wise).
            (default: None)
        nnmf_factor (bool): whether to use the factorization or disable it to use
            the uncompressed optimizer. (default: False)
    """

    def __init__(
        self,
        params,
        lr: float = 1e-4,
        betas: tuple[float, float] = (0.9, 0.9999),
        eps: float = 1e-6,
        weight_decay: float = 0.0,
        clip_lambda: Optional[Callable[[int], float]] = lambda step: step**0.25,
        vector_reshape: bool = True,
        stochastic_rounding: bool = True,
        use_atan2: bool = False,
        cautious_mask: bool = False,
        grams_moment: bool = False,
        orthogonal_gradient: bool = False,
        use_AdEMAMix: bool = False,
        beta3_ema: float = 0.9999,
        alpha: float = 5.0,
        t_alpha: int | None = None,
        Simplified_AdEMAMix: bool = False,
        alpha_grad: float = 100.0,
        kourkoutas_beta: bool = False,
        beta2_min: float = 0.9,
        ema_alpha: float = 0.95,
        tiny_spike: float = 1e-9,
        k_warmup_steps: int = 0,
        k_logging: int = 0,
        layer_key_fn: Optional[Callable] = None,
        nnmf_factor: bool = False,
    ):
        if not (lr >= 0.0):
            raise ValueError(f"Learning-rate should be >= 0.0. Got {lr}")
        if not (0.0 <= betas[0] < 1.0 and 0.0 <= betas[1] < 1.0):
            raise ValueError(f"Betas should be in [0.0, 1.0). Got {betas}")
        if not (eps >= 0.0):
            raise ValueError(f"Epsilon should be >= 0.0. Got {eps}")
        if not (weight_decay >= 0.0):
            raise ValueError(f"Weight-decay should be >= 0.0. Got {weight_decay}")
        if cautious_mask and grams_moment:
            print("Warning: cautious is incompatible with grams, Disabling cautious.")
            cautious_mask = False
        if betas[0] == 0.0 and Simplified_AdEMAMix:
            raise ValueError(f"Beta1 cannot be 0.0 when using Simplified_AdEMAMix. Got {betas[0]}")
        if kourkoutas_beta and not (betas[1] > beta2_min): raise ValueError(f"For Kourkoutas-β, betas[1] (as beta2_max) must be > beta2_min. Got {betas[1]} and {beta2_min}")
        if use_AdEMAMix and Simplified_AdEMAMix:
            print("Warning: use_AdEMAMix is incompatible with Simplified_AdEMAMix, Disabling use_AdEMAMix.")
        if grams_moment and Simplified_AdEMAMix:
            print("Warning: grams is incompatible with Simplified_AdEMAMix, Disabling grams.")
        if cautious_mask and Simplified_AdEMAMix:
            print("Warning: cautious is incompatible with Simplified_AdEMAMix, Disabling cautious.")

        defaults = {
            "lr": lr, "betas": betas, "eps": eps, "weight_decay": weight_decay,
            "vector_reshape": vector_reshape, "beta3_ema": beta3_ema, "alpha": alpha,
            "t_alpha": t_alpha, "alpha_grad": alpha_grad, 
            "kourkoutas_beta": kourkoutas_beta, "beta2_min": beta2_min, "ema_alpha": ema_alpha,
            "tiny_spike": tiny_spike, "k_warmup_steps": k_warmup_steps, "k_logging": k_logging,
        }
        self.clip_lambda = clip_lambda
        self.stochastic_rounding = stochastic_rounding
        self.use_atan2 = use_atan2 and not Simplified_AdEMAMix
        self.cautious_mask = cautious_mask and not Simplified_AdEMAMix
        self.grams_moment = grams_moment and not Simplified_AdEMAMix
        self.orthogonal_gradient = orthogonal_gradient
        self.use_AdEMAMix = use_AdEMAMix and not Simplified_AdEMAMix
        self.Simplified_AdEMAMix = Simplified_AdEMAMix
        self.factored = nnmf_factor
        self.kourkoutas_beta = kourkoutas_beta
        self.layer_key_fn = layer_key_fn
        super().__init__(params, defaults)

        if self.kourkoutas_beta:
            self.kourkoutas_helper = KourkoutasHelper(self)

    @property
    def supports_fused_back_pass(self): return True
    @property
    def supports_memory_efficient_fp16(self): return True
    @property
    def supports_flat_params(self): return False

    @torch.no_grad()
    def step_parameter(self, p: torch.Tensor, group: dict, i: int | None = None):
        if p.grad is None:
            return

        grad = p.grad
        if self.factored and grad.dtype != torch.float32:
            grad = grad.float()
        if self.orthogonal_gradient:
            grad = _orthogonalize_gradient(p, grad)
        state = self.state[p]

        # State Initialization
        if 'step' not in state:
            state['step'] = 0

            should_factor = (
                self.factored and
                not (len(p.shape) == 1 and not group['vector_reshape'])
            )

            state['factored'] = should_factor

            dtype = torch.float32 if self.factored else p.dtype

            if state['factored']:
                state['effective_shape'] = _get_effective_shape(p.numel())
                d1, d2 = state['effective_shape']

                # m_0 = 0
                if group['betas'][0] > 0:
                    state['mu_m_nmf'] = torch.zeros(d1, device=p.device, dtype=dtype) 
                    state['mv_m_nmf'] = torch.zeros(d2, device=p.device, dtype=dtype)
                    if not self.grams_moment:
                        packed_d2 = (d2 + 7) // 8
                        state['sign'] = torch.zeros((d1, packed_d2), dtype=torch.uint8, device=p.device)
                if self.use_AdEMAMix:
                    state['mu_m_slow_nmf'] = torch.zeros(d1, device=p.device, dtype=dtype) 
                    state['mv_m_slow_nmf'] = torch.zeros(d2, device=p.device, dtype=dtype)
                    packed_d2 = (d2 + 7) // 8
                    state['sign_slow'] = torch.zeros((d1, packed_d2), dtype=torch.uint8, device=p.device)
                # v_0 = g_0^2 (SMMF_ADOPT NMF storage)
                vt_init = grad.view(d1, d2).square_()
                # Allocate NMF factors for v
                state['mu_v_nmf'] = torch.zeros(d1, device=p.device, dtype=dtype) 
                state['mv_v_nmf'] = torch.zeros(d2, device=p.device, dtype=dtype)
                # Initialize v_0 using NMF
                _nnmf(vt_init, out=(state['mu_v_nmf'], state['mv_v_nmf']))
            else: # Fallback for non-factored tensors
                if group['betas'][0] > 0:
                    state['exp_avg'] = torch.zeros_like(p, dtype=dtype) # m_0
                if self.use_AdEMAMix:
                    state['exp_avg_slow'] = torch.zeros_like(p, dtype=dtype)
                state['exp_avg_sq'] = grad.square()   # v_0

        beta1, beta2 = group['betas']

        current_step = state['step']
        if group.get('kourkoutas_beta', False):
            # Call prepare_step() once at the beginning of the step for all params
            self.kourkoutas_helper.maybe_prepare_step(current_step)
            # Accumulate current grad's norm for the *next* step
            self.kourkoutas_helper.accumulate_gradient_sq_norm(p, grad)
            # Get the dynamic beta2 calculated in prepare_step()
            beta2 = self.kourkoutas_helper.get_beta2(p, group, current_step)

        # The first step is for initialization only (skip when use_atan2 as it's scale invariant).
        if state['step'] == 0 and not self.use_atan2:
            state['step'] += 1
            return

        if self.use_AdEMAMix:
            beta3_ema = group['beta3_ema']
            alpha = group['alpha']
            t_alpha = group['t_alpha']
            # Use step+1 for 1-based step count in scheduler
            alpha_step = state['step'] + 1
            alpha_t = alpha
            if t_alpha is not None and t_alpha > 0 and alpha_step < t_alpha:
                alpha_t = min(alpha_step * alpha / t_alpha, alpha)
        if self.Simplified_AdEMAMix:
            alpha_grad = group["alpha_grad"]

        if state['factored']:
            d1, d2 = state['effective_shape']

            # Reconstruct m_{t-1}
            if beta1 > 0:
                mt = _unnmf((state['mu_m_nmf'], state['mv_m_nmf']))
                if not self.grams_moment:
                    if state['sign'].dtype != torch.uint8:
                        state['sign'] = state['sign'].to(torch.uint8)
                    unpacked_sign = _unpack_bools(state['sign'], original_m=d2)
                    torch.where(unpacked_sign, mt, -mt, out=mt)
                    del unpacked_sign

            # Reconstruct AdEMAMix EMA
            if self.use_AdEMAMix:
                mt_slow = _unnmf((state['mu_m_slow_nmf'], state['mv_m_slow_nmf']))
                if state['sign_slow'].dtype != torch.uint8:
                    state['sign_slow'] = state['sign_slow'].to(torch.uint8)
                unpacked_sign_slow = _unpack_bools(state['sign_slow'], original_m=d2)
                torch.where(unpacked_sign_slow, mt_slow, -mt_slow, out=mt_slow)
                del unpacked_sign_slow

            # Reconstruct v_{t-1} using NNMF
            vt = _unnmf((state['mu_v_nmf'], state['mv_v_nmf']))

            # ADOPT Step A: Decorrelate g_t using v_{t-1}
            grad_reshaped = grad.view(d1, d2)
            denom = vt.sqrt()

            if self.use_atan2:
                normalized_grad = torch.atan2(grad_reshaped, denom)
            else:
                normalized_grad = grad_reshaped / denom.add_(group['eps'])
                if self.clip_lambda is not None:
                    clip_val = self.clip_lambda(state['step'])
                    normalized_grad.clamp_(-clip_val, clip_val)
            del denom

            # ADOPT Step B: Update momentum m_t using normalized gradient
            if beta1 > 0:
                if self.Simplified_AdEMAMix:
                    mt.mul_(beta1).add_(normalized_grad, alpha=1.0)
                else:
                    mt.mul_(beta1).add_(normalized_grad, alpha=1.0 - beta1)
                if self.grams_moment:
                    mt = grad_reshaped.sign() * mt.abs()
                elif self.cautious_mask:
                    mask = (mt * grad_reshaped > 0).to(grad_reshaped.dtype)
                    mask.div_(mask.mean().clamp_(min=1e-3))
                    mt.mul_(mask)
                    del mask

            if self.use_AdEMAMix:
                mt_slow.mul_(beta3_ema).add_(normalized_grad, alpha=1.0 - beta3_ema)
                if beta1 > 0:
                    update = torch.add(mt, mt_slow, alpha=alpha_t)
                else:
                    update = torch.add(normalized_grad, mt_slow, alpha=alpha_t)
            elif self.Simplified_AdEMAMix:
                update = torch.add(mt, normalized_grad, alpha=alpha_grad)
            else:
                update = mt.clone() if beta1 > 0 else normalized_grad

            update = update.view(p.shape)

            if self.use_atan2:
                update.mul_(group['lr'] * 1.2732395447351628)
            else:
                update.mul_(group['lr']) 

            # Update second moment v_t for the *next* step using raw g_t
            vt.mul_(beta2).addcmul_(grad_reshaped, grad_reshaped, value=1.0 - beta2)
            del grad_reshaped

            # Compress and store new factors
            if beta1 > 0:
                if not self.grams_moment:
                    state['sign'] = _pack_bools(mt > 0)
                _nnmf(mt.abs(), out=(state['mu_m_nmf'], state['mv_m_nmf']))
                del mt

            if self.use_AdEMAMix:
                state['sign_slow'] = _pack_bools(mt_slow > 0)
                _nnmf(mt_slow.abs(), out=(state['mu_m_slow_nmf'], state['mv_m_slow_nmf']))
                del mt_slow

            # factorize v_t using NMF compression
            _nnmf(vt, out=(state['mu_v_nmf'], state['mv_v_nmf']))
            del vt

        else: # Standard ADOPT logic for non-factored tensors
            v = state['exp_avg_sq'] # v_{t-1}                

            # ADOPT Step A: Decorrelate g_t using v_{t-1}
            denom = v.sqrt()

            if self.use_atan2:
                normalized_grad = torch.atan2(grad, denom)
            else:
                normalized_grad = grad / denom.add_(group['eps'])
                if self.clip_lambda is not None:
                    clip_val = self.clip_lambda(state['step'])
                    normalized_grad.clamp_(-clip_val, clip_val)
            del denom

            # ADOPT Step B: Update momentum m_t
            if beta1 > 0:
                m = state['exp_avg'] # m_{t-1},
                if self.Simplified_AdEMAMix:
                    m.mul_(beta1).add_(normalized_grad, alpha=1.0)
                else:
                    m.mul_(beta1).add_(normalized_grad, alpha=1.0 - beta1)

            if self.grams_moment:
                m = grad.sign() * m.abs()
            elif self.cautious_mask:
                mask = (m * grad > 0).to(grad.dtype)
                mask.div_(mask.mean().clamp_(min=1e-3))
                m.mul_(mask)
                del mask

            if self.use_AdEMAMix:
                m_slow = state['exp_avg_slow']
                m_slow.mul_(beta3_ema).add_(normalized_grad, alpha=1.0 - beta3_ema)
                if beta1 > 0:
                    update = torch.add(m, m_slow, alpha=alpha_t)
                else:
                    update = torch.add(normalized_grad, m_slow, alpha=alpha_t)
            elif self.Simplified_AdEMAMix:
                update = torch.add(m, normalized_grad, alpha=alpha_grad)
            else:
                update = m.clone() if beta1 > 0 else normalized_grad

            if self.use_atan2:
                update.mul_(group['lr'] * 1.2732395447351628)
            else:
                update.mul_(group['lr']) 

            # Update second moment v_t for the next step using raw g_t
            v.mul_(beta2).addcmul_(grad, grad.conj(), value=1 - beta2)

        # Parameter Update
        if group["weight_decay"] != 0:
            if p.dtype == torch.bfloat16 and self.stochastic_rounding:
                add_stochastic_(p.data, p.data, alpha=-group["weight_decay"] * group["lr"])
            else:
                p.data.add_(p.data, alpha=-group["weight_decay"] * group["lr"])

        if p.dtype == torch.bfloat16 and self.stochastic_rounding:
            add_stochastic_(p.data, -update)
        else:
            p.data.add_(-update)
        del update

        state['step'] += 1

    @torch.no_grad()
    def step(self, closure=None):
        """Performs a single optimization step."""
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            for i, p in enumerate(group['params']):
                self.step_parameter(p, group, i)

        return loss
import torch

def _orthogonalize_gradient(p: torch.Tensor, grad: torch.Tensor) -> torch.Tensor:
    """Projects the gradient `grad` to be orthogonal to the parameter `p`."""
    if grad.is_sparse: raise RuntimeError("OrthoGrad logic does not support sparse gradients.")
    original_shape = grad.shape
    original_dtype = grad.dtype
    w = p.view(-1).float()
    g = grad.view(-1).float()
    w_norm_sq = torch.dot(w, w).add_(1e-30)
    proj = torch.dot(w, g) / w_norm_sq
    g_orth = g.sub(w, alpha=proj)
    g_norm = g.norm(2)
    g_orth_norm = g_orth.norm(2).add_(1e-30)
    g_orth_scaled = g_orth * (g_norm / g_orth_norm)
    return g_orth_scaled.view(original_shape).to(original_dtype)
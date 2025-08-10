from __future__ import annotations
import numpy as np

# Eq. (2): cosine similarity
def cosine_sim(ei: np.ndarray, ej: np.ndarray) -> float:
    ni = np.linalg.norm(ei); nj = np.linalg.norm(ej)
    if ni == 0 or nj == 0: return 0.0
    return float(np.dot(ei, ej) / (ni * nj))

# Eq. (24): Euclidean distance metric
def d_metric(ei: np.ndarray, ej: np.ndarray) -> float:
    return float(np.linalg.norm(ei - ej))

# Eq. (25): semantic density ρ (Gaussian bumps)
def rho_density(points: np.ndarray, grid: np.ndarray, bandwidth: float = 1.0) -> np.ndarray:
    diffs = grid[:, None, :] - points[None, :, :]
    sq = np.sum(diffs**2, axis=-1)
    val = np.exp(-sq / (2 * bandwidth**2)).sum(axis=1)
    return val

# Φ and F = -∇Φ (Eq. (26)) on a 2D grid
def potential_phi(grid: np.ndarray, density: np.ndarray, alpha: float = 1.0) -> np.ndarray:
    return -alpha * density

def force_from_phi(grid: np.ndarray, phi: np.ndarray, grid_shape: tuple[int, int]) -> np.ndarray:
    H, W = grid_shape
    phi2 = phi.reshape(H, W)
    gx = np.zeros_like(phi2); gy = np.zeros_like(phi2)
    gx[:, 1:-1] = (phi2[:, 2:] - phi2[:, :-2]) / 2.0
    gy[1:-1, :] = (phi2[2:, :] - phi2[:-2, :]) / 2.0
    Fx = -gx; Fy = -gy
    return np.stack([Fx, Fy], axis=-1).reshape(H*W, 2)

# Eq. (31): de/dt = V(e,t)  (discrete)
def advect_positions(pos: np.ndarray, V: np.ndarray, dt: float = 0.08) -> np.ndarray:
    return pos + dt * V

# Eq. (37): edge weight update (discrete)
def update_edge_weight(w: float, A: float, D: float, C: float,
                       alpha: float=0.2, beta: float=0.05, gamma: float=0.1, dt: float=1.0) -> float:
    dw = alpha*A - beta*D + gamma*C
    return max(0.0, w + dt*dw)

# Eq. (88): drift D_n = ||s0 - sn||
def drift(s0: np.ndarray, sn: np.ndarray) -> float:
    return float(np.linalg.norm(s0 - sn))

# Eq. (89)/(90): entropy from discrete probabilities
def entropy_from_probs(p: np.ndarray, eps: float=1e-12) -> float:
    p = np.clip(p, eps, 1.0); p = p / p.sum()
    return float(-np.sum(p*np.log(p)))

# Simple state-update operators F(S, R, U)
def F_nonlinear(S: np.ndarray, R_ctx: np.ndarray, U: np.ndarray) -> np.ndarray:
    return np.tanh(S + 0.6*R_ctx + 0.2*U)

def stabilizing_flow(S: np.ndarray, target: np.ndarray, k: float=0.02) -> np.ndarray:
    return S + k*(target - S)

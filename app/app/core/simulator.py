import math
import time
import numpy as np

class DynParams:
    def __init__(self):
        self.dt = 0.02
        self.pull_k = 0.01
        self.edge_threshold = 0.06
        self.alpha = 0.20  # A (sim)
        self.beta  = 0.05  # D (dist)
        self.gamma = 0.10  # C (consistency)

class DynamathSimulator:
    def __init__(self, n=12, seed=0):
        rng = np.random.default_rng(seed)
        # embeddings (2D)
        self.E = rng.normal(0.0, 0.2, size=(n,2)) + np.array([1.2,0.60])
        # internal states
        self.S = rng.normal(0.0, 0.1, size=(n,4))
        self.S0 = self.S.copy()

        self.W = np.zeros((n,n), dtype=np.float32)
        self.params = DynParams()

        # sensor (webcam) input
        self.sensor = dict(motion=0.0, brightness=0.0, hue=0.0, rgb=[0.0,0.0,0.0])

        # precompute neighbors (k-NN=3) indices per step
        self.k_neighbors = 3

    def set_params(self, payload: dict):
        p = self.params
        p.dt = float(payload.get("speed_dt", p.dt))
        p.pull_k = float(payload.get("pull_k", p.pull_k))
        p.edge_threshold = float(payload.get("edge_threshold", p.edge_threshold))
        p.alpha = float(payload.get("alpha", p.alpha))
        p.beta  = float(payload.get("beta", p.beta))
        p.gamma = float(payload.get("gamma", p.gamma))

    def set_sensor(self, payload: dict):
        # expected keys: motion [0..1], brightness [0..1], hue [-pi..pi], rgb [r,g,b] each 0..1
        self.sensor["motion"] = float(payload.get("motion", 0.0))
        self.sensor["brightness"] = float(payload.get("brightness", 0.0))
        self.sensor["hue"] = float(payload.get("hue", 0.0))
        rgb = payload.get("rgb", [0.0,0.0,0.0])
        if isinstance(rgb, (list,tuple)) and len(rgb)==3:
            self.sensor["rgb"] = [float(rgb[0]), float(rgb[1]), float(rgb[2])]

    def _cos_sim(self, A, B):
        num = (A*B).sum(axis=-1)
        den = np.linalg.norm(A,axis=-1)*np.linalg.norm(B,axis=-1) + 1e-8
        return num / den

    def _knn(self):
        # naive pairwise; n is tiny
        D = np.linalg.norm(self.E[:,None,:] - self.E[None,:,:], axis=-1)
        idx = np.argsort(D, axis=1)[:,1:self.k_neighbors+1]
        return idx, D

    def _field_force(self):
        # density via simple RBF sum => potential Φ = -α * ρ ; F = -∇Φ
        E = self.E
        n = E.shape[0]
        F = np.zeros_like(E)
        for i in range(n):
            diff = E[i] - E
            r2 = (diff**2).sum(axis=1) + 1e-6
            w = np.exp(-r2 / 0.05)   # smooth local density
            grad = (diff * w[:,None]).sum(axis=0)
            F[i] = -grad            # toward higher density
        return F

    def _update_edges(self, D):
        # Eq. (37): dw/dt = αA - βD + γC  (discrete add)
        A = np.zeros_like(D)
        C = np.zeros_like(D)
        # cos-sim on embeddings (2D)
        for i in range(self.E.shape[0]):
            for j in range(self.E.shape[0]):
                if i==j: continue
                A[i,j] = self._cos_sim(self.E[i:i+1], self.E[j:j+1])[0]
                C[i,j] = 1.0 / (1e-4 + np.linalg.norm(self.S[i]-self.S[j]))
        self.W += self.params.alpha*A - self.params.beta*D + self.params.gamma*C
        self.W = np.clip(self.W, 0.0, 1e9)

    def _advect_embeddings_with_sensor(self):
        mot = self.sensor["motion"]      # 0..1
        hue = self.sensor["hue"]         # -pi..pi
        # direction from hue, amplitude from motion and brightness
        amp = 0.05 * mot * (0.2 + 0.8*self.sensor["brightness"])
        dx = amp * math.cos(hue)
        dy = amp * math.sin(hue)
        self.E += np.array([dx, dy])    # same small push to all nodes (global flow)

    def step(self):
        # 1) neighbors & distances
        idx, D = self._knn()

        # 2) embedding flow from field force
        F = self._field_force()
        self.E += self.params.dt * F

        # 2b) sensor-driven advection (Δe(U_t))
        self._advect_embeddings_with_sensor()

        # 3) state update S ← tanh(S + a·Rctx + b·U)
        Rctx = np.array([ self.S[nbrs].mean(axis=0) for nbrs in idx ])
        U = np.array([
            self.sensor["motion"],
            self.sensor["brightness"],
            self.sensor["hue"]/math.pi,      # normalize to [-1,1]
            sum(self.sensor["rgb"])/3.0
        ], dtype=np.float32)
        self.S = np.tanh(self.S + self.params.alpha*Rctx + self.params.beta*U)

        # 4) edges
        self._update_edges(D)

        # metrics
        drift = float(np.linalg.norm(self.S0 - self.S))
        # entropy over normalized |S| magnitudes
        mags = np.abs(self.S).mean(axis=1) + 1e-9
        p = mags / mags.sum()
        entropy = float(-(p*np.log(p)).sum())
        return drift, entropy

    def snapshot(self):
        # edge list above threshold
        th = self.params.edge_threshold * 3.2e7  # keep earlier visual scale
        edges = []
        n = self.E.shape[0]
        for i in range(n):
            for j in range(i+1,n):
                w = float(self.W[i,j])
                if w>th:
                    edges.append([i,j,w])
        return {
            "emb": self.E.tolist(),
            "edges": edges
        }

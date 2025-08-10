# Dynamath CPU Live (v7) — Dynamic Graph Formalism with Real-Time Video Input

## Abstract
This repository contains the CPU-only (Docker-based, version 7) implementation of the **Dynamath** formalism, extended with **real-time webcam video ingestion** for live perturbation of a dynamic graph. It serves both as a demonstration platform and as an experimental testbed for verifying the formalism’s predictive capabilities regarding **drift**, **entropy**, and **topological state-space changes** under continuously varying input conditions. The system operates fully on CPU without GPU acceleration, making it accessible for reproducibility on standard research workstations.

**Reference to formalism description:**
- Zenodo DOI: [https://zenodo.org/records/16762105](https://zenodo.org/records/16762105)
- Live web interface: [https://dynamath-dynaflow.vercel.app/](https://dynamath-dynaflow.vercel.app/)

## 1. Scientific Motivation
The **Dynamath** framework models evolving systems as **weighted dynamic graphs** with time-dependent node states and distance-modulated connectivity. This build extends prior work by introducing a **live sensory channel** (video feed) to:
- Induce structured, non-random perturbations
- Measure the correlation between **input complexity** and **drift magnitude**
- Observe entropy changes as a proxy for **information assimilation**

## 2. Theoretical Context
The formalism treats:
- **β** = *D(dist)* as a control parameter linking **distance metrics** to system reactivity
- **A** = similarity function (A=sim)
- **Entropy H(p)** as a measure of distributional complexity
- **Drift** = |Sₜ − Sₜ₋₁| as the absolute change in system state per time step

**Hypothesis tested in this build:**
> A continuous, structured input (even at low resolution, e.g., 140p) induces sustained drift modulation and entropy variation beyond stochastic baseline noise.

## 3. Experimental Setup

### 3.1 Software Environment
- CPU-only Docker container (no GPU dependencies)
- Web-based UI for controlling parameters and enabling webcam feed
- Live graph visualization with concurrent numeric telemetry

### 3.2 Video Input
- Live webcam stream (tested at 140p–720p)
- Frame data converted into input perturbations for node features
- Adjustable `β (D=dist)` parameter influences drift amplification

### 3.3 Key Observables
- **Drift dynamics** (primary metric)
- **Entropy variation** over time
- Graph topology changes (node rearrangement, edge weight redistribution)

## 4. Confirmed Properties

| Property | Observation | Implication |
|----------|-------------|-------------|
| Continuity of state evolution for small `dt` | No discontinuities observed | Stability of iterative solver |
| Graph reactivity to A=sim, D=dist | Structural changes match input complexity | Confirms functional link between similarity and distance metrics |
| Correlation of β and drift amplitude | Higher β increases drift sensitivity | β is a reliable tuning parameter |
| Entropy fluctuation with live input | Strong correlation with drift peaks | Supports hypothesis of information uptake |
| Persistent non-zero drift with static scene noise | Drift remains above baseline | Suggests minimal stochastic leakage |

## 5. How to Reproduce

### 5.1 Build and Run
```bash
docker build -t dynamath-v7 .
docker run -p 8000:8000 dynamath-v7
```

### 5.2 Access
Open [http://localhost:8000](http://localhost:8000) in your browser.

### 5.3 Parameters
- `β (D=dist)` — controls drift amplitude
- `dt` — integration step size
- `cam` — toggles webcam input

## 6. Suggested Experimental Protocol
1. Start container and enable webcam (`cam` toggle).
2. Set baseline parameters:
   - `β = 0.5`
   - `dt = 0.01`
3. Record baseline drift and entropy with camera covered.
4. Introduce controlled motion in front of the camera (hand movement, object rotation).
5. Observe:
   - Drift magnitude increase relative to baseline
   - Entropy spikes following structured motion
   - Graph node rearrangements
6. Repeat with varying `β` values (0.2, 0.8, 1.2) to confirm sensitivity scaling.

## 7. Interpretation of Results
- Sustained drift under live input indicates active adaptation of the state space, not random walk noise.
- Entropy fluctuations correspond to complexity variation in the incoming signal.
- The ability to modulate `β` and observe proportional changes in drift validates the formalism’s predictive capacity for parameter sensitivity.

## 8. Broader Implications
This build demonstrates that **Dynamath** can be extended into sensory-reactive computation domains, enabling:
- Real-time signal classification
- Adaptive control systems
- Formalism-based anomaly detection

By bridging theoretical constructs with empirical, measurable phenomena, this setup provides a reproducible framework for cross-laboratory verification.

## References
- Formalism Record — [https://zenodo.org/records/16762105](https://zenodo.org/records/16762105)
- Live Web Interface — [https://dynamath-dynaflow.vercel.app/](https://dynamath-dynaflow.vercel.app/)
- Associated mathematical derivations and theoretical framework — see Zenodo record.

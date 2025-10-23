# Algorithm Details

**Purpose**: Detailed explanations of detection algorithms and cryptographic methods used in Argus.

## Graph-Theoretic Detection

### Spectral Analysis

**Based on**: Laplacian eigenvalue monitoring

**Theory**:
The graph Laplacian is defined as `L = D - A`, where:

- `D` is the degree matrix (diagonal with node degrees)
- `A` is the adjacency matrix

Eigenvalues of the Laplacian (`λ₁ ≤ λ₂ ≤ ... ≤ λₙ`) reveal structural properties:

- `λ₁ = 0` always (for connected graphs)
- `λ₂` = **algebraic connectivity** (measures graph robustness)
- Higher eigenvalues relate to clustering and community structure

**Detection Method**:

1. Train on clean baseline: compute mean and std of eigenvalues
2. For test graph: compute current eigenvalues
3. Flag anomalies when eigenvalue distribution deviates significantly
4. Use Z-score threshold (typically 2-3 standard deviations)

**Why It Works**:

- Phantom UAVs alter graph topology
- New nodes change eigenvalue distribution
- Sudden changes indicate anomalies

**Limitations**:

- Requires statistical baseline
- May miss subtle attacks
- Sensitive to natural network variations

**Reference**:
Peel, L., et al. (2015). "Detecting Change Points in the Large-scale Structure of Evolving Networks"

---

### Centrality-Based Detection

**Metrics Used**:

1. **Degree Centrality**: `C_D(v) = deg(v) / (n-1)`

   - Number of connections normalized by max possible
   - High degree = hub node (may be suspicious)

2. **Betweenness Centrality**: `C_B(v) = Σ(σ_st(v) / σ_st)`

   - Fraction of shortest paths passing through node
   - High betweenness = bridge node

3. **Closeness Centrality**: `C_C(v) = 1 / Σd(v, u)`
   - Inverse of average distance to all other nodes
   - High closeness = central position

**Detection Method**:

1. Train on baseline: compute mean and std for each centrality metric
2. For each node in test graph:
   - Compute all three centrality values
   - Calculate Z-scores vs baseline
   - Combine into weighted anomaly score: `0.4×degree_z + 0.4×betweenness_z + 0.2×closeness_z`
3. Flag nodes with combined score > threshold

**Why It Works**:

- Phantom UAVs often have unusual connectivity patterns
- Randomly placed phantoms may be isolated or over-connected
- Position spoofing creates inconsistent centrality

**Limitations**:

- Normal network dynamics create false positives
- Coordinated attacks can mimic legitimate patterns
- Requires connected graph for closeness

**Reference**:
Freeman, L. C. (1978). "Centrality in social networks: Conceptual clarification"

---

## Cryptographic Defense

### Ed25519 Digital Signatures

**Algorithm**: EdDSA (Edwards-curve Digital Signature Algorithm) on Curve25519

**Why Ed25519**:

- **Fast**: ~50μs signing, ~100μs verification
- **Secure**: 256-bit security (equivalent to RSA-3072)
- **Deterministic**: No random nonce needed (immune to nonce reuse attacks)
- **Small**: 32-byte keys, 64-byte signatures
- **Side-channel resistant**: Constant-time operations

**Signing Process**:

1. Generate key pair: `(sk, pk)` where `sk` is 32-byte private key, `pk` is public key
2. To sign message `m`:
   - Compute `r = H(hash_prefix || m)` where `hash_prefix` is derived from `sk`
   - Compute `R = r × G` (point on curve)
   - Compute `h = H(R || pk || m)`
   - Compute `s = (r + h × sk) mod L`
   - Signature is `(R, s)` encoded as 64 bytes

**Verification Process**:

1. Parse signature into `(R, s)`
2. Compute `h = H(R || pk || m)`
3. Check if `s × G = R + h × pk`
4. Accept if equation holds, reject otherwise

**In Argus**:

- Each legitimate UAV has an Ed25519 key pair
- UAVs sign every Remote ID message with their private key
- Receivers verify signatures using known public keys
- Phantom UAVs cannot produce valid signatures

**Security Properties**:

- **Unforgeability**: Computationally infeasible to forge signatures without private key
- **Perfect detection**: 100% TPR (all spoofed messages rejected), 0% FPR (all legitimate accepted)
- **Non-repudiation**: Signatures prove message origin

**Trade-offs**:

- ✅ Advantages: Perfect accuracy, provable security
- ⚠️ Disadvantages:
  - Requires key distribution infrastructure
  - 101% message overhead (signature doubles message size)
  - ~60× slower than graph methods (still < 100ms)

**Reference**:
Bernstein, D. J., et al. (2012). "High-speed high-security signatures"

---

## Machine Learning Detection (Future Work)

### Node2Vec Graph Embeddings

**Algorithm**: Random walk-based graph embedding

**Intuition**:

- Represent each node as a vector in continuous space
- Similar nodes (by network position) have similar vectors
- Anomalous nodes cluster separately in embedding space

**Process**:

1. Generate random walks starting from each node
2. Treat walks as "sentences" and nodes as "words"
3. Train Word2Vec to learn embeddings
4. Use embeddings as features for anomaly detection

**Parameters**:

- `dimensions`: Embedding size (typically 64-128)
- `walk_length`: Length of each random walk (20-80)
- `num_walks`: Walks per node (10-200)
- `p`, `q`: Return/explore parameters (control walk strategy)

**Reference**:
Grover, A., & Leskovec, J. (2016). "node2vec: Scalable Feature Learning for Networks"

### Isolation Forest

**Algorithm**: Ensemble method for anomaly detection

**Intuition**:

- Anomalies are "few and different"
- Anomalous points are easier to isolate in decision trees
- Average isolation depth indicates anomaly score

**Process**:

1. Build ensemble of random trees
2. For each tree, recursively partition data
3. Anomalies require fewer splits to isolate
4. Compute anomaly score from average path length
5. Threshold to classify anomalous vs normal

**Parameters**:

- `n_estimators`: Number of trees (100-200)
- `contamination`: Expected fraction of anomalies (0.05-0.2)
- `max_samples`: Samples per tree ('auto' = 256)

**Reference**:
Liu, F. T., et al. (2008). "Isolation Forest"

---

## Attack Models

### Phantom UAV Injection

**Implementation**:

```python
for i in range(phantom_count):
    phantom_id = f"PHANTOM-{i}"
    position = random_position_in_bounds()
    velocity = random_velocity()

    phantom = UAV(
        uav_id=phantom_id,
        position=position,
        velocity=velocity,
        is_legitimate=False,  # Ground truth label
        private_key=None      # No crypto key!
    )

    swarm.add_uav(phantom)
```

**Detection Challenges**:

- Phantoms may land in realistic positions
- Movement patterns can mimic legitimate UAVs
- Graph topology changes are subtle with few phantoms

---

### Position Falsification

**Implementation**:

```python
for target_uav in selected_targets:
    offset = random_offset(magnitude)

    # UAV keeps true position for movement
    true_pos = target_uav.position

    # But reports false position in Remote ID
    reported_pos = true_pos + offset

    # Receiver sees falsified coordinates
    message.latitude = reported_pos[1]
    message.longitude = reported_pos[0]
```

**Detection Challenges**:

- Graph topology remains unchanged (true position used)
- Only detectable via:
  - Velocity inconsistencies (position jumps)
  - Comparison with other sensors (radar, visual)
  - Cryptographic verification (if enabled)

---

### Coordinated Attack

**Implementation**:

```python
formation_center = random_position()
formation_velocity = shared_velocity_vector()

for i in range(phantom_count):
    # Position relative to formation center
    angle = 2π × i / phantom_count
    offset = (radius × cos(angle), radius × sin(angle), 0)

    phantom_pos = formation_center + offset

    phantom = UAV(
        position=phantom_pos,
        velocity=formation_velocity,  # All move together!
        is_legitimate=False
    )
```

**Why It's Harder to Detect**:

- Phantoms form coherent sub-swarm
- Movement is coordinated (realistic)
- May have normal centrality patterns
- Requires detecting "too perfect" coordination

---

## Consensus Algorithm

### Average Consensus

**Goal**: All UAVs converge to the average of their initial values

**Update Rule**:

```
x_i(t+1) = x_i(t) + ε × Σ_{j∈N_i} (x_j(t) - x_i(t))
```

Where:

- `x_i(t)` = state of UAV i at time t
- `N_i` = neighbors of UAV i (within comm range)
- `ε` = step size (typically `1 / max_degree`)

**Convergence**:

- If graph is connected: converges to `x̄ = (1/n)Σx_i(0)`
- Convergence rate depends on algebraic connectivity (λ₂)

**Attack Impact**:

- Phantom UAVs inject false values
- Pulls consensus away from true average
- More phantoms = larger consensus error

**Defense Effectiveness**:

- Crypto: Reject phantom values → normal convergence
- Graph detection: Remove flagged nodes → reduced error

**Reference**:
Olfati-Saber, R., & Murray, R. M. (2004). "Consensus Problems in Networks of Agents with Switching Topology and Delays"

---

## Performance Considerations

### Computational Complexity

| Operation                | Complexity            | Typical Time (n=50) |
| ------------------------ | --------------------- | ------------------- |
| Graph update             | O(n²)                 | ~0.5ms              |
| Laplacian eigenvalues    | O(n³)                 | ~0.6ms              |
| Centrality (betweenness) | O(n³)                 | ~1.0ms              |
| Ed25519 sign             | O(1)                  | ~0.05ms             |
| Ed25519 verify           | O(1)                  | ~0.1ms              |
| Node2Vec                 | O(n × walks × length) | ~50-100ms           |

### Scalability

**Graph Methods** (O(n²) - O(n³)):

- Works well up to n=100-200 UAVs
- Beyond that, consider:
  - Sampling/approximation algorithms
  - Sparse graph optimizations
  - Incremental eigenvalue updates

**Cryptography** (O(n)):

- Scales linearly with swarm size
- Parallelizable verification
- Bottleneck: key distribution, not computation

**Memory**:

- Full graph: O(n²) for adjacency
- Sparse representation: O(edges) ≈ O(n×avg_degree)
- For n=100, avg_degree=10: ~1KB per graph snapshot

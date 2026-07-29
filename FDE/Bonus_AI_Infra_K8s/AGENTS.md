# Non-negotiables

These hold no matter what a coding agent or a tutorial suggests.

1. **Real managed Kubernetes.** The deploy runs on GKE (or EKS) with working `kubectl`
   access. RunPod, Modal, and other platforms that hide the Kubernetes API do not
   satisfy this assignment. A local kind cluster is acceptable only as the documented
   quota fallback, and the GPU run happens once quota lands.
2. **Readiness means model in memory.** The readiness probe gates on the engine's
   `/health` endpoint. A TCP or "port open" probe is Part 3A's bug, never the final
   state.
3. **Zero-drop rollouts.** The Deployment ships with `maxUnavailable: 0` and
   `maxSurge: 1`, and the rollout experiment proves a live stream survives a restart.
4. **One pod, one GPU.** Pods request `nvidia.com/gpu: 1` and tolerate the GPU taint.
   No CPU-only "it would work with a GPU" submissions for the graded core.
5. **Costs are recorded.** The writeup includes actual spend from the billing console,
   and the submission includes the post-teardown billing screenshot. An idle cluster
   left running fails the teardown criterion regardless of everything else.
6. **Manifests are committed.** Everything applied to the cluster lives in
   `manifests/` in your fork. No undocumented `kubectl edit` state.
7. **Evidence over vibes.** Timings come from watching real events (`kubectl get pods
   -w`, timestamps), not estimates. The eval script must run against the live cluster
   before teardown.

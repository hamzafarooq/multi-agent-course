# Session notes: AI training, tuning, inference and RL on Kubernetes

Guest session for the FDE track, July 23, 2026.
Speaker: **Sanjeev Ganjihal**, AI Infrastructure Engineer, Google.
[LinkedIn](https://www.linkedin.com/in/sanjeevg89/) · [Substack](https://sanjeevganjihal.substack.com/)

## The one idea

The cluster does not care what a "model" is. It cares what **shape** the work is, and
shape picks the pattern. Every AI workload you will ever meet is one of four shapes,
and all four run on the same substrate: Kubernetes.

| Shape | What it is | The Kubernetes pattern |
|---|---|---|
| **Training** | one giant machine: thousands of GPUs in lockstep, all or nothing | gang scheduling: JobSet + Kueue + constant checkpoints |
| **Fine-tuning** | a queue of small short jobs; interruption is fine | Jobs on Spot GPUs + quota queue + checkpoint/resume |
| **Inference** | an always-on fleet behind a URL that breathes with traffic | Deployment / LeaderWorkerSet + LLM-aware routing and autoscaling |
| **RL** | a factory loop: an inference fleet feeding a training gang | Ray on Kubernetes gluing both worlds + weight shipping |

## The 5-layer AI infra stack

Every fix has a floor. Diagnose on the right one.

| Layer | Name | Lives here |
|---|---|---|
| L5 | Workloads and frameworks | vLLM, SGLang, PyTorch FSDP, JAX, TRL/veRL, LoRA stacks |
| L4 | **Cloud-native orchestration (the session)** | Kubernetes, Kueue, JobSet, LeaderWorkerSet, KubeRay, Inference Gateway, Karpenter |
| L3 | Managed cluster and cloud | GKE / EKS / AKS, node pools, VPC and IAM, GPU quotas, Spot |
| L2 | Storage and network fabric | S3/GCS, NVMe caches, NVLink, InfiniBand/RoCE, GPUDirect |
| L1 | Accelerators and silicon | NVIDIA H200/Blackwell, Google TPU (Trillium, Ironwood), CPUs for graders |

Routing table: slow tokens go to L5 (engine settings) · pods stuck Pending go to L4
(queues and quotas) · minutes-long cold starts go to L2/L3 (weight staging) ·
throughput cliffs on big jobs go to L2 fabric or L1 topology.

## The parallelism toolbox

Four ways to split a model. Each one is a bet about your network.

| Technique | Splits | Stresses | Used by |
|---|---|---|---|
| Data parallel (DP/FSDP) | the batch; same model everywhere, average the results | all-reduce bandwidth (InfiniBand/RoCE) | every trainer, RL updates |
| Tensor parallel (TP) | every layer's matrices; 4-8 GPUs act as one | NVLink inside one node, never across boxes | big-model serving |
| Pipeline parallel (PP) | the model by depth; layers in a relay | tolerates slower links | giant training runs |
| Expert parallel (EP) | MoE experts; a router picks a few per token | all-to-all traffic | trillion-scale MoEs (Kimi K3, DeepSeek V4) |

Frontier training stacks all four. Fine-tuning needs none of them; that is LoRA's whole
trick. Placement that respects the fabric runs up to 2x faster on identical hardware,
which is why topology-aware scheduling exists.

## The field guide

- **Train, a gang:** JobSet describes the many-pods-one-job gang · Kueue admits it all
  or nothing against team quotas · checkpoints to object storage make failure cost
  minutes · topology decides placement.
- **Fine-tune, a queue:** LoRA/QLoRA shrinks it to one card · a K8s Job runs it to
  completion · Spot GPUs at 60-90% off because checkpoint/resume tolerates eviction ·
  Kueue meters the experiment queue.
- **Serve, a fleet:** vLLM pods in a Deployment, or LeaderWorkerSet when the model spans
  nodes · readiness = model in memory · route on queue depth and prefix reuse ·
  autoscale on tokens, never CPU% · drain streams before killing pods.
- **RL, the loop:** a generation fleet (vLLM) + graders + a training gang, glued by Ray
  on Kubernetes · weights stream back every round · generation is the bottleneck, so
  inference skills carry the day.

## Receipts worth knowing (verified July 2026)

- CNCF 2025 survey: 82% of container users run Kubernetes in production; 66% of
  organizations run some or all AI inference on it.
- CoreWeave runs a Kubernetes-native GPU cloud (SUNK, Slurm on Kubernetes) with single
  jobs past 32,000 GPUs; OpenAI trains there under $22B+ in committed deals.
- Google's GKE supports 65,000-node clusters; Anthropic's published GKE work cut
  failure recovery from hours to 2-5 minutes.
- The open frontier went trillion-scale in one month: Kimi K3 (2.8T, open weights),
  DeepSeek V4 (1.6T, MIT), Qwen3.8-Max (2.4T, preview). Moonshot serves K3 with
  Mooncake, split prefill/decode pools, reporting a 90% cache-hit rate.
- Failure at scale is arithmetic, not anecdote: fleet failure interval equals per-part
  MTBF divided by part count. 100,000 accelerators at a five-year MTBF means a fault
  roughly every half hour, which is why checkpoints, health checks and topology-aware
  placement are the three reflexes of every frontier cluster.

## Sources

- [CNCF 2025 annual survey](https://www.cncf.io/announcements/2026/01/20/kubernetes-established-as-the-de-facto-operating-system-for-ai-as-production-use-hits-82-in-2025-cncf-annual-cloud-native-survey/)
- [CoreWeave SUNK](https://www.coreweave.com/blog/why-sunk-redefines-the-ai-research-cluster-for-production-grade-training) · [CoreWeave and OpenAI](https://www.coreweave.com/news/coreweave-expands-agreement-with-openai-by-up-to-6-5b)
- [GKE 65,000-node clusters](https://cloud.google.com/blog/products/containers-kubernetes/gke-65k-nodes-and-counting) · [Anthropic on GKE](https://www.zenml.io/llmops-database/scaling-ai-training-and-inference-infrastructure-with-gke-dynamic-slicing-on-tpus)
- [Kimi K3](https://www.kimi.com/blog/kimi-k3) · [DeepSeek V4](https://api-docs.deepseek.com/news/news260424/) · [Qwen3.8-Max](https://www.marktechpost.com/2026/07/19/alibaba-previews-qwen3-8-max-a-2-4-trillion-parameter-multimodal-model-days-after-moonshots-kimi-k3-open-weight-launch/)

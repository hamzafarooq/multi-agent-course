# Bonus: AI Infra on Kubernetes (RAG at scale for Moment Search)

> 🎁 **This is an optional bonus, not a graded assignment.** There's no submission
> and no rubric you have to clear — do it on your own time, when you're curious how
> the model behind the API actually runs. It pairs with the guest-speaker session on
> AI infra. Everything below still works as a self-guided lab; just treat the
> "graded" language as "this is the part worth doing carefully."

> So far you have used LLMs the way most of the world does: through a hosted
> OpenAI-style API. This assignment is where you cross to the other side of that URL.
> You will serve an open-source model yourself with vLLM for the first time, wire a
> working AI application to it, and then run it as a real fleet on Kubernetes, with the
> break-and-fix experiments that separate a demo from a deploy.

The application is **[Moment Search](https://github.com/traversaal-ai/momentsearch)**:
visual video search and RAG (CLIP retrieval + Qdrant + bring-your-own vision LLM). You
will not modify its code. You will change three lines of its `.env`, which is the whole
point: vLLM speaks the OpenAI API, so owning your model is a config change, not a
rewrite.

Companion session: **AI training, tuning, inference and RL on Kubernetes** (July 23,
2026). Recap in [`SESSION_NOTES.md`](SESSION_NOTES.md). The instructor demo runbook for
this exact stack is in [`demo/`](demo/).

One catch that matters: Moment Search shows the LLM actual video frames, so your model
must be **vision-capable**. Text-only models will not work. We use
`Qwen/Qwen2.5-VL-7B-Instruct` (Apache 2.0, fits one L4). Budget about 3 hours and under
$10; the $300 GCP free credit covers it many times over. **Always tear down when
you're done** — GPUs bill while idle, bonus or not.

## The two rungs

- **Rung A (warm-up): one box on RunPod.** Your first time serving a model yourself:
  one rented GPU, one command, and a vision model that a real application depends on.
  RunPod is perfect here and requires no quota wait.
- **Rung B (the main event): the fleet on GKE.** The learning objective of this rung is
  Kubernetes itself: kubectl, node pools, probes, rollouts, autoscaling and cost
  hygiene, on the platform enterprise customers actually run. RunPod and Modal are
  great products that hide the Kubernetes API; that is exactly why they cannot carry
  this rung.

Already have AWS credits? EKS with a g5/g6 node group works; manifests are identical.

## Part 0: Accounts and quota (start early, this has a wait)

1. Install `gcloud`, create a project, enable the Kubernetes Engine API.
2. Upgrade from free trial to paid billing. The $300 credit survives; GPU quota does
   not exist on trial accounts.
3. Request quota: IAM & Admin, Quotas, "NVIDIA L4 GPUs", region `us-central1`, request
   2. Approval usually takes minutes to hours.
4. This step is part of the assignment. Quota tickets are real FDE work; record how
   long yours took.

## Part 1: Meet the app (15 minutes, no GPU needed)

```bash
git clone https://github.com/traversaal-ai/momentsearch.git
cd momentsearch
cp .env.example .env
docker compose up --build
python examples/quickstart.py     # seeds the sample corpus
```

Open http://localhost:8000. Retrieval works with no LLM key at all (CLIP runs
locally). Ask a question and note what is missing: the cited answer. That missing
piece is what you are about to own.

## Part 2, Rung A: one box on RunPod (warm-up)

Rent a single 24 GB+ GPU on RunPod and serve the vision model with vLLM. One command
turns a rented GPU into the same OpenAI-compatible endpoint you have been calling all
course, except now you own it:

```bash
vllm serve Qwen/Qwen2.5-VL-7B-Instruct --max-model-len 8192 --limit-mm-per-prompt image=8
```

Point Moment Search at it in `.env` and restart the app:

```
LLM_PROVIDER=openai
LLM_BASE_URL=http://<runpod-ip>:8000/v1
LLM_MODEL=Qwen/Qwen2.5-VL-7B-Instruct
LLM_API_KEY=not-needed
```

Ask the same question again. Same app, your model, cited answers. Screenshot it, then
shut the pod down. That is the whole rung; everything after this is about what happens
when one box is not enough.

## Part 3, Rung B: create the cluster (about 10 minutes)

```bash
gcloud container clusters create fde-lab \
  --zone us-central1-a --num-nodes 1 --machine-type e2-standard-4

gcloud container node-pools create gpu-pool \
  --cluster fde-lab --zone us-central1-a \
  --machine-type g2-standard-8 \
  --accelerator type=nvidia-l4,count=1,gpu-driver-version=latest \
  --num-nodes 2 --enable-autoscaling --min-nodes 1 --max-nodes 3 --spot
```

The autoscaling flags matter: experiment B below only works if the cluster is allowed
to buy a third node. Check the five words from the session: `kubectl get nodes` shows
your node pools; `kubectl describe node <gpu-node>` shows `nvidia.com/gpu: 1` and the
taint that keeps ordinary pods off expensive hardware.

## Part 4: Deploy the fleet and rewire the app

Read [`manifests/vllm.yaml`](manifests/vllm.yaml) top to bottom, then:

```bash
kubectl apply -f manifests/vllm.yaml
kubectl get pods -w
```

Every field exists for a reason covered in the session: one pod per GPU, a readiness
probe that gates on `/health` (model in memory, not port open), a rollout strategy
that never dips below full capacity, and a toleration for the GPU taint. Record the
gap between `Running` and `Ready`; that gap is the weights loading into VRAM.

Get the front door and point the app at the fleet:

```bash
kubectl get svc vllm    # note EXTERNAL-IP
```

```
LLM_BASE_URL=http://<EXTERNAL-IP>/v1
```

Restart Moment Search and ask again. The answer now comes from a two-replica fleet
behind a LoadBalancer. Nothing in the app changed.

## Part 5: Break it three ways (the interesting part)

Run every experiment with the app open. Infrastructure failures are only real when you
watch them through a product.

**A. The lying probe.** Change the readiness probe to a plain TCP check on port 8000
and redeploy. Ask questions in the app during startup and capture the failures that
leak through. Revert. One paragraph: why did "port open" lie?

**B. Capacity is bought, not borrowed.** `kubectl scale deployment vllm --replicas=3`.
The pod goes `Pending`; the cluster buys a Spot node, installs drivers, pulls the
image, loads weights. Time the whole chain from scale command to `Ready`. That number
is why fleets keep a warm floor.

**C. The rollout that drops nobody.** With `maxUnavailable: 0, maxSurge: 1` already in
the scaffolding, ask the app a question and run `kubectl rollout restart deployment
vllm` while the answer streams. Confirm it finishes. Then delete one pod outright and
ask again: the readiness gate keeps traffic on the healthy replica while the dead one
resurrects. Explain both behaviors.

## Stretch goals (pick one)

- **Tensor parallel:** recreate the GPU pool with `g2-standard-24` and `count=2`,
  serve the model with `--tensor-parallel-size 2`.
- **The queue shape:** install Kueue, set a quota of 1 GPU, submit three fine-tune
  style Jobs, watch them admit one at a time.
- **Smart traffic:** install the Gateway API Inference Extension and route by model
  name.

## What to capture (for yourself — nothing to submit)

Since this is a bonus, these are for your own notes and to share in the session if
you like — not a graded deliverable.

1. Run `python eval/eval.py` against the live cluster before teardown; it writes
   `eval/REPORT.md`.
2. A one-page writeup: your three timings (Ready gap, scale-up chain, rollout), Rung A
   vs Rung B observations, actual spend from the billing page, and the one thing that
   surprised you.
3. A 60 to 90 second recording: Moment Search answering through your fleet, then
   `kubectl get pods -w` during the scale-up.
4. A screenshot of the empty billing page after teardown.

Self-check rubric: [`eval/rubric.json`](eval/rubric.json). Non-negotiables (still
worth honoring even unsupervised): [`AGENTS.md`](AGENTS.md).

## Teardown (not optional, bonus or not)

```bash
gcloud container clusters delete fde-lab --zone us-central1-a
```

GPUs bill while idle. Delete the cluster the same day. Leaving a GPU node running
overnight is also an FDE lesson, just an expensive one.

## If quota is stuck

Do Rung A on RunPod (no quota needed), and every Kubernetes step on a local kind
cluster with a CPU model (ollama with `qwen2.5-vl` or vLLM CPU mode). Probes, scaling
and rollouts behave identically. Swap in the GPU pool when quota lands, then rerun the
eval.

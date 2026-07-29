# Live demo runbook: Moment Search on a GKE vLLM fleet

A five minute end-to-end demo for the July 23 session. Moment Search answers questions
about video, on screen, backed by a self-served open-source vision model running as a
two-replica vLLM fleet on GKE. Mid-demo we kill a pod while the app keeps answering,
then scale the fleet and watch the cluster buy a GPU node live.

Everything here is reproducible from scratch by one engineer in about 45 minutes and
roughly $3 of spend. It is the same stack students build in Assignment 3, so rehearsing
the demo also validates the assignment.

## What the audience sees

1. A real product (Moment Search sample corpus) answering with cited video moments.
2. `.env` on screen: three lines are the entire difference between OpenAI and a fleet
   you own. vLLM speaks the same API.
3. A pod deleted mid-question; the answer still streams. The fleet shape: any N.
4. `kubectl scale --replicas=3`; a Pending pod triggers a live Spot node purchase.
   While it provisions, the speaker explains the warm floor.

## Prerequisites

- gcloud authenticated to a project with billing enabled and quota for 3 L4 GPUs in
  `us-central1` (request 3, not 2: the scale-out moment needs headroom).
- kubectl, Docker, Python 3.11, FFmpeg.
- No API keys needed. Retrieval is local CLIP; generation is the fleet.

## Provision (T minus 60 minutes)

```bash
./provision.sh    # creates cluster + GPU pool, applies manifests, waits for Ready
```

The script prints the LoadBalancer IP when the fleet is up. First readiness takes 5 to
10 minutes (node boot, image pull, 7B VLM weights into VRAM). While it loads:

```bash
git clone https://github.com/traversaal-ai/momentsearch.git && cd momentsearch
cp .env.example .env
# set these three lines, using the IP the script printed:
#   LLM_PROVIDER=openai
#   LLM_BASE_URL=http://<EXTERNAL-IP>/v1
#   LLM_MODEL=Qwen/Qwen2.5-VL-7B-Instruct
#   LLM_API_KEY=not-needed
docker compose up --build -d
python examples/quickstart.py          # seeds the sample corpus (four LLM talks)
```

Verify: open http://localhost:8000, ask "when does the speaker draw the attention
diagram?" and confirm a cited answer returns in a few seconds.

Stage three windows before class: browser on the app, a terminal running
`kubectl get pods -w`, and a spare terminal for commands.

## The five minutes, scripted

| Clock | Do | Say |
|---|---|---|
| 0:00 | Ask the app a question; let the cited answer stream | "This answer was just written by a 7B open-source vision model reading video frames. Not an API. It runs on a cluster I own." |
| 1:00 | Show the three `.env` lines | "Swapping OpenAI for my own fleet was these three lines. vLLM speaks the same protocol. That is the whole trick of owning your inference." |
| 1:45 | Show `kubectl get pods`: two Ready replicas | "Two identical pods, one GPU each, behind one front door. The fleet shape from the session." |
| 2:15 | `kubectl delete pod <one of them>`, immediately re-ask in the app | "I just killed half the fleet mid-question. The answer keeps streaming: the readiness gate holds traffic on the healthy replica while Kubernetes resurrects the dead one." |
| 3:30 | `kubectl scale deployment vllm --replicas=3`; watch Pending in the pods window | "Three replicas wanted, two GPUs owned. Watch the cluster literally buy a machine. This takes minutes, which is exactly why real fleets keep a warm floor instead of chasing spikes." |
| 4:30 | Leave the node provisioning on screen | "Everything you just watched is Assignment 3. You will build this exact stack and break it three ways on purpose." |

The node typically reaches Ready after the talking is done; that is fine, the Pending
state and the node appearing are the demo, not the completion.

## Reset (between rehearsal and class)

```bash
kubectl scale deployment vllm --replicas=2
```

The autoscaler removes the extra Spot node after its scale-down delay; no other reset
is needed. Re-ask one question to confirm health.

## Teardown (same day, always)

```bash
./teardown.sh
```

Then check the billing page. GPUs bill while idle.

## Troubleshooting

- **Pods Pending forever:** GPU quota. `gcloud compute regions describe us-central1`
  shows usage; the quota request page is the fix.
- **EXTERNAL-IP stuck on `<pending>`:** wait 2 to 3 minutes; LoadBalancers are slow to
  program. Firewall is handled by GKE automatically.
- **CUDA out of memory:** drop to `Qwen/Qwen2.5-VL-3B-Instruct` in the manifest, or
  lower `--max-model-len` to 4096.
- **Slow first token on frame-heavy questions:** expected; six images per prompt is
  real multimodal prefill. It is a talking point, not a bug.
- **Spot preemption during the demo:** rare, and if it happens it IS the demo. Say
  "that was a real preemption" and let the readiness gate carry the moment.

#!/usr/bin/env bash
# Provision the demo stack: GKE cluster + Spot L4 pool + the vLLM fleet.
# Idempotent enough to re-run; ~10 min to cluster, ~5-10 more to model Ready.
set -euo pipefail

ZONE="${ZONE:-us-central1-a}"
CLUSTER="${CLUSTER:-fde-lab}"
DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo ">> project: $(gcloud config get-value project 2>/dev/null)"

if ! gcloud container clusters describe "$CLUSTER" --zone "$ZONE" >/dev/null 2>&1; then
  echo ">> creating cluster $CLUSTER"
  gcloud container clusters create "$CLUSTER" \
    --zone "$ZONE" --num-nodes 1 --machine-type e2-standard-4
  gcloud container node-pools create gpu-pool \
    --cluster "$CLUSTER" --zone "$ZONE" \
    --machine-type g2-standard-8 \
    --accelerator type=nvidia-l4,count=1,gpu-driver-version=latest \
    --num-nodes 2 --enable-autoscaling --min-nodes 1 --max-nodes 3 --spot
else
  echo ">> cluster $CLUSTER already exists, reusing"
fi

gcloud container clusters get-credentials "$CLUSTER" --zone "$ZONE"

echo ">> applying the fleet"
kubectl apply -f "$DIR/manifests/vllm.yaml"

echo ">> waiting for rollout (weights into VRAM takes 5-10 min on first boot)"
kubectl rollout status deployment/vllm --timeout=20m

echo ">> waiting for the front door"
for i in $(seq 1 60); do
  IP="$(kubectl get svc vllm -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)"
  [ -n "$IP" ] && break
  sleep 5
done
[ -n "${IP:-}" ] || { echo "!! LoadBalancer IP never arrived"; exit 1; }

echo ""
echo ">> fleet is up. Point Moment Search .env at it:"
echo "   LLM_PROVIDER=openai"
echo "   LLM_BASE_URL=http://$IP/v1"
echo "   LLM_MODEL=Qwen/Qwen2.5-VL-7B-Instruct"
echo "   LLM_API_KEY=not-needed"

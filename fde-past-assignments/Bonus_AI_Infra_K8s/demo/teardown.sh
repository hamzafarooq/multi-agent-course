#!/usr/bin/env bash
# Delete the demo cluster. GPUs bill while idle; run this the same day.
set -euo pipefail
ZONE="${ZONE:-us-central1-a}"
CLUSTER="${CLUSTER:-fde-lab}"
gcloud container clusters delete "$CLUSTER" --zone "$ZONE" --quiet
echo ">> deleted. Now check the billing page and screenshot it."

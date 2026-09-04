# Bonus — LLM Inference Optimization

Optional material for Module 5. A voice agent lives or dies on **latency and cost**, and these
two deep-dives are where those numbers actually come from — the inference-level techniques that
make any model (voice or not) cheaper and faster to run. Nothing here is required to complete
the module.

| Folder | What it covers |
|:--|:--|
| [`Quantization_and_KV_Caching`](Quantization_and_KV_Caching/) | 4-bit quantization with bitsandbytes + Transformers; TTFT / inter-token latency / throughput; full-precision vs. quantized comparison (Llama-3.1-8B: ~30 GB → ~6 GB VRAM, higher throughput). |
| [`Speculative_Decoding_from_scratch`](Speculative_Decoding_from_scratch/) | A small "draft" model proposes tokens; a large model verifies them in one parallel pass and accepts the correct prefix. Built from scratch to expose the accept/reject mechanics. |

Each folder has its own `README.md` and notebooks. A GPU is recommended — the notebooks
benchmark on an NVIDIA A40 (48 GB) via [RunPod](https://www.runpod.io/).

# Quantization

A collection of Jupyter notebooks demonstrating **4-bit model quantization** using [bitsandbytes](https://github.com/TimDettmers/bitsandbytes) and [Hugging Face Transformers](https://github.com/huggingface/transformers). These notebooks show how to reduce the memory footprint of large language models while maintaining output quality, and how to measure inference performance.

## Notebooks

### 1. `bnb_4bit_Maven.ipynb` — 4-Bit Quantization Fundamentals

A step-by-step guide to 4-bit quantization with bitsandbytes:

- **Basic usage**: Load a model (`facebook/opt-350m`) in 4-bit with a single argument (`load_in_4bit=True`)
- **Compute dtype**: Change the computation precision (e.g., `bfloat16`) for speed improvements
- **Quantization types**: Compare FP4 vs NF4 (Normal Float 4) quantization
- **Combined configuration**: Use `BitsAndBytesConfig` to set quantization type, compute dtype, and nested quantization together
- **Scaling up**: Load a 20B-parameter model (`EleutherAI/gpt-neox-20b`) entirely on a single GPU using 4-bit quantization
- **Hub integration**: Push quantized models to Hugging Face Hub

### 2. `Maven_TextStreamer_Quantization.ipynb` — Text Streaming & Inference Metrics

Demonstrates real-time text streaming and inference performance benchmarking:

- **TextStreamer**: Stream generated tokens to the console in real-time
- **TextIteratorStreamer**: Iterate over generated tokens programmatically with per-token timestamps
- **Performance metrics**: Measure Time To First Token (TTFT), Inter-Token Latency (ITL), end-to-end latency, and throughput
- **Full-precision vs quantized comparison**: Run the same benchmarks on the full-precision and 4-bit quantized `Meta-Llama-3.1-8B-Instruct` model
- **GPU memory tracking**: Monitor VRAM usage before and after model loading

## Key Results

| Metric | Full Precision | 4-Bit Quantized |
|--------|---------------|-----------------|
| GPU Memory | ~29.9 GB | ~5.8 GB |
| Throughput | ~17.6 tokens/s | ~32.5 tokens/s |
| TTFT | 0.084s | 0.073s |
| ITL | 0.057s | 0.030s |
| End-to-End Latency | 5.75s | 3.11s |

*Results from `Maven_TextStreamer_Quantization.ipynb` using `Meta-Llama-3.1-8B-Instruct` on an NVIDIA A40 (48 GB VRAM) via [RunPod](https://www.runpod.io/).*

## Usage

1. Install the dependencies from requirements.txt
2. Authenticate with Hugging Face Hub (required for gated models like Llama):
   ```python
   from huggingface_hub import notebook_login
   notebook_login()
   ```
3. Open either notebook and run the cells sequentially

## References

- [bitsandbytes](https://github.com/TimDettmers/bitsandbytes) — 4-bit and 8-bit quantization library
- [QLoRA paper](https://arxiv.org/abs/2305.14314) — Introduces NF4 quantization type
- [Hugging Face 8-bit integration blogpost](https://huggingface.co/blog/hf-bitsandbytes-integration)
- [Hugging Face Transformers documentation](https://huggingface.co/docs/transformers)

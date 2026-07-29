# Speculative Decoding from Scratch

This module demonstrates **Speculative Decoding**, an inference optimization technique for large language models (LLMs) that can significantly speed up text generation.

## What is Speculative Decoding?

Speculative decoding is a technique to accelerate LLM inference by using a smaller, faster "draft" model to propose tokens, which are then verified by a larger, more accurate "main" model. When the draft is accurate, the main model can accept multiple tokens at once rather than generating them one-by-one, leading to substantial speed improvements.

### Key Concept

Instead of the slow process of:
1. Large model generates token 1
2. Large model generates token 2
3. Large model generates token 3
4. ...

Speculative decoding does:
1. Small (fast) model generates tokens 1-k
2. Large model verifies all k tokens in parallel
3. Accept correct tokens, reject and regenerate from first mismatch
4. Repeat

## Implementation

This implementation includes:

- **Normal Inference**: Standard token-by-token generation using the large model (baseline)
- **Speculative Decoding Demo**: Draft generation with a small model, followed by verification with the large model

### Models Used

- **Draft Model**: `google/gemma-2-2b-it` (2B parameters) - Fast but less accurate
- **Main Model**: `google/gemma-2-9b-it` (9B parameters) - Slower but more accurate

## Features

The code demonstrates:

1. **Draft Generation**: Using a smaller model (2B) to quickly generate candidate tokens
2. **Verification**: Calculating log-likelihood scores to measure how well the draft aligns with the main model (9B)
3. **Performance Measurement**: Comparing latency and tokens-per-second between normal and speculative approaches
4. **Batch Testing**: Running multiple prompts to calculate average performance metrics

## Usage

```python
# Run the script
python speculative_decoding.py
```

The script will:
1. Load both the small and large Gemma2 models
2. Run inference on 5 different prompts
3. Compare performance between normal and speculative decoding
4. Display latency, tokens/second, and speed improvement metrics

## Key Metrics

### Log Likelihood (Verification Score)

The log-likelihood score measures the quality of the draft:

- **Closer to 0** (less negative): Draft tokens were highly probable according to the main model → better alignment
- **Farther from 0** (more negative): Draft tokens were unlikely according to the main model → poor alignment

Higher scores indicate the draft model is generating text that closely matches what the main model would have generated, leading to better efficiency gains.

### Performance Metrics

The script measures:
- **Latency**: Total time taken for generation
- **Tokens per Second**: Generation speed
- **Speed Improvement**: Percentage improvement of speculative over normal inference

## Important Notes

This is a **simplified demonstration** for educational purposes. It calculates verification scores but doesn't implement the full token-by-token accept/reject mechanism of production speculative decoding systems.

In a full implementation:
- Tokens would be accepted/rejected one-by-one during generation
- The main model would only regenerate from the first rejected token
- This would achieve actual speedups by reducing the number of main model forward passes

## Requirements

```bash
pip install torch transformers
```

GPU with sufficient VRAM recommended for running both models (requires ~20GB for both models in bfloat16).

## References

- Original Paper: [Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192)
- Hugging Face Transformers: [Documentation](https://huggingface.co/docs/transformers)

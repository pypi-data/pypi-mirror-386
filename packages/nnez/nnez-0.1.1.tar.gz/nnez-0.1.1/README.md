# nnez

**Neural Network Easy Extraction** - A lightweight Python package for extracting activation patterns from transformer language models with just a few lines of code. The package caches your embeddings, so after you create your embedding for a piece of text once, the package will just quickly load that embedding in the future rather than recomputing it.

This is designed to be maximally simple and was originally meant to help in cases where you just want to create an embedding based on a text, which is a common usecase in cognitive neuroscience research. This package is built ontop of [NNsight](https://github.com/ndif-team/nnsight).

Below, I describe how to use the package. See also `examples/quickstart.py`

## 📦 Installation

```bash
pip install nnez
```

## 🎮 Quick Start

### Extract Activations from any Transformer LLM

```python
from nnez import get_activity_from_text

# Extract activations from specific layers of GPT-2
text = "The capital of France is Paris."
layers = [5, 10]  # Extract from layers 5 and 10

activations = get_activity_from_text(
    text=text,
    layers_list=layers,
    model_name="gpt2" # You can specify any huggingface model
)

print(activations.shape)  # (2, 768) - 2 layers, 768 dimensions each
```

### Single Layer Extraction

```python
# Extract from a single layer (returns 1D array)
act = get_activity_from_text("Hello world!", 11)  # Layer 11 only
print(act.shape)  # (768,) - Single layer, flattened
```

### Batch Processing

```python
import numpy as np

texts = ["First text", "Second text", "Third text"]
all_activations = []

for text in texts:
    act = get_activity_from_text(text, [0, 6, 11])
    all_activations.append(act)

# Stack into 3D array: (num_texts, num_layers, hidden_size)
batch_activations = np.stack(all_activations)
print(batch_activations.shape)  # (3, 3, 768)
```

## Grammar Utilities

The package includes some grammar utilities leveraging the `inflect` library. These are helpful if you want to do an analysis like that in the associated LLM-RSA paper (Bogdan et al., under review).

```python
from nnez.grammar import get_article, pluralize, quantify

# Smart article detection
get_article("hour")       # "an" (silent h)
get_article("university") # "a"  (y-sound)
get_article("FBI")        # "an" (eff-bee-eye)

# Pluralization
pluralize("child")       # "children"
pluralize("analysis")    # "analyses"
pluralize("octopus")     # "octopuses"

# Quantification
quantify(0, "cat")        # "no cats"
quantify(1, "child")      # "1 child"
quantify(3, "child")      # "3 children"
```

## 📊 Output Shape Reference

| Model | HuggingFace Name | Hidden Size | Output Shape (3 layers) |
|-------|------------------|------------|-------------------------|
| GPT-2 | `gpt2` | 768 | (3, 768) |
| Llama 3.2 3B | `meta-llama/Llama-3.2-3B` | 3072 | (3, 3072) |
| Llama 3.1 8B | `meta-llama/Llama-3.1-8B` | 4096 | (3, 4096) |
| Qwen 2.5 3B | `Qwen/Qwen2.5-3B` | 2048 | (3, 2048) |
| Qwen 2.5 7B | `Qwen/Qwen2.5-7B` | 3584 | (3, 3584) |
| Mistral 7B | `mistralai/Mistral-7B-v0.1` | 4096 | (3, 4096) |
| Gemma 2 2B | `google/gemma-2-2b` | 2304 | (3, 2304) |
| Phi-3 Mini | `microsoft/Phi-3-mini-4k-instruct` | 3072 | (3, 3072) |
| BERT Base | `bert-base-uncased` | 768 | (3, 768) |
| BERT Large | `bert-large-uncased` | 1024 | (3, 1024) |
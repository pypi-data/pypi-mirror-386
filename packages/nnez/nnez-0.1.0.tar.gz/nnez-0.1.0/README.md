# nnez

**Neural Network Easy Extraction** - A lightweight Python package for extracting activation patterns from transformer language models with just a few lines of code.

[![PyPI version](https://badge.fury.io/py/nnez.svg)](https://badge.fury.io/py/nnez)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Features

- 🎯 **Simple API** - Extract LLM activations with just one function call
- 🧠 **Multi-Model Support** - Works with GPT-2, GPT-Neo, LLaMA, BERT, and more
- 📊 **NumPy Output** - Get activations as NumPy arrays for easy analysis
- 🔄 **Flexible Layer Selection** - Extract from any combination of layers
- ⚡ **Automatic Caching** - Reuse loaded models for faster repeated extractions
- 🎨 **Bonus Grammar Tools** - Article detection and pluralization utilities using inflect

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
    model_name="gpt2"
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

## 🔬 Advanced Usage

### Using Different Models

```python
# GPT-2 variants
act = get_activity_from_text(text, [10], model_name="gpt2-medium")

# GPT-Neo
act = get_activity_from_text(text, [0, 12], model_name="EleutherAI/gpt-neo-125M")

# BERT
act = get_activity_from_text(text, [6], model_name="bert-base-uncased")

# Any HuggingFace model
act = get_activity_from_text(text, [10], model_name="your-model-here")
```

### Layer Selection Strategies

```python
# First and last layers - for input/output representations
activations = get_activity_from_text(text, [0, 11])

# Every other layer - for efficient probing
activations = get_activity_from_text(text, list(range(0, 12, 2)))

# Middle layers only - for syntactic features
activations = get_activity_from_text(text, [4, 5, 6, 7])
```

### Similarity Analysis

```python
from scipy.spatial.distance import cosine

text1 = "The cat sat on the mat."
text2 = "The dog sat on the rug."

# Extract from same layers
act1 = get_activity_from_text(text1, [6, 10])
act2 = get_activity_from_text(text2, [6, 10])

# Compare layer-wise similarities
for i, layer in enumerate([6, 10]):
    similarity = 1 - cosine(act1[i], act2[i])
    print(f"Layer {layer} similarity: {similarity:.3f}")
```

## 🎁 Bonus: Grammar Utilities

The package includes grammar tools powered by the `inflect` library:

```python
from nnez.grammar import get_article, pluralize, quantify

# Smart article detection
get_article("hour")       # "an" (silent h)
get_article("university") # "a"  (y-sound)
get_article("FBI")        # "an" (eff-bee-eye)

# Pluralization
pluralize("child")        # "children"
pluralize("analysis")    # "analyses"
pluralize("octopus")     # "octopuses"

# Quantification
quantify(0, "cat")        # "no cats"
quantify(1, "child")      # "1 child"
quantify(3, "child")      # "3 children"
```

## 🛠️ API Reference

### Core Function

```python
get_activity_from_text(
    text: str,
    layers_list: Union[List[int], int],
    model_name: str = "gpt2",
    device: Optional[str] = None,
    verbose: bool = False,
    cache_model: bool = True
) -> np.ndarray
```

**Parameters:**
- `text`: Input text to analyze
- `layers_list`: Layer indices to extract from (list or single int)
- `model_name`: HuggingFace model identifier
- `device`: Device to use ('cuda', 'cpu', or None for auto)
- `verbose`: Print detailed extraction information
- `cache_model`: Cache model for faster repeated use

**Returns:**
- NumPy array of shape `(num_layers, hidden_size)` or `(hidden_size,)` for single layer

## 📊 Output Shape Reference

| Model | Hidden Size | Output Shape (3 layers) |
|-------|------------|-------------------------|
| GPT-2 | 768 | (3, 768) |
| GPT-2 Medium | 1024 | (3, 1024) |
| GPT-2 Large | 1280 | (3, 1280) |
| GPT-2 XL | 1600 | (3, 1600) |
| BERT Base | 768 | (3, 768) |
| BERT Large | 1024 | (3, 1024) |

## 🔧 Requirements

- Python 3.8+
- PyTorch
- Transformers
- NNsight
- NumPy
- inflect (for grammar utilities)

## 📈 Use Cases

- **Interpretability Research** - Analyze internal representations of LLMs
- **Probing Classifiers** - Extract features for downstream tasks
- **Semantic Similarity** - Compare representations across texts
- **Layer Analysis** - Study information flow through model layers
- **Neuron Analysis** - Investigate activation patterns
- **Model Debugging** - Understand model behavior on specific inputs

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📝 Citation

If you use `nnez` in your research, please cite:

```bibtex
@software{nnez2024,
  title = {nnez: Neural Network Easy Extraction},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/nnez}
}
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of [NNsight](https://github.com/ndif-team/nnsight) for model introspection
- Uses [inflect](https://github.com/jaraco/inflect) for grammar utilities
- Compatible with [HuggingFace Transformers](https://github.com/huggingface/transformers)

## 🔗 Links

- [PyPI Package](https://pypi.org/project/nnez/)
- [GitHub Repository](https://github.com/yourusername/nnez)
- [Documentation](https://nnez.readthedocs.io/)
- [Issue Tracker](https://github.com/yourusername/nnez/issues)

---

Made with ❤️ for the ML interpretability community
import numpy as np
import torch
from nnsight import LanguageModel
from transformers import AutoTokenizer
from typing import List, Union, Optional, Tuple
from functools import cache
import warnings
import os
from pathlib import Path
import hashlib


@cache
def get_model_cached(model_name: str) -> Tuple[LanguageModel, AutoTokenizer]:
    model = LanguageModel(model_name, device_map="auto")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model, tokenizer


def get_cache_fp(
    model_name: str,
    text: str,
    layers_list: Union[List[int], int],
    cache_dir: Optional[Union[Path, str]] = ".nnez",
) -> str:
    """
    Generate a file path for caching activation outputs.

    Creates a deterministic file path based on the model name, text content,
    and requested layers. This enables caching of activation extractions to
    avoid redundant computations for the same inputs.

    Args:
        model_name: The HuggingFace model identifier (e.g., "gpt2", "meta-llama/Llama-3.2-3B")
        text: The input text being processed (used to generate a hash for the filename)
        layers_list: Either a single layer index (int) or list of layer indices to extract
        cache_dir: Directory where cached activations are stored. Defaults to ".nnez"
                  subdirectory in the current working directory.

    Returns:
        Path object pointing to the cache file location. The file path structure is:
        {cache_dir}/{model_name}/{text_hash}_{layers}.npy

        Where the layers portion is formatted as:
        - Single layer: "{layer_num}" (e.g., "5")
        - Consecutive layers: "{first}-{last}" (e.g., "0-11")
        - Non-consecutive layers: "{layer1}_{layer2}_{layer3}" (e.g., "0_5_10")

    Examples:
        >>> # Single layer cache path
        >>> fp = get_cache_fp("gpt2", "Hello world", 5)
        >>> # Returns: Path(".nnez/gpt2/a1b2c3d4e5f67890_5.npy")

        >>> # Consecutive layers get compressed notation
        >>> fp = get_cache_fp("gpt2", "Hello world", [0, 1, 2, 3])
        >>> # Returns: Path(".nnez/gpt2/a1b2c3d4e5f67890_0-3.npy")

        >>> # Non-consecutive layers list all indices
        >>> fp = get_cache_fp("gpt2", "Hello world", [0, 5, 10])
        >>> # Returns: Path(".nnez/gpt2/a1b2c3d4e5f67890_0_5_10.npy")

    Notes:
        - Text is hashed using SHA256 (truncated to 16 chars) for consistent,
          privacy-preserving filenames
        - The cache directory structure is created automatically when saving
        - Cached files are numpy arrays stored in .npy format for efficient loading
    """
    model_dir = Path(cache_dir) / model_name
    text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

    if isinstance(layers_list, int):
        cache_fp = model_dir / f"{text_hash}_{layers_list}.npy"
    else:
        all_increasing = True
        for i in range(len(layers_list) - 1):
            if layers_list[i] == layers_list[i + 1] - 1:
                pass
            else:
                all_increasing = False
                break
        if all_increasing:
            cache_fp = (
                model_dir
                / f"{text_hash}_{layers_list[0]}-{layers_list[-1]}.npy"
            )
        else:
            layer_list_str = "_".join(map(str, layers_list))
            cache_fp = model_dir / f"{text_hash}_{layer_list_str}.npy"
    return cache_fp


def get_activity_from_text(
    text: Union[str, List[str]],
    layers_list: Union[List[int], int],
    model_name: str = "gpt2",  # Default to public model that doesn't require auth
    device: Optional[str] = None,
    verbose: bool = False,
    cache_activations: bool = True,
    cache_dir: Optional[Union[Path, str]] = ".nnez",
    cache_overwrite: bool = False,
    cache_model: bool = True,
) -> np.ndarray:
    """
    Extract residual stream activity from specified layers at the last token position.

    Args:
        text (str or List[str]): Input text(s) to analyze
        layers_list (List[int] or int): List of layer indices to extract activations
                                        from or int for a single layer
        model_name (str): Hugging Face model name/path
        device (str, optional): Device to use ('cuda', 'cpu', or None for auto)
        verbose (bool): Whether to print debug information
        cache_model (bool): Whether to cache the model and tokenizer,
                            helps avoid re-loading the model and tokenizer

    Returns:
        np.ndarray: Residual stream activities from specified layers
                   at the last token position. Shape: (num_texts, num_layers, hidden_size)
                   where each row corresponds to one layer's activations.
                   If a single text is provided, the num_texts dimension disappears
                   If a single layer is requested as an int, the num_layers dimension disappears

    Raises:
        ValueError: If layers are out of bounds or model architecture is unsupported
        RuntimeError: If activation extraction fails
    """

    if cache_activations:
        cache_fp = get_cache_fp(model_name, text, layers_list, cache_dir)
        if cache_fp.exists() and not cache_overwrite:
            return np.load(cache_fp)
        else:
            pass
    else:
        cache_fp = None

    # Determine device
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    if verbose:
        print(f"Using device: {device}")
        print(f"Model: {model_name}")
        print(f"Extracting from layers: {layers_list}")

    if isinstance(layers_list, int):
        layers_list = [layers_list]
        int_layer = True
    else:
        int_layer = False

    # Suppress the GPT2TokenizerFast warning that appears even when using the correct method
    os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "true"
    # Initialize the model and tokenizer
    if cache_model:
        model, tokenizer = get_model_cached(model_name)
    else:
        model = LanguageModel(model_name, device_map=device)
        tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Set pad token if needed
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Tokenize the input text
    inputs = tokenizer(
        text, return_tensors="pt", padding=False, truncation=True
    )
    input_ids = inputs["input_ids"].to(device)

    # Validate layer indices
    # Get the number of layers in the model
    # Handle different model architectures
    if hasattr(model, "transformer") and hasattr(model.transformer, "h"):
        # GPT-2 style models
        num_layers = len(model.transformer.h)
        layer_attr = "transformer.h"
    elif hasattr(model, "model") and hasattr(model.model, "layers"):
        # LLaMA/Mistral style models
        num_layers = len(model.model.layers)
        layer_attr = "model.layers"
    elif hasattr(model, "model") and hasattr(model.model, "h"):
        # Some other GPT-style models
        num_layers = len(model.model.h)
        layer_attr = "model.h"
    elif (
        hasattr(model, "model")
        and hasattr(model.model, "encoder")
        and hasattr(model.model.encoder, "layer")
    ):
        # BERT style models
        num_layers = len(model.model.encoder.layer)
        layer_attr = "model.encoder.layer"
    else:
        # Try to inspect the model structure
        print(f"Model structure: {model}")
        raise ValueError(f"Unsupported model architecture for {model_name}")

    # Check if all requested layers are valid
    invalid_layers = [l for l in layers_list if l >= num_layers or l < 0]
    if invalid_layers:
        raise ValueError(
            f"Invalid layer indices {invalid_layers}. "
            f"Model has {num_layers} layers (indices 0-{num_layers-1})"
        )

    # Get the position of the last token
    seq_len = input_ids.shape[1]
    last_token_pos = seq_len - 1

    if verbose:
        print(f"Input tokens: {seq_len}")
        print(f"Last token position: {last_token_pos}")
        tokens = tokenizer.convert_ids_to_tokens(input_ids[0])
        print(f"Tokens: {tokens}")

    # List to store activations from each layer
    layer_activations = []

    # Run the model with tracing to extract activations
    with torch.no_grad():  # I think this helps prevent memory leaks
        with model.trace(input_ids) as tracer:
            # Extract activations from each specified layer
            for layer_idx in layers_list:
                if verbose:
                    print(f"  Extracting from layer {layer_idx}...")

                # Access the appropriate layer based on model architecture
                if layer_attr == "transformer.h":
                    # GPT-2 style
                    hidden_states = model.transformer.h[layer_idx].output[0]
                elif layer_attr == "model.layers":
                    # LLaMA style
                    hidden_states = model.model.layers[layer_idx].output[0]
                elif layer_attr == "model.h":
                    # Other GPT style
                    hidden_states = model.model.h[layer_idx].output[0]
                elif layer_attr == "model.encoder.layer":
                    # BERT style
                    hidden_states = model.model.encoder.layer[layer_idx].output[
                        0
                    ]

                # Extract activation at the last token position
                # Shape: (batch_size=1, seq_len, hidden_size) -> (1, hidden_size)
                last_token_activation = hidden_states[:, last_token_pos, :]

                # Save the activation (we'll extract later outside the trace)
                saved_act = last_token_activation.save()
                layer_activations.append(saved_act)

                if verbose:
                    print(f"    Saved activation for layer {layer_idx}")

    # Extract saved activations and convert to numpy
    numpy_activations = []
    for i, saved_activation in enumerate(layer_activations):
        # Get the tensor value and convert to numpy
        if hasattr(saved_activation, "value"):
            tensor = saved_activation.value
        else:
            tensor = saved_activation

        # Remove batch dimension and convert to numpy
        # Shape: (1, hidden_size) -> (hidden_size,)
        numpy_array = tensor.squeeze(0).detach().cpu().numpy()
        numpy_activations.append(numpy_array)

        if verbose:
            print(f"Layer {layers_list[i]} shape: {numpy_array.shape}")

    # Stack into a 2D array: (num_layers, hidden_size)
    result = np.stack(numpy_activations)

    if verbose:
        print(f"Final output shape: {result.shape}")
        print(
            f"Output stats - Min: {result.min():.4f}, Max: {result.max():.4f}, Mean: {result.mean():.4f}"
        )

    if int_layer:
        result = result.squeeze(0)

    if cache_fp:
        Path(cache_fp).parent.mkdir(parents=True, exist_ok=True)
        np.save(cache_fp, result)

    return result


if __name__ == "__main__":
    print("=" * 70)
    print("RESIDUAL STREAM EXTRACTION - EXAMPLE USAGE")
    print("=" * 70)

    text = "The quick brown fox jumps over the lazy dog."

    layers_to_extract_l = [[0, 3, 6, 9, 11], 5, [5]]
    for layers_to_extract in layers_to_extract_l:
        activations = get_activity_from_text(
            text=text,
            layers_list=layers_to_extract,
            model_name="gpt2",
        )
        print(f"Layers: {layers_to_extract}, extracted: {activations.shape=}")

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-XX-XX

### Added
- Initial release of nnez package
- Core functionality for extracting LLM activations from transformer models
- Support for multiple model architectures (GPT-2, BERT, LLaMA, etc.)
- Flexible layer selection with single or multiple layer extraction
- NumPy array output format for easy integration with scientific Python
- Model caching for improved performance in repeated extractions
- Grammar utilities using inflect library:
  - Smart article detection (a/an)
  - Pluralization and singularization
  - Quantification with automatic plural handling
- Comprehensive documentation and examples
- Type hints for better IDE support
- Support for both CPU and CUDA devices

### Features
- Single-line activation extraction from any HuggingFace transformer model
- Automatic handling of different model architectures
- Batch processing support
- Verbose mode for debugging
- Proper noun detection
- Mass noun recognition

### Technical Details
- Built on top of NNsight for model introspection
- Compatible with transformers >= 4.20.0
- Requires Python >= 3.8
- Full type annotations
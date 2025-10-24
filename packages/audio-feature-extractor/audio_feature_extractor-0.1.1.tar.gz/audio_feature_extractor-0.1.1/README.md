# Audio Feature Extractor

A simple and extensible tool for extracting audio features, designed for speech and audio experiments.

## Features

- Extracts traditional audio features (pitch, timbre, loudness, etc.)
- Supports English and Chinese G2P (grapheme-to-phoneme) conversion
- Embedding and semantic feature extraction (e.g., speaker embeddings, ASR, etc.)
- Modular design for easy extension

## Installation

1. **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd audio_feature_extractor
    ```

2. **Install dependencies:**
    ```bash
    pip install .
    ```
    > **Note:** For GPU support, install the appropriate version of PyTorch for your CUDA version before running `pip install .`. See [PyTorch Get Started](https://pytorch.org/get-started/locally/) for details.

## Usage

```python
from audio_feature_extractor import FeatureExtractor

extractor = FeatureExtractor()
audio_path = "tmp/test.wav"
features = extractor.extract_features(audio_path)
print(features)
```

## Project Structure

```
src/audio_feature_extractor/
    extractor.py
    features/
        traditional.py
        embedding.py
        semantic.py
    g2p/
```

## Notes

- This tool is intended for research and experimental use.
- For large models or neural network weights, see the documentation for download instructions.
- If you encounter CUDA/cuDNN or dependency issues, please refer to the [Troubleshooting](#troubleshooting) section below.

## Troubleshooting

- **CUDA/cuDNN errors:**  
  Make sure your environment variables (e.g., `LD_LIBRARY_PATH`) are set correctly and that you have installed the correct CUDA/cuDNN versions. 
- **PyTorch version:**  
  Install the correct PyTorch version for your hardware and CUDA version before installing this package.

## License

[MIT](LICENSE) 

## Changelog

### v0.1.0

- Initial release: basic usage for English speech feature extraction.

---

Feel free to contribute or open issues!
# Email Signature Detector

[![PyPI version](https://badge.fury.io/py/email-signature-detector.svg)](https://badge.fury.io/py/email-signature-detector)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Email Signature Detector** is a Python library for accurately identifying and extracting email signatures from raw email text. It leverages a fine-tuned BERT model packaged in ONNX format for efficient, cross-platform inference.

This tool is designed to be simple to integrate, providing clear and actionable output that includes not only the signature text but also its precise location (character and token indices) within the email body.

## Key Features

- **High Accuracy**: Utilizes a state-of-the-art transformer model for robust signature detection.
- **Efficient and Portable**: The model is converted to ONNX format, ensuring fast inference with minimal dependencies.
- **Detailed Output**: Provides the start and end character indices of the signature, making it easy to slice and process email content.
- **Easy to Use**: A straightforward API that requires only a few lines of code to integrate.
- **Bundled Model**: The ONNX model and tokenizer are included with the package, so no extra downloads are needed.

## Installation

You can install the library directly from PyPI:

```bash
pip install email-signature-detector
```

## How to Use

Here is a simple example of how to use the `ONNXSignaturePredictor` to detect and extract an email signature.

```python
from email_signature_detector import ONNXSignaturePredictor

# 1. Instantiate the predictor
# The model is bundled with the package, so no arguments are needed.
predictor = ONNXSignaturePredictor()

# 2. Define the email text
email_text = """Hi Team,

I hope this email finds you well.

I'm writing to follow up on our discussion from last week's meeting. I've attached the document with the updated project timeline. Please review it and provide your feedback by the end of the day.

Also, a quick reminder that the quarterly review is scheduled for this Friday.

Thanks for your cooperation.

Best regards,
John Doe
Senior Project Manager
"""

# 3. Get the prediction
result = predictor.predict(email_text)

# 4. Use the results
if result["has_signature"]:
    signature_data = result["signature"]
    start_char = signature_data.get("start_token")
    end_char = signature_data.get("end_token")

    print("--- Signature Found ---")
    if start_char is not None and end_char is not None:
        # Extract the body and signature using character indices
        email_body = email_text[:start_char].strip()
        signature = email_text[start_char:end_char]

        print(f"\nEmail Body:\n'{email_body}'")
        print(f"\nSignature:\n'{signature}'")
    else:
        # Fallback if character indices are not available
        print(f"Signature Text: '{signature_data['text']}'")
else:
    print("No signature was detected.")

```

### Prediction Output

The `predict` method returns a dictionary with the following structure:

```json
{
  "has_signature": true,
  "confidence": 0.98,
  "signature": {
    "text": "Best regards,\nJohn Doe\nSenior Project Manager",
    "start_token": 45,
    "end_token": 55,
  },
  "body": "Hi Team, ... Thanks for your cooperation."
}
```

## API Reference

### `ONNXSignaturePredictor`

The main class for making predictions.

`__init__(self, model_path=None, tokenizer_path=None, confidence_threshold=0.5)`

-   `model_path` (Optional[Path]): Path to a custom ONNX model file. Defaults to the bundled model.
-   `tokenizer_path` (Optional[Path]): Path to a custom tokenizer. Defaults to the bundled tokenizer.
-   `confidence_threshold` (float): The minimum average confidence for a span to be considered a signature.

`predict(self, email_text: str) -> Dict`

-   `email_text` (str): The raw email content to be processed.
-   Returns: A dictionary containing the prediction results.

`predict_batch(self, email_texts: List[str], batch_size=32) -> List[Dict]`

-   `email_texts` (List[str]): A list of email contents to be processed in a batch.
-   `batch_size` (int): The number of emails to process at once.
-   Returns: A list of prediction dictionaries.

## For Developers

### Publishing to PyPI

If you contribute to the project and need to publish a new version, follow these steps.

**1. Install Build Tools**

Make sure you have the latest versions of `build` and `twine`:

```bash
pip install --upgrade build twine
```

**2. Build the Package**

From the root of the project, run the build command:

```bash
python3 -m build
```

This command will create a `dist` directory containing the distribution files (`.tar.gz` and `.whl`).

**3. Upload to PyPI**

Use `twine` to upload the package to the official PyPI repository. You will need a PyPI account and an API token.

```bash
python3 -m twine upload dist/*
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

*This README was generated with assistance from an AI pair programmer.*
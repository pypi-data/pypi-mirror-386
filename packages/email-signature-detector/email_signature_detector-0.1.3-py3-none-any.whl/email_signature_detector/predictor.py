"""
ONNX-based predictor for email signature detection.
"""

import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional
import onnxruntime as ort

from .utils import decode_signature_span, format_signature_detection_result

logger = logging.getLogger(__name__)


class ONNXSignaturePredictor:
    """ONNX Runtime predictor for email signature detection."""

    def __init__(
        self,
        model_path: Optional[Path] = None,
        tokenizer_path: Optional[Path] = None,
        providers: List[str] = None,
        confidence_threshold: float = 0.5,
        min_signature_tokens: int = 3
    ):
        """
        Initialize predictor.

        Args:
            model_path: Path to ONNX model file
            tokenizer_path: Path to tokenizer directory
            providers: ONNX execution providers
            confidence_threshold: Minimum confidence for signature detection
            min_signature_tokens: Minimum tokens for valid signature
        """
        # Default to bundled model if no path is provided
        if model_path is None:
            model_path = Path(__file__).parent / "model" / \
                "modernbert_sig_int8.onnx"

        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.min_signature_tokens = min_signature_tokens

        # Download model if it doesn't exist
        if not self.model_path.exists():
            self._download_model()

        # Default providers
        if providers is None:
            providers = ['CPUExecutionProvider']

        logger.info(f"Loading ONNX model from {self.model_path}")
        logger.info(f"Using providers: {providers}")

        # Load ONNX model
        self.session = ort.InferenceSession(
            str(self.model_path),
            providers=providers
        )

        # Load tokenizer
        from transformers import AutoTokenizer

        if tokenizer_path is None:
            tokenizer_path = self.model_path.parent / "tokenizer"

        logger.info(f"Loading tokenizer from {tokenizer_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_path))

        logger.info("Predictor initialized successfully")

    def _download_model(self):
        """Download the ONNX model if it doesn't exist."""
        import urllib.request

        model_url = "https://media.githubusercontent.com/media/numeo-ai/email-signature-detector/main/src/email_signature_detector/model/modernbert_sig_int8.onnx"

        # Create model directory if it doesn't exist
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading model from {model_url}")
        logger.info(f"Saving to {self.model_path}")

        try:
            # Try to import tqdm for progress bar
            try:
                from tqdm import tqdm

                def progress_hook(block_num, block_size, total_size):
                    if not hasattr(progress_hook, 'pbar'):
                        progress_hook.pbar = tqdm(
                            total=total_size,
                            unit='B',
                            unit_scale=True,
                            desc="Downloading model"
                        )
                    progress_hook.pbar.update(block_size)

                    # Close progress bar when download is complete
                    if block_num * block_size >= total_size:
                        progress_hook.pbar.close()

                urllib.request.urlretrieve(model_url, str(
                    self.model_path), reporthook=progress_hook)

            except ImportError:
                # Fallback to basic download without progress bar
                logger.info(
                    "tqdm not available, downloading without progress bar...")
                urllib.request.urlretrieve(model_url, str(self.model_path))

            logger.info("Model downloaded successfully!")
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            raise RuntimeError(
                f"Could not download model from {model_url}. "
                f"Please download it manually to {self.model_path}"
            )

    def predict(
        self,
        email_text: str,
        return_logits: bool = False
    ) -> Dict:
        """
        Predict signature in email.

        Args:
            email_text: Email text
            return_logits: Whether to return raw logits

        Returns:
            Prediction dictionary
        """
        # Tokenize
        inputs = self.tokenizer(
            email_text,
            return_tensors="np",
            padding="max_length",
            max_length=512,
            truncation=True
        )

        # Prepare ONNX inputs
        onnx_inputs = {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64)
        }

        # Run inference
        outputs = self.session.run(None, onnx_inputs)
        logits = outputs[0][0]  # [seq_len, num_labels]

        # Get tokens
        tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

        # Decode signature span
        detection_result = decode_signature_span(
            logits,
            tokens,
            confidence_threshold=self.confidence_threshold,
            min_signature_tokens=self.min_signature_tokens
        )

        # Format result
        result = format_signature_detection_result(
            email_text,
            detection_result,
            include_body=True
        )

        if return_logits:
            result["logits"] = logits.tolist()

        return result

    def detect_signature(
        self,
        email_text: str,
    ) -> bool:
        """
        Detects signature in the email and returns prediction dictionary.

        Args:
            email_text: Email text

        Returns:
            Prediction dictionary
        """
        result = self.predict(email_text)
        return result

    def predict_batch(
        self,
        email_texts: List[str],
        batch_size: int = 32
    ) -> List[Dict]:
        """
        Predict signatures for multiple emails.

        Args:
            email_texts: List of email texts
            batch_size: Batch size for processing

        Returns:
            List of prediction dictionaries
        """
        results = []

        for i in range(0, len(email_texts), batch_size):
            batch = email_texts[i:i + batch_size]

            # Tokenize batch
            inputs = self.tokenizer(
                batch,
                return_tensors="np",
                padding="max_length",
                max_length=512,
                truncation=True
            )

            # Prepare ONNX inputs
            onnx_inputs = {
                "input_ids": inputs["input_ids"].astype(np.int64),
                "attention_mask": inputs["attention_mask"].astype(np.int64)
            }

            # Run inference
            outputs = self.session.run(None, onnx_inputs)
            logits = outputs[0]  # [batch_size, seq_len, num_labels]

            # Process each sample
            for j, email_text in enumerate(batch):
                tokens = self.tokenizer.convert_ids_to_tokens(
                    inputs["input_ids"][j])

                detection_result = decode_signature_span(
                    logits[j],
                    tokens,
                    confidence_threshold=self.confidence_threshold,
                    min_signature_tokens=self.min_signature_tokens
                )

                result = format_signature_detection_result(
                    email_text,
                    detection_result,
                    include_body=True
                )

                results.append(result)

        return results

    def get_model_info(self) -> Dict:
        """
        Get model information.

        Returns:
            Model info dictionary
        """
        input_meta = self.session.get_inputs()[0]
        output_meta = self.session.get_outputs()[0]

        return {
            "model_path": str(self.model_path),
            "input_name": input_meta.name,
            "input_shape": input_meta.shape,
            "input_type": input_meta.type,
            "output_name": output_meta.name,
            "output_shape": output_meta.shape,
            "output_type": output_meta.type,
            "providers": self.session.get_providers()
        }


email_signature_detector = ONNXSignaturePredictor()

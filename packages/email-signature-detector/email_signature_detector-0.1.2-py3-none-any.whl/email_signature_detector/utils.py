"""
Utility functions for inference and post-processing.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


def decode_signature_span(
    logits: np.ndarray,
    tokens: List[str],
    confidence_threshold: float = 0.5,
    min_signature_tokens: int = 3
) -> Dict:
    """
    Decode logits to extract signature span.
    
    Args:
        logits: Model logits [seq_len, num_labels]
        tokens: Token strings
        confidence_threshold: Minimum confidence for signature detection
        min_signature_tokens: Minimum tokens to consider valid signature
        
    Returns:
        Dictionary with:
            - signature_present: bool
            - start_token: int or None
            - end_token: int or None
            - confidence: float
            - signature_text: str or None
    """
    # Get predicted labels
    probs = softmax(logits, axis=-1)
    pred_labels = np.argmax(logits, axis=-1)
    max_probs = np.max(probs, axis=-1)
    
    # Find signature tokens (labels 1 or 2)
    sig_indices = np.where((pred_labels == 1) | (pred_labels == 2))[0]
    
    if len(sig_indices) < min_signature_tokens:
        return {
            "signature_present": False,
            "start_token": None,
            "end_token": None,
            "confidence": 0.0,
            "signature_text": None
        }
    
    # Get start and end
    start_idx = int(sig_indices[0])
    end_idx = int(sig_indices[-1])
    
    # Compute average confidence
    sig_confidences = max_probs[sig_indices]
    avg_confidence = float(np.mean(sig_confidences))
    
    # Extract signature text
    sig_tokens = tokens[start_idx:end_idx + 1]
    sig_text = reconstruct_text_from_tokens(sig_tokens)
    
    return {
        "signature_present": avg_confidence >= confidence_threshold,
        "start_token": start_idx,
        "end_token": end_idx,
        "confidence": avg_confidence,
        "signature_text": sig_text
    }


def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    """Compute softmax."""
    exp_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


def reconstruct_text_from_tokens(tokens: List[str]) -> str:
    """
    Reconstruct text from tokens.
    
    Args:
        tokens: List of token strings
        
    Returns:
        Reconstructed text
    """
    # Handle subword tokens (##)
    text = ""
    for token in tokens:
        if token.startswith("##"):
            text += token[2:]
        elif token in ["[CLS]", "[SEP]", "[PAD]"]:
            continue
        else:
            if text and not text.endswith(" "):
                text += " "
            text += token
    
    return text.strip()


def extract_email_body(
    email_text: str,
    signature_start: Optional[int],
    signature_end: Optional[int]
) -> str:
    """
    Extract email body (content without signature).
    
    Args:
        email_text: Full email text
        signature_start: Character index of signature start
        signature_end: Character index of signature end
        
    Returns:
        Email body without signature
    """
    if signature_start is None:
        return email_text
    
    return email_text[:signature_start].strip()


def char_to_token_alignment(
    text: str,
    encoding,
    char_indices: Tuple[int, int]
) -> Tuple[int, int]:
    """
    Convert character indices to token indices.
    
    Args:
        text: Original text
        encoding: Tokenizer encoding
        char_indices: (start_char, end_char)
        
    Returns:
        (start_token, end_token)
    """
    start_char, end_char = char_indices
    
    # Find corresponding token indices
    start_token = None
    end_token = None
    
    for token_idx in range(len(encoding.tokens())):
        char_span = encoding.token_to_chars(token_idx)
        if char_span is None:
            continue
        
        token_start, token_end = char_span
        
        if start_token is None and token_start <= start_char < token_end:
            start_token = token_idx
        
        if token_start < end_char <= token_end:
            end_token = token_idx
            break
    
    return start_token, end_token


def format_signature_detection_result(
    email_text: str,
    detection_result: Dict,
    include_body: bool = True
) -> Dict:
    """
    Format signature detection result for API response.
    
    Args:
        email_text: Original email text
        detection_result: Detection result from decode_signature_span
        include_body: Whether to include extracted body
        
    Returns:
        Formatted response dictionary
    """
    response = {
        "has_signature": detection_result["signature_present"],
        "confidence": detection_result["confidence"],
        "signature": {
            "text": detection_result["signature_text"],
            "start_token": detection_result["start_token"],
            "end_token": detection_result["end_token"]
        }
    }
    
    if include_body and detection_result["signature_present"]:
        # Extract body (everything before signature)
        sig_text = detection_result["signature_text"]
        if sig_text and sig_text in email_text:
            body = email_text[:email_text.index(sig_text)].strip()
            response["body"] = body
    
    return response


class SignatureDetectionCache:
    """Simple LRU cache for signature detection."""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize cache.
        
        Args:
            max_size: Maximum number of items to cache
        """
        from collections import OrderedDict
        self.cache = OrderedDict()
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached result."""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def put(self, key: str, value: Dict):
        """Cache result."""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                # Remove least recently used
                self.cache.popitem(last=False)
            self.cache[key] = value
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()


def compute_text_hash(text: str) -> str:
    """
    Compute hash of text for caching.
    
    Args:
        text: Input text
        
    Returns:
        Hash string
    """
    import hashlib
    return hashlib.md5(text.encode()).hexdigest()

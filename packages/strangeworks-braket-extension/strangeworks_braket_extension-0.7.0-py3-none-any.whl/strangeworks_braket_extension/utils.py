"""utils.py."""

from collections import Counter
from typing import Any

import numpy as np


def _serialize_result(obj: Any):
    """Custom Serializer for Braket Results

    Converts numpy types, Counter, sets, Pydantic models, and complex objects to
    JSON-serializable types for transmission to the Strangeworks platform.

    This function handles Braket result objects that may contain:
    - NumPy arrays and scalar types (converted to Python native types)
    - Counter objects (converted to dicts)
    - Pydantic models v1 and v2 (converted via dict() or model_dump())
    - Arbitrary objects with __dict__ (serialized as dictionaries)
    - Objects using __slots__ (fallback to string representation)

    The serialization order is important:
    1. Pydantic models are detected first to use their built-in serialization
    2. Objects with __dict__ are serialized by extracting their attributes
    3. Only objects without __dict__ (like slotted objects) fall back to str()

    This approach ensures that Braket result objects, which are typically complex
    objects with nested Pydantic models and NumPy arrays, are properly converted
    to JSON-compatible structures.

    Parameters
    ----------
    obj : Any
        Result from Braket.

    Returns
    -------
    Any
        Result as a JSON-serializable object (dict, list, or primitive type).
    """
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, Counter):
        return dict(obj)
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, (list, tuple)):
        return [_serialize_result(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: _serialize_result(v) for k, v in obj.items()}
    elif hasattr(obj, "dict") and hasattr(obj, "__fields__"):
        # Pydantic v1 model - use dict() method for proper serialization
        # Recursively serialize the dict to handle nested Pydantic models and NumPy types
        return _serialize_result(obj.dict())
    elif hasattr(obj, "model_dump") and hasattr(obj, "model_fields"):
        # Pydantic v2 model - use model_dump() method for proper serialization
        # Recursively serialize the dict to handle nested Pydantic models and NumPy types
        return _serialize_result(obj.model_dump())
    elif hasattr(obj, "__dict__"):
        # Serialize arbitrary objects by extracting their __dict__ attributes
        # This handles most Python objects including Braket result components
        return {k: _serialize_result(v) for k, v in obj.__dict__.items()}
    else:
        # Fallback for objects without __dict__ (e.g., objects using __slots__)
        # Try to convert to string representation, or None if that fails
        try:
            return str(obj)
        except Exception:
            return None

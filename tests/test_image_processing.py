"""
Image processing utilities: brightness/contrast adjustments.

GDCM / pylibjpeg decompression helpers have been removed — decompression is
now handled transparently by pydicom itself in core/loaders.py.
"""

import numpy as np


def adjust_brightness_contrast(image: np.ndarray, brightness: int, contrast: int) -> np.ndarray:
    """
    Apply brightness and contrast to a uint8 image with linear, predictable response.

    Algorithm
    ---------
    1. Normalise to [0, 1].
    2. Brightness: simple additive offset mapped linearly to [-1, +1].
       The response is perfectly uniform across the full slider travel.
    3. Contrast: scale around the midpoint (0.5).
       Slider -255 -> x0.0 (flat grey), 0 -> x1.0 (unchanged), +255 -> x4.0.
       Squaring the normalised factor gives a smooth, singularity-free curve.
    4. Clip to [0, 1] and convert back to uint8.

    Args:
        image:      2-D numpy array (any numeric dtype).
        brightness: Integer in [-255, 255]. 0 = no change.
        contrast:   Integer in [-255, 255]. 0 = no change.

    Returns:
        Adjusted image as uint8, values clipped to [0, 255].
    """
    img = image.astype(np.float32) / 255.0  # normalise to [0, 1]

    # Brightness: linear offset, full slider range maps to [-1, +1]
    img += brightness / 255.0

    # Contrast: scale around midpoint; squaring gives smooth [0..4] multiplier
    if contrast != 0:
        factor = ((contrast + 255.0) / 255.0) ** 2  # 0->0, 127->~1, 255->4
        img = (img - 0.5) * factor + 0.5

    return np.clip(img * 255.0, 0, 255).astype(np.uint8)

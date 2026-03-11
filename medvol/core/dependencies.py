"""
Optional dependency detection.

We no longer manually invoke gdcm or pylibjpeg — pydicom handles decompression
transparently when these packages are installed.  We keep the detection here
only to show a helpful warning in the UI if a file fails to decode.
"""

try:
    import gdcm  # noqa: F401  — probe only; pydicom uses it transparently

    GDCM_AVAILABLE = True
except ImportError:
    GDCM_AVAILABLE = False

try:
    import pylibjpeg  # noqa: F401  — probe only; pydicom uses it transparently

    PYLIBJPEG_AVAILABLE = True
except ImportError:
    PYLIBJPEG_AVAILABLE = False

# pydicom ≥ 2.1 ships its own fallback handler; detect it too
try:
    import pydicom.pixels  # noqa: F401  (exists in pydicom ≥ 2.4)

    PYDICOM_PIXELS = True
except ImportError:
    PYDICOM_PIXELS = False

# We consider compression "handleable" if any backend is present
ANY_COMPRESSION_BACKEND = GDCM_AVAILABLE or PYLIBJPEG_AVAILABLE or PYDICOM_PIXELS

COMPRESSION_HANDLERS = {
    "jpeg": PYLIBJPEG_AVAILABLE or GDCM_AVAILABLE,
    "j2k": GDCM_AVAILABLE,
    "rle": GDCM_AVAILABLE,
}

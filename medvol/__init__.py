"""
MEDVOL — 3D Medical Image Viewer

Brutalist open-source viewer for DICOM and NIfTI volumes.
Built with PyQt5, VTK, and Matplotlib.
"""

__version__ = "1.0.0"
__author__ = "YOUR_NAME"
__license__ = "MIT"

# Public programmatic API — importable without starting Qt
from medvol.core.loaders import (
    load_nifti_file,
    load_dicom_file,
    load_dicom_folder,
)
from medvol.utils.image_processing import adjust_brightness_contrast

__all__ = [
    "load_nifti_file",
    "load_dicom_file",
    "load_dicom_folder",
    "adjust_brightness_contrast",
    "__version__",
]

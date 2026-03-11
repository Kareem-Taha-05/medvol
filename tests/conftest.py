"""
Shared pytest fixtures for MEDVOL tests.

All test data is synthetic — no real patient files are used or committed.
"""

import numpy as np
import pytest
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import UID
import io


# ── Synthetic volume ────────────────────────────────────────────────────────────

@pytest.fixture
def synthetic_volume() -> np.ndarray:
    """
    A small (32, 64, 64) uint8 volume with a bright sphere in the centre.
    Shape: Z=32 slices, Y=64 rows, X=64 cols.
    """
    vol = np.zeros((32, 64, 64), dtype=np.uint8)
    z, y, x = np.ogrid[:32, :64, :64]
    mask = (z - 16)**2 + (y - 32)**2 + (x - 32)**2 < 15**2
    vol[mask] = 200   # bright sphere — simulates bone density
    # Inner softer region
    inner = (z - 16)**2 + (y - 32)**2 + (x - 32)**2 < 8**2
    vol[inner] = 80   # simulates soft tissue
    return vol


@pytest.fixture
def anisotropic_volume() -> np.ndarray:
    """
    Volume where Z spacing is 6× larger than XY (common in clinical CT).
    Used to verify that callers handle non-isotropic spacing.
    """
    return np.random.randint(0, 255, (16, 64, 64), dtype=np.uint8)


# ── Synthetic DICOM datasets ────────────────────────────────────────────────────

def _make_dicom_dataset(
    rows: int = 64,
    cols: int = 64,
    instance_number: int = 1,
    series_uid: str = "1.2.3.4.5",
    pixel_spacing: tuple[float, float] = (0.5, 0.5),
    slice_thickness: float = 3.0,
) -> Dataset:
    """Create a minimal in-memory DICOM dataset with synthetic pixel data."""
    ds = Dataset()
    ds.file_meta = Dataset()
    ds.file_meta.TransferSyntaxUID = UID("1.2.840.10008.1.2.1")  # Explicit Little Endian
    ds.file_meta.MediaStorageSOPClassUID = UID("1.2.840.10008.5.1.4.1.1.2")
    ds.file_meta.MediaStorageSOPInstanceUID = UID(f"1.2.3.4.5.6.{instance_number}")

    ds.SOPClassUID = UID("1.2.840.10008.5.1.4.1.1.2")
    ds.SOPInstanceUID = UID(f"1.2.3.4.5.6.{instance_number}")
    ds.SeriesInstanceUID = UID(series_uid)
    ds.StudyInstanceUID = UID("9.8.7.6.5")

    ds.Modality = "CT"
    ds.Rows = rows
    ds.Columns = cols
    ds.InstanceNumber = instance_number
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelSpacing = list(pixel_spacing)
    ds.SliceThickness = slice_thickness
    ds.RescaleSlope = 1.0
    ds.RescaleIntercept = -1024.0
    ds.NumberOfFrames = 1

    # Random pixel data
    pixel_data = np.random.randint(0, 4096, (rows, cols), dtype=np.uint16)
    ds.PixelData = pixel_data.tobytes()

    ds.is_implicit_VR = False
    ds.is_little_endian = True
    return ds


@pytest.fixture
def dicom_dataset() -> Dataset:
    """Single-frame DICOM dataset with pixel spacing metadata."""
    return _make_dicom_dataset()


@pytest.fixture
def dicom_series(tmp_path) -> list:
    """
    A list of 10 DICOM file paths written to a temp directory.
    Shares one SeriesInstanceUID, sorted by InstanceNumber.
    """
    import pydicom
    paths = []
    for i in range(1, 11):
        ds = _make_dicom_dataset(instance_number=i)
        path = tmp_path / f"slice_{i:04d}.dcm"
        pydicom.dcmwrite(str(path), ds)
        paths.append(str(path))
    return paths


@pytest.fixture
def dicom_folder(dicom_series, tmp_path) -> str:
    """Path to a temp folder containing a 10-slice DICOM series."""
    return str(tmp_path)
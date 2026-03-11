"""
Volume loading: single DICOM file, DICOM folder series, and NIfTI file ingestion.

Compression strategy
--------------------
Rather than manually invoking gdcm or pylibjpeg, we let pydicom handle
decompression transparently via its own handler chain.  This works for the
vast majority of DICOM files, including JPEG, JPEG 2000, and RLE, as long as
the user has any of these installed:
    pip install pylibjpeg pylibjpeg-libjpeg   # JPEG / JPEG-LS
    pip install python-gdcm                    # JPEG 2000 / RLE (Windows-friendly)
    pip install gdcm                           # alternative gdcm package

We only raise an explicit error if pixel_array itself raises, passing the
original exception message to the user so they know what to install.

Voxel spacing
-------------
DICOM slices carry PixelSpacing (row/col spacing in mm) and the series carries
SliceThickness / SpacingBetweenSlices.  We read these and resample the volume
so voxels are isotropic before handing it to the viewer, which fixes the
stretched/squashed appearance on multi-frame and folder-series DICOMs.
"""

import os
from collections import Counter

import numpy as np
import pydicom
import nibabel as nib
from scipy.ndimage import zoom as ndimage_zoom
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QProgressDialog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalise_to_uint8(arr: np.ndarray) -> np.ndarray:
    """Normalise any numeric ndarray to uint8 [0, 255]."""
    arr = arr.astype(np.float32)
    mn, mx = arr.min(), arr.max()
    if mx > mn:
        return ((arr - mn) * 255.0 / (mx - mn)).astype(np.uint8)
    return np.zeros_like(arr, dtype=np.uint8)


def _pixel_array(ds) -> np.ndarray:
    """
    Return the pixel array for a pydicom dataset.
    Lets pydicom + whatever backend is installed handle decompression.
    Raises a clear exception if it cannot decode.
    """
    try:
        return ds.pixel_array
    except Exception as exc:
        raise Exception(
            f"Cannot decode pixel data: {exc}\n\n"
            "Try installing one of:\n"
            "  pip install pylibjpeg pylibjpeg-libjpeg\n"
            "  pip install python-gdcm"
        ) from exc


def _read_pixel_spacing(ds) -> tuple[float, float]:
    """Return (row_spacing_mm, col_spacing_mm) from PixelSpacing or (1, 1)."""
    ps = getattr(ds, "PixelSpacing", None)
    if ps and len(ps) == 2:
        return float(ps[0]), float(ps[1])
    return 1.0, 1.0


def _read_slice_spacing(datasets: list) -> float:
    """
    Derive slice spacing (mm) from a list of datasets.
    Tries SpacingBetweenSlices, then SliceThickness, then ImagePositionPatient,
    falling back to 1.0.
    """
    if not datasets:
        return 1.0

    ds = datasets[0]

    sbs = getattr(ds, "SpacingBetweenSlices", None)
    if sbs:
        return abs(float(sbs))

    st = getattr(ds, "SliceThickness", None)
    if st:
        return abs(float(st))

    # Try to derive from ImagePositionPatient z-coordinates
    if len(datasets) >= 2:
        pos0 = getattr(datasets[0], "ImagePositionPatient", None)
        pos1 = getattr(datasets[-1], "ImagePositionPatient", None)
        if pos0 and pos1:
            dz = abs(float(pos1[2]) - float(pos0[2]))
            if dz > 0:
                return dz / max(len(datasets) - 1, 1)

    return 1.0


def _resample_isotropic(
    volume: np.ndarray, row_sp: float, col_sp: float, slc_sp: float
) -> np.ndarray:
    """
    Resample volume to isotropic 1 mm³ voxels using the minimum spacing as target.
    volume shape: (Z, Y, X)
    """
    spacings = np.array([slc_sp, row_sp, col_sp])
    if np.allclose(spacings, spacings[0], rtol=0.05):
        # Already close enough to isotropic — skip resampling
        return volume

    target = spacings.min()
    zoom_factors = spacings / target

    # Cap zoom to avoid huge upsampling that would make the app unusably slow
    zoom_factors = np.clip(zoom_factors, 0.25, 4.0)

    if np.allclose(zoom_factors, 1.0, rtol=0.02):
        return volume

    print(f"[loader] resampling with zoom {zoom_factors.round(3)}")
    resampled = ndimage_zoom(volume.astype(np.float32), zoom_factors, order=1)
    return resampled.astype(np.float32)


# ---------------------------------------------------------------------------
# DICOM folder / series loader
# ---------------------------------------------------------------------------


def _sort_dicom_files(paths: list[str]) -> list[str]:
    """Sort a list of DICOM paths by InstanceNumber, then filename."""
    tagged = []
    for p in paths:
        try:
            ds = pydicom.dcmread(p, stop_before_pixels=True)
            n = int(getattr(ds, "InstanceNumber", 0))
        except Exception:
            n = 0
        tagged.append((n, p))
    tagged.sort(key=lambda t: (t[0], t[1]))
    return [p for _, p in tagged]


def load_dicom_folder(folder_path: str, parent=None) -> np.ndarray | None:
    """
    Load all DICOM slices from *folder_path* into a resampled 3-D uint8 volume.
    """
    all_files = [
        os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(".dcm")
    ]
    if not all_files:
        QMessageBox.critical(parent, "Error", "No DICOM files found in the selected folder.")
        return None

    dicom_files = _sort_dicom_files(all_files)

    progress = QProgressDialog("Loading DICOM series…", "Cancel", 0, len(dicom_files), parent)
    progress.setWindowModality(Qt.WindowModal)
    progress.setMinimumDuration(0)

    slices = []
    datasets = []
    target_shape = None

    for i, filepath in enumerate(dicom_files):
        progress.setValue(i)
        if progress.wasCanceled():
            return None
        try:
            ds = pydicom.dcmread(filepath)
            arr = _pixel_array(ds)

            # Apply rescale
            if hasattr(ds, "RescaleSlope") and hasattr(ds, "RescaleIntercept"):
                arr = arr * float(ds.RescaleSlope) + float(ds.RescaleIntercept)

            # Establish target shape from first valid slice
            if target_shape is None:
                target_shape = arr.shape

            # Resize if this slice differs (rare but happens)
            if arr.shape != target_shape:
                from skimage.transform import resize as sk_resize

                arr = sk_resize(
                    arr,
                    target_shape,
                    order=1,
                    mode="edge",
                    anti_aliasing=False,
                    preserve_range=True,
                )

            slices.append(arr.astype(np.float32))
            datasets.append(ds)

        except Exception as exc:
            QMessageBox.warning(parent, "Warning", f"Skipping {os.path.basename(filepath)}:\n{exc}")

    progress.setValue(len(dicom_files))

    if not slices:
        QMessageBox.critical(parent, "Error", "No valid DICOM slices could be loaded.")
        return None

    volume = np.stack(slices, axis=0)  # (Z, Y, X)

    # Read spacing and resample to isotropic
    row_sp, col_sp = _read_pixel_spacing(datasets[0])
    slc_sp = _read_slice_spacing(datasets)
    print(f"[loader] folder spacing: row={row_sp} col={col_sp} slice={slc_sp}")

    volume = _resample_isotropic(volume, row_sp, col_sp, slc_sp)
    return _normalise_to_uint8(volume)


# ---------------------------------------------------------------------------
# Single DICOM file loader
# ---------------------------------------------------------------------------


def _find_series_siblings(seed_path: str) -> list[str]:
    """
    Return all .dcm files in the same folder that share the seed's
    SeriesInstanceUID, sorted by InstanceNumber.
    """
    folder = os.path.dirname(os.path.abspath(seed_path))
    candidates = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".dcm")]
    if not candidates:
        return [seed_path]

    try:
        seed_ds = pydicom.dcmread(seed_path, stop_before_pixels=True)
        series_uid = getattr(seed_ds, "SeriesInstanceUID", None)
    except Exception:
        return [seed_path]

    if series_uid is None:
        return _sort_dicom_files(candidates)

    matched = []
    for path in candidates:
        try:
            ds = pydicom.dcmread(path, stop_before_pixels=True)
            if getattr(ds, "SeriesInstanceUID", None) == series_uid:
                matched.append(path)
        except Exception:
            continue

    return _sort_dicom_files(matched) if matched else [seed_path]


def load_dicom_file(file_path: str, parent=None) -> np.ndarray | None:
    """
    Load a single DICOM file and return a 3-D uint8 volume.

    * Multi-frame (NumberOfFrames > 1): extracts all frames as slices.
    * Single-frame: auto-detects sibling files in the same folder that belong
      to the same series and loads them all.
    * Truly isolated single slice: returns a 3-copy volume so all views work.
    """
    try:
        ds = pydicom.dcmread(file_path)
        n_frames = int(getattr(ds, "NumberOfFrames", 1))

        # ── Multi-frame ───────────────────────────────────────────────────
        if n_frames > 1:
            raw = _pixel_array(ds)  # shape (F, H, W) or (H, W)
            if raw.ndim == 2:
                raw = raw[np.newaxis]

            if hasattr(ds, "RescaleSlope") and hasattr(ds, "RescaleIntercept"):
                raw = raw * float(ds.RescaleSlope) + float(ds.RescaleIntercept)

            volume = raw.astype(np.float32)  # (Z, Y, X)

            # Per-frame spacing
            row_sp, col_sp = _read_pixel_spacing(ds)
            slc_sp = abs(float(getattr(ds, "SliceThickness", 1.0) or 1.0))
            # SharedFunctionalGroupsSequence carries per-frame spacing in enhanced DICOMs
            sfgs = getattr(ds, "SharedFunctionalGroupsSequence", None)
            if sfgs:
                pm = getattr(sfgs[0], "PixelMeasuresSequence", None)
                if pm:
                    ps = getattr(pm[0], "PixelSpacing", None)
                    st = getattr(pm[0], "SliceThickness", None)
                    if ps:
                        row_sp, col_sp = float(ps[0]), float(ps[1])
                    if st:
                        slc_sp = abs(float(st))

            print(f"[loader] multi-frame spacing: row={row_sp} col={col_sp} slice={slc_sp}")
            volume = _resample_isotropic(volume, row_sp, col_sp, slc_sp)
            return _normalise_to_uint8(volume)

        # ── Single-frame: look for a series ──────────────────────────────
        siblings = _find_series_siblings(file_path)
        if len(siblings) > 1:
            return load_dicom_folder(os.path.dirname(os.path.abspath(file_path)), parent)

        # ── Truly isolated single slice ───────────────────────────────────
        arr = _pixel_array(ds)
        if hasattr(ds, "RescaleSlope") and hasattr(ds, "RescaleIntercept"):
            arr = arr * float(ds.RescaleSlope) + float(ds.RescaleIntercept)
        arr = _normalise_to_uint8(arr.astype(np.float32))
        return np.stack([arr] * 3, axis=0)

    except Exception as exc:
        QMessageBox.critical(parent, "Error", str(exc))
        return None


# ---------------------------------------------------------------------------
# NIfTI loader
# ---------------------------------------------------------------------------


def load_nifti_file(file_path: str) -> np.ndarray:
    """
    Load a NIfTI file and return a resampled (slices, rows, cols) uint8 volume.
    Reads voxel dimensions from the header and resamples to isotropic spacing.
    """
    nifti_img = nib.load(file_path)
    volume = nifti_img.get_fdata().astype(np.float32)

    # NIfTI voxel sizes: header.get_zooms() returns (col, row, slice) spacing
    zooms = nifti_img.header.get_zooms()[:3]
    col_sp, row_sp, slc_sp = float(zooms[0]), float(zooms[1]), float(zooms[2])
    print(f"[loader] NIfTI spacing: row={row_sp} col={col_sp} slice={slc_sp}")

    # NIfTI layout is (X, Y, Z) → transpose to (Z, Y, X) = (slices, rows, cols)
    volume = np.transpose(volume, (2, 1, 0))

    volume = _resample_isotropic(volume, row_sp, col_sp, slc_sp)
    return _normalise_to_uint8(volume)

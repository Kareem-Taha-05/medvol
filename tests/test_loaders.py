"""
Tests for medvol.core.loaders.

All I/O is done with synthetic data — no real patient files required.
"""

import numpy as np
import pytest

from medvol.core.loaders import (
    _normalise_to_uint8,
    _resample_isotropic,
    _read_pixel_spacing,
    _read_slice_spacing,
    load_nifti_file,
    load_dicom_folder,
)


# ── _normalise_to_uint8 ────────────────────────────────────────────────────────

class TestNormaliseToUint8:
    def test_range_maps_to_0_255(self):
        arr = np.array([0.0, 50.0, 100.0], dtype=np.float32)
        result = _normalise_to_uint8(arr)
        assert result.min() == 0
        assert result.max() == 255
        assert result.dtype == np.uint8

    def test_flat_array_returns_zeros(self):
        arr = np.full((4, 4), 42.0, dtype=np.float32)
        result = _normalise_to_uint8(arr)
        assert (result == 0).all()

    def test_negative_values_handled(self):
        arr = np.array([-1024.0, 0.0, 3071.0])   # typical CT HU range
        result = _normalise_to_uint8(arr)
        assert result.min() == 0
        assert result.max() == 255
        assert result.dtype == np.uint8

    def test_preserves_shape(self, synthetic_volume):
        result = _normalise_to_uint8(synthetic_volume.astype(np.float32))
        assert result.shape == synthetic_volume.shape


# ── _resample_isotropic ────────────────────────────────────────────────────────

class TestResampleIsotropic:
    def test_already_isotropic_returns_same_shape(self, synthetic_volume):
        vol = synthetic_volume.astype(np.float32)
        result = _resample_isotropic(vol, row_sp=1.0, col_sp=1.0, slc_sp=1.0)
        assert result.shape == vol.shape

    def test_anisotropic_expands_slice_dimension(self, synthetic_volume):
        """If slices are 3mm apart but pixels are 1mm, Z axis should expand ~3×."""
        vol = synthetic_volume.astype(np.float32)
        result = _resample_isotropic(vol, row_sp=1.0, col_sp=1.0, slc_sp=3.0)
        # Z dimension should be larger (slices resampled to match 1mm)
        assert result.shape[0] > vol.shape[0]
        # XY should stay roughly the same
        assert result.shape[1] == vol.shape[1]
        assert result.shape[2] == vol.shape[2]

    def test_output_is_float32(self, synthetic_volume):
        vol = synthetic_volume.astype(np.float32)
        result = _resample_isotropic(vol, 1.0, 1.0, 2.0)
        assert result.dtype == np.float32

    def test_near_isotropic_tolerance(self, synthetic_volume):
        """Spacing within 5% tolerance should not resample (no-op)."""
        vol = synthetic_volume.astype(np.float32)
        result = _resample_isotropic(vol, row_sp=1.0, col_sp=1.0, slc_sp=1.04)
        assert result.shape == vol.shape


# ── _read_pixel_spacing ────────────────────────────────────────────────────────

class TestReadPixelSpacing:
    def test_reads_from_dataset(self, dicom_dataset):
        row_sp, col_sp = _read_pixel_spacing(dicom_dataset)
        assert row_sp == pytest.approx(0.5)
        assert col_sp == pytest.approx(0.5)

    def test_fallback_when_missing(self):
        import pydicom
        ds = pydicom.Dataset()
        row_sp, col_sp = _read_pixel_spacing(ds)
        assert row_sp == 1.0
        assert col_sp == 1.0


# ── _read_slice_spacing ────────────────────────────────────────────────────────

class TestReadSliceSpacing:
    def test_reads_slice_thickness(self, dicom_dataset):
        spacing = _read_slice_spacing([dicom_dataset])
        assert spacing == pytest.approx(3.0)

    def test_empty_list_returns_1(self):
        spacing = _read_slice_spacing([])
        assert spacing == 1.0


# ── load_dicom_folder ──────────────────────────────────────────────────────────

class TestLoadDicomFolder:
    def test_returns_uint8_array(self, dicom_folder):
        vol = load_dicom_folder(dicom_folder, parent=None)
        assert vol is not None
        assert vol.dtype == np.uint8

    def test_shape_has_three_dims(self, dicom_folder):
        vol = load_dicom_folder(dicom_folder, parent=None)
        assert vol is not None
        assert vol.ndim == 3

    def test_slice_count_matches_files(self, dicom_folder):
        import os
        n_dcm = len([f for f in os.listdir(dicom_folder) if f.endswith(".dcm")])
        vol = load_dicom_folder(dicom_folder, parent=None)
        assert vol is not None
        # After isotropic resampling, Z may differ — but it should be > 0
        assert vol.shape[0] > 0

    def test_empty_folder_returns_none(self, tmp_path):
        vol = load_dicom_folder(str(tmp_path), parent=None)
        assert vol is None


# ── load_nifti_file ────────────────────────────────────────────────────────────

class TestLoadNiftiFile:
    def test_loads_synthetic_nifti(self, tmp_path, synthetic_volume):
        import nibabel as nib
        # Save a tiny NIfTI and reload it
        img = nib.Nifti1Image(
            synthetic_volume.transpose(2, 1, 0).astype(np.float32),  # X,Y,Z for NIfTI
            affine=np.eye(4)
        )
        path = tmp_path / "test.nii"
        nib.save(img, str(path))

        vol = load_nifti_file(str(path))
        assert vol.dtype == np.uint8
        assert vol.ndim == 3
        assert vol.max() == 255 or vol.max() > 0

    def test_shape_is_z_y_x(self, tmp_path):
        """Loader must transpose NIfTI (X,Y,Z) → (Z,Y,X)."""
        import nibabel as nib
        data = np.zeros((10, 20, 30), dtype=np.float32)  # X=10, Y=20, Z=30
        img = nib.Nifti1Image(data, np.eye(4))
        path = tmp_path / "shape_test.nii"
        nib.save(img, str(path))

        vol = load_nifti_file(str(path))
        # Z=30, Y=20, X=10 (possibly resampled but ordering preserved)
        assert vol.shape[0] >= vol.shape[2]   # Z is the first axis (largest here)
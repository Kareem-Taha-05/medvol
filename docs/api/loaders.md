# core.loaders

File I/O for all supported volume formats.

All public functions return a `numpy.ndarray` of shape `(Z, Y, X)` and dtype
`uint8`, with voxels resampled to isotropic spacing.

---

::: medvol.core.loaders
    options:
      members:
        - load_nifti_file
        - load_dicom_file
        - load_dicom_folder
      show_source: true

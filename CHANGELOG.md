# Changelog

All notable changes to MEDVOL are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Version numbers follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2024-01-XX

### Added
- **3D volume rendering** via VTK `vtkFixedPointVolumeRayCastMapper` with
  anatomically-correct transfer functions (air → fat → muscle → bone).
- **Multi-planar reconstruction** — linked axial, sagittal, and coronal
  views with real-time crosshair synchronisation on click-drag.
- **NIfTI support** — `.nii` and `.nii.gz` with header-aware isotropic resampling.
- **DICOM single-file loading** — auto-detects whether the file is a true
  multi-frame or a lone slice, and finds sibling slices by `SeriesInstanceUID`.
- **DICOM series loading** — folder ingestion sorted by `InstanceNumber`,
  with progress dialog and cancellation.
- **Multi-frame enhanced DICOM** — reads `SharedFunctionalGroupsSequence`
  for per-frame `PixelSpacing` and `SliceThickness`.
- **Isotropic resampling** — reads `PixelSpacing`, `SpacingBetweenSlices`,
  and `SliceThickness` from DICOM / NIfTI headers; resamples via
  `scipy.ndimage.zoom` so voxels are cubic before display.
- **Pydicom-native decompression** — JPEG, JPEG 2000, and RLE handled
  transparently via pydicom's backend chain (`python-gdcm` or `pylibjpeg`).
  No direct GDCM API calls — compatible with all Windows `python-gdcm` builds.
- **Per-pane zoom** — independent zoom per view; crosshair mode resets all panes.
- **Brightness / contrast sliders** — singularity-free algorithm; Matplotlib
  `vmin=0 vmax=255` pins colour scale so adjustments are never auto-normalised away.
- **Brutalist phosphor UI** — acid-green `#b8ff2e` on concrete `#252523`,
  zero rounded corners, three-point VTK lighting, `Arial Black` typography.
- **Installable package** — `pip install .` + `medvol` CLI entry point.

### Architecture
- `core/loaders.py` — all file I/O, spacing detection, resampling
- `core/volume_rendering.py` — full VTK pipeline
- `core/dependencies.py` — optional backend detection
- `ui/main_viewer.py` — Qt layout, events, mode control
- `ui/slice_canvas.py` — horizontal-strip Matplotlib canvas widget
- `utils/image_processing.py` — brightness/contrast

---

## [Unreleased]

### Planned
- Windowing presets: bone, lung, soft tissue, brain
- Measurement tools: distance, angle, ROI area
- DICOM metadata inspector panel
- Maximum Intensity Projection (MIP) mode
- Export slice or 3D render to PNG / TIFF
- Keyboard shortcuts for slice navigation

---

[1.0.0]: https://github.com/Kareem-Taha-05/medvol/releases/tag/v1.0.0
[Unreleased]: https://github.com/Kareem-Taha-05/medvol/compare/v1.0.0...HEAD
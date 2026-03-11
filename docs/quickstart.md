# Quick Start

## Launch the application

```bash
medvol
```

---

## Load a NIfTI file

1. Click **NIFTI FILE** in the command bar
2. Select a `.nii` or `.nii.gz` file
3. All four panels populate immediately — three 2D slice views and the 3D volume

!!! tip "No NIfTI file?"
    Download a free brain dataset from [OpenNeuro](https://openneuro.org) or the
    [IXI Dataset](https://brain-development.org/ixi-dataset/).
    Any T1-weighted brain MRI works well.

---

## Load a DICOM series

1. Click **DICOM SERIES**
2. Select the **folder** containing the `.dcm` files
3. MEDVOL reads all files, sorts by `InstanceNumber`, and resamples to isotropic voxels

---

## Load a single DICOM file

1. Click **DICOM FILE**
2. Select any `.dcm` file
3. MEDVOL checks whether it is:
   - A **multi-frame** file → extracts all frames
   - A **single-frame** file → searches the folder for sibling slices with the same `SeriesInstanceUID`
   - A **truly isolated** slice → displays it as a 3-slice volume so all views work

---

## Navigate slices

**Click and drag** inside any slice view to move the crosshair.
All three planes update in real-time to show the corresponding slice.

Each plane also has a **slider** — drag it or scroll to step through slices.

---

## Adjust brightness and contrast

Use the **BRIGHTNESS** and **CONTRAST** sliders in the bottom control bar.

- Brightness: uniform ±additive offset over the full range
- Contrast: scale around midpoint — centre is unchanged, extremes clip to black/white

Both sliders return to zero on double-click (standard Qt behaviour).

---

## Zoom

1. Click the **ZOOM** button in the command bar — it turns green (active)
2. Click **ZOOM +** then click on a slice view to zoom in on that point
3. Click **ZOOM −** then click to zoom out
4. Click **CURSOR** to return to crosshair navigation — zoom resets

---

## Keyboard reference

| Key | Action |
|-----|--------|
| `Ctrl+Q` | Quit |

More keyboard shortcuts are planned — see the [Roadmap](../changelog.md).

---

## Programmatic use

```python
from medvol.core.loaders import load_nifti_file, load_dicom_folder

# Load a NIfTI volume
volume = load_nifti_file("brain.nii.gz")
print(volume.shape, volume.dtype)   # (182, 218, 182)  uint8

# Load a DICOM series
volume = load_dicom_folder("/path/to/CT/")
print(volume.shape)   # (N, rows, cols)  uint8

# Brightness/contrast adjustment
from medvol.utils.image_processing import adjust_brightness_contrast
import numpy as np

axial_slice = volume[volume.shape[0] // 2]
adjusted = adjust_brightness_contrast(axial_slice, brightness=20, contrast=40)
```

# MEDVOL

**Open-source 3D medical image viewer. DICOM & NIfTI. Zero configuration.**

---

<div style="text-align:center; margin: 2rem 0;">
  <img src="assets/demo/demo.gif" width="720" alt="MEDVOL demo"/>
</div>

---

## What is MEDVOL?

MEDVOL is a desktop application for visualising 3D medical imaging data.
It opens DICOM and NIfTI volumes, shows them as linked axial/sagittal/coronal
slice views, and renders the full volume in 3D using VTK ray-casting.

It was built to be fast, correct, and visually distinct from every other
medical viewer — no clinical bloat, no proprietary file format lock-in,
no broken aspect ratios.

---

## At a Glance

| Feature | Detail |
|---------|--------|
| **3D rendering** | VTK `vtkFixedPointVolumeRayCastMapper` with anatomic transfer functions |
| **Multi-planar views** | Axial, sagittal, coronal — linked crosshair sync on click-drag |
| **Voxel spacing** | Reads `PixelSpacing` + `SliceThickness` from DICOM / NIfTI headers |
| **Isotropic resampling** | `scipy.ndimage.zoom` to cubic voxels before display |
| **DICOM formats** | Single file, multi-frame enhanced, folder series |
| **DICOM compression** | JPEG, JPEG 2000, RLE (via `pydicom` backend chain) |
| **NIfTI** | `.nii` and `.nii.gz`, NIfTI-1 and NIfTI-2 |
| **Platform** | Windows, macOS, Linux |

---

## Quick Install

```bash
git clone https://github.com/Kareem-Taha-05/medvol
cd medvol
pip install .
medvol
```

→ See [Installation](installation.md) for platform-specific notes and
compression backend setup.

---

## Design Philosophy

MEDVOL makes three deliberate choices that most medical viewers don't:

**1. Isotropic resampling is not optional.**
CT scans typically have 0.5mm in-plane pixels but 3mm slice spacing.
Every viewer that ignores this makes bones look like pancakes.
MEDVOL reads the actual spacing metadata and resamples before display.

**2. Decompression should be invisible.**
The DICOM standard allows JPEG, JPEG 2000, and RLE pixel encoding.
MEDVOL delegates decompression to pydicom's backend chain — if the right
library is installed, compressed files open without any user intervention.

**3. The 3D view is the centrepiece.**
Most viewers treat 3D rendering as an afterthought tucked in a corner.
MEDVOL puts the volume render on the left at 60% of the screen width —
because that's the most impressive thing the application does.

---

## Screenshots

<table>
<tr>
<td><img src="assets/demo/screenshot_main.png" alt="Full window"/></td>
<td><img src="assets/demo/screenshot_3d.png" alt="3D render"/></td>
</tr>
<tr>
<td align="center"><em>Full window — brutalist phosphor UI</em></td>
<td align="center"><em>3D ray-cast render with three-point lighting</em></td>
</tr>
</table>

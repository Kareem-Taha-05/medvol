---
name: Bug Report
about: Something is broken — help us fix it
title: "[BUG] "
labels: bug
assignees: ""
---

## What happened?

<!-- Describe the bug clearly. What did you expect? What did you get instead? -->

## Steps to reproduce

1. Opened the app with `medvol`
2. Clicked **DICOM FILE** / **DICOM SERIES** / **NIFTI FILE**
3. Selected: `<describe file type and rough size>`
4. Saw: `<error message or wrong behaviour>`

## Error output

<!-- Paste the full terminal output / traceback here -->

```
paste traceback here
```

## Environment

| Field | Value |
|-------|-------|
| OS | <!-- e.g. Windows 11, Ubuntu 22.04, macOS 14 Sonoma --> |
| Python | <!-- python --version --> |
| MEDVOL | <!-- pip show medvol | grep Version --> |
| VTK | <!-- pip show vtk | grep Version --> |
| PyQt5 | <!-- pip show PyQt5 | grep Version --> |
| Installed extras | <!-- [compress] / [dev] / none --> |

## File details

- **Format**: DICOM single file / DICOM multi-frame / DICOM series folder / NIfTI
- **Compression** (DICOM only): Uncompressed / JPEG / JPEG 2000 / RLE / Unknown
- **Modality** (if known): CT / MRI / PET / Other

> ⚠️ Do not attach real patient files. If you need to share a file to reproduce
> the bug, please use a synthetic dataset or strip all identifying metadata first.
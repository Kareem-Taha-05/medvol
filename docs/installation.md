# Installation

## Requirements

- Python **3.10 or later**
- A display (MEDVOL is a desktop GUI application — it cannot run headlessly)

---

## Standard Install

```bash
git clone https://github.com/Kareem-Taha-05/medvol
cd medvol
pip install .
```

Launch:

```bash
medvol
```

---

## With DICOM Compression Support

Most DICOM files from clinical scanners are uncompressed and work out of the box.
If your files use JPEG, JPEG 2000, or RLE transfer syntaxes, install the
compression extras:

```bash
pip install ".[compress]"
```

This installs:

| Package | Handles |
|---------|---------|
| `pylibjpeg` + `pylibjpeg-libjpeg` | JPEG baseline / JPEG-LS (1.2.840.10008.1.2.4.50/51) |
| `python-gdcm` | JPEG 2000 (1.2.840.10008.1.2.4.90/91) and RLE (1.2.840.10008.1.2.5) |

If a file fails to open with a "Cannot decode pixel data" error, installing
the above will almost always fix it.

---

## Platform Notes

=== "Windows"

    ```bash
    pip install .
    # or with compression:
    pip install ".[compress]"
    ```

    `python-gdcm` on Windows ships with its own DLLs — no external install needed.
    If the VTK wheel fails, check that you are on Python 3.10–3.12 (VTK wheels
    are not published for every minor version).

=== "macOS (Apple Silicon)"

    VTK's pip wheel may fail on arm64. If it does:

    ```bash
    brew install vtk
    pip install PyQt5 pydicom nibabel scipy scikit-image matplotlib
    pip install --no-deps .
    medvol
    ```

=== "Linux"

    VTK requires `libGL`. If you see an OpenGL error at startup:

    ```bash
    sudo apt install libgl1-mesa-glx libglib2.0-0
    pip install .
    medvol
    ```

    On headless servers, add a virtual framebuffer:

    ```bash
    sudo apt install xvfb
    Xvfb :99 -screen 0 1920x1080x24 &
    DISPLAY=:99 medvol
    ```

---

## Virtual Environment (Recommended)

```bash
git clone https://github.com/Kareem-Taha-05/medvol
cd medvol
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install .
medvol
```

---

## Development Install

If you want to modify the code and see changes without reinstalling:

```bash
pip install -e ".[dev]"
pre-commit install    # optional: auto-format/lint on every commit
```

---

## Verifying the Install

```bash
python -c "import medvol; print(medvol.__version__)"
# Expected output: 1.0.0
```
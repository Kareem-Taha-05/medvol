# Contributing to MEDVOL

Thank you for your interest in contributing. MEDVOL is a focused codebase —
each module has one clear responsibility, so it's straightforward to find
where a change belongs.

---

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Code Standards](#code-standards)
- [Running Tests](#running-tests)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Adding File Format Support](#adding-file-format-support)
- [Reporting Bugs](#reporting-bugs)

---

## Development Setup

```bash
# 1. Fork and clone
git clone https://github.com/Kareem-Taha-05/medvol
cd medvol

# 2. Create a virtual environment (Python 3.10+)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install in editable mode with dev dependencies
pip install -e ".[dev]"

# 4. Install pre-commit hooks (runs Black + Ruff + Mypy on every commit)
pre-commit install

# 5. Run the app to verify your setup
medvol
```

### Optional: DICOM compression backends

If you're working on DICOM loading and need to test compressed files:

```bash
pip install ".[compress]"
# installs: pylibjpeg  pylibjpeg-libjpeg  python-gdcm
```

---

## Project Structure

```
medvol/
├── core/
│   ├── loaders.py           ← ALL file I/O lives here. Add new formats here.
│   ├── volume_rendering.py  ← VTK pipeline only. No Qt, no numpy slicing.
│   ├── dependencies.py      ← Detection of optional backends (gdcm, pylibjpeg).
│   └── constants.py         ← UI palette, mode strings, zoom factors.
├── ui/
│   ├── main_viewer.py       ← Qt layout, event routing, mode control.
│   └── slice_canvas.py      ← The horizontal-strip Matplotlib widget.
└── utils/
    └── image_processing.py  ← Pure numpy transforms. No Qt, no VTK.
```

**Hard boundaries:**
- `utils/image_processing.py` must never import Qt or VTK
- `core/volume_rendering.py` must never import Qt widgets (only `QMessageBox` for errors)
- `core/loaders.py` returns plain `numpy.ndarray` — no UI state

---

## Code Standards

### Formatting

```bash
black medvol/          # auto-formats code (line length 100)
ruff check medvol/     # linting + import order
```

Both run automatically on commit via pre-commit hooks. If a commit is
rejected, just run the commands above and commit again.

### Type hints

All new functions must have type hints:

```python
# Good
def load_nifti_file(file_path: str) -> np.ndarray:

# Bad
def load_nifti_file(file_path):
```

### Docstrings

Use the existing style (Google-style, no Sphinx directives):

```python
def adjust_brightness_contrast(image: np.ndarray, brightness: int, contrast: int) -> np.ndarray:
    """
    Apply brightness and contrast to a uint8 image.

    Args:
        image:      2-D numpy array, any numeric dtype.
        brightness: Integer in [-255, 255]. 0 = no change.
        contrast:   Integer in [-255, 255]. 0 = no change.

    Returns:
        Adjusted image as uint8, values clipped to [0, 255].
    """
```

### Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add windowing preset for lung CT
fix: correct coronal crosshair inversion when clicking sagittal
docs: add JPEG 2000 decompression notes to CONTRIBUTING
refactor: extract _sort_dicom_files from load_dicom_folder
test: add fixture for multi-frame enhanced DICOM
```

---

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=medvol --cov-report=term-missing

# One file
pytest tests/test_loaders.py -v
```

The `tests/fixtures/sample.nii.gz` file is a tiny synthetic NIfTI volume
(16×16×16 voxels) — no patient data. Tests that need a DICOM file generate
one programmatically via pydicom's `Dataset` API to avoid distributing
real medical files.

---

## Submitting a Pull Request

1. Create a branch from `main`: `git checkout -b feat/your-feature-name`
2. Make your changes. Keep each PR focused on one thing.
3. Add or update tests if you changed a loader or utility function.
4. Run `black medvol/ && ruff check medvol/` before pushing.
5. Open a PR against `main`. Fill in the PR template.
6. A maintainer will review within a few days.

**PRs that will be merged quickly:**
- Bug fixes with a test that reproduces the bug
- New file format support following the existing loader pattern
- Documentation improvements
- Performance improvements to the loader or resampling pipeline

**PRs that need discussion first** (open an issue before starting):
- Changes to the VTK transfer functions
- Changes to the UI layout or colour palette
- New UI panels or controls

---

## Adding File Format Support

All loaders live in `medvol/core/loaders.py`. A new format should:

1. Return a `numpy.ndarray` of shape `(Z, Y, X)` and dtype `uint8`
2. Call `_resample_isotropic()` if the source format carries voxel spacing
3. Call `_normalise_to_uint8()` as the final step
4. Handle errors by raising a descriptive `Exception` (the caller shows it in a `QMessageBox`)

Example skeleton:

```python
def load_myformat_file(file_path: str) -> np.ndarray:
    """
    Load a .xyz file and return a (Z, Y, X) uint8 volume.

    Args:
        file_path: Path to a .xyz file.

    Returns:
        3-D uint8 numpy array.
    """
    import mylib
    data   = mylib.load(file_path)
    volume = np.transpose(data.array, (2, 1, 0))   # adjust axis order as needed

    row_sp = data.spacing[0]
    col_sp = data.spacing[1]
    slc_sp = data.spacing[2]
    volume = _resample_isotropic(volume.astype(np.float32), row_sp, col_sp, slc_sp)
    return _normalise_to_uint8(volume)
```

Then wire it up in `ui/main_viewer.py` — add an upload button in
`_build_command_bar()` and a handler method following the same pattern as
`upload_nifti_folder()`.

---

## Reporting Bugs

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).

Please include:
- Your OS and Python version (`python --version`)
- How you installed (`pip install .` / `pip install -r requirements.txt`)
- The exact file type you were loading (DICOM single / series / multi-frame / NIfTI)
- Full error traceback from the terminal

**No patient data in issues.** If you need to share a file to reproduce
a bug, use a synthetic test file or redact all metadata.
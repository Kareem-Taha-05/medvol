"""
Load a DICOM series from a folder and inspect it.

Usage:
    python examples/load_dicom_series.py /path/to/dicom/folder/

Prints volume info — no display required.
Useful for verifying that a DICOM series loads correctly before opening the GUI.
"""

import sys
import os
import numpy as np
from medvol.core.loaders import load_dicom_folder


def main():
    if len(sys.argv) < 2:
        print("Usage: python load_dicom_series.py <folder_path>")
        sys.exit(1)

    folder = sys.argv[1]

    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a directory")
        sys.exit(1)

    dcm_files = [f for f in os.listdir(folder) if f.lower().endswith(".dcm")]
    print(f"Found {len(dcm_files)} DICOM file(s) in: {folder}")

    if not dcm_files:
        print("No .dcm files found.")
        sys.exit(1)

    # Peek at the first file's metadata
    import pydicom
    try:
        first = pydicom.dcmread(os.path.join(folder, sorted(dcm_files)[0]),
                                stop_before_pixels=True)
        print(f"\nSeries metadata (from first file):")
        print(f"  Modality:           {getattr(first, 'Modality', 'Unknown')}")
        print(f"  SeriesDescription:  {getattr(first, 'SeriesDescription', 'N/A')}")
        print(f"  Rows × Cols:        {getattr(first, 'Rows', '?')} × {getattr(first, 'Columns', '?')}")
        print(f"  PixelSpacing:       {getattr(first, 'PixelSpacing', 'N/A')} mm")
        print(f"  SliceThickness:     {getattr(first, 'SliceThickness', 'N/A')} mm")
        ts = getattr(first.file_meta, 'TransferSyntaxUID', 'N/A')
        print(f"  TransferSyntax:     {ts}")
    except Exception as e:
        print(f"Could not read metadata: {e}")

    print("\nLoading volume (this resamples to isotropic voxels)...")
    volume = load_dicom_folder(folder, parent=None)

    if volume is None:
        print("Load failed. See error above.")
        sys.exit(1)

    print(f"\nVolume loaded successfully")
    print(f"  Shape:   {volume.shape}  (Z × Y × X)")
    print(f"  Dtype:   {volume.dtype}")
    print(f"  Range:   [{volume.min()}, {volume.max()}]")
    print(f"  Memory:  {volume.nbytes / 1e6:.1f} MB")

    print("\nReady — launch the viewer with:  medvol")


if __name__ == "__main__":
    main()
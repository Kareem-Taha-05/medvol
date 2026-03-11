"""
Load a NIfTI volume programmatically and inspect it.

Usage:
    python examples/load_nifti.py path/to/brain.nii.gz

No display required — this runs headlessly and prints volume info.
"""

import sys
import numpy as np
from medvol.core.loaders import load_nifti_file


def main():
    if len(sys.argv) < 2:
        print("Usage: python load_nifti.py <path_to_file.nii.gz>")
        sys.exit(1)

    path = sys.argv[1]
    print(f"Loading: {path}")

    volume = load_nifti_file(path)

    print(f"\nVolume loaded successfully")
    print(f"  Shape:  {volume.shape}  (Z × Y × X)")
    print(f"  Dtype:  {volume.dtype}")
    print(f"  Min:    {volume.min()}")
    print(f"  Max:    {volume.max()}")
    print(f"  Mean:   {volume.mean():.1f}")

    # Show a text histogram of the intensity distribution
    print("\n  Intensity histogram:")
    bins = np.linspace(0, 256, 9, dtype=int)
    for lo, hi in zip(bins[:-1], bins[1:]):
        count = ((volume >= lo) & (volume < hi)).sum()
        bar_len = int(count / volume.size * 60)
        print(f"  {lo:3d}–{hi:3d}  {'█' * bar_len} {count:,}")

    # Show the centre axial slice as ASCII art (very rough)
    print(f"\n  Centre axial slice (ASCII, {volume.shape[2]}×{volume.shape[1]} → 60×20):")
    axial = volume[volume.shape[0] // 2]
    from skimage.transform import resize
    thumb = resize(axial, (20, 60), anti_aliasing=True, preserve_range=True)
    chars = " .:-=+*#%@"
    for row in thumb:
        print("  " + "".join(chars[int(v / 256 * (len(chars) - 1))] for v in row))


if __name__ == "__main__":
    main()
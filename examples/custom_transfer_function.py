"""
Custom VTK transfer function example.

Shows how to swap the default tissue transfer function for specialised presets
(lung window, bone window, soft-tissue MIP style) by calling render_volume()
with a patched renderer.

Usage:
    python examples/custom_transfer_function.py brain.nii.gz
    # then interact with the VTK window — close it to exit

This demonstrates the programmatic API for embedding MEDVOL's volume renderer
in your own PyQt5 application.
"""

import sys
import numpy as np
import vtk

from PyQt5.QtWidgets import QApplication, QMainWindow
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from medvol.core.loaders import load_nifti_file


# ── Transfer function presets ─────────────────────────────────────────────────

def bone_window():
    """High contrast: air and soft tissue transparent, bone bright white."""
    opacity = vtk.vtkPiecewiseFunction()
    opacity.AddPoint(0,   0.00)
    opacity.AddPoint(150, 0.00)
    opacity.AddPoint(180, 0.60)
    opacity.AddPoint(220, 0.85)
    opacity.AddPoint(255, 0.95)

    colour = vtk.vtkColorTransferFunction()
    colour.AddRGBPoint(0,   0.00, 0.00, 0.00)
    colour.AddRGBPoint(150, 0.00, 0.00, 0.00)
    colour.AddRGBPoint(200, 0.90, 0.85, 0.75)
    colour.AddRGBPoint(255, 1.00, 1.00, 1.00)
    return opacity, colour


def soft_tissue_window():
    """Emphasises mid-range densities (muscle, organs). Used in abdomen CT."""
    opacity = vtk.vtkPiecewiseFunction()
    opacity.AddPoint(0,   0.00)
    opacity.AddPoint(30,  0.00)
    opacity.AddPoint(60,  0.20)
    opacity.AddPoint(120, 0.45)
    opacity.AddPoint(160, 0.55)
    opacity.AddPoint(200, 0.20)
    opacity.AddPoint(255, 0.05)

    colour = vtk.vtkColorTransferFunction()
    colour.AddRGBPoint(0,   0.00, 0.00, 0.00)
    colour.AddRGBPoint(60,  0.55, 0.25, 0.15)
    colour.AddRGBPoint(100, 0.75, 0.38, 0.25)
    colour.AddRGBPoint(140, 0.85, 0.55, 0.40)
    colour.AddRGBPoint(180, 0.80, 0.70, 0.60)
    colour.AddRGBPoint(255, 0.90, 0.85, 0.80)
    return opacity, colour


def mip_style():
    """Maximum-Intensity-Projection style: bright = opaque, dark = invisible."""
    opacity = vtk.vtkPiecewiseFunction()
    opacity.AddPoint(0,   0.00)
    opacity.AddPoint(50,  0.00)
    opacity.AddPoint(100, 0.50)
    opacity.AddPoint(180, 0.80)
    opacity.AddPoint(255, 1.00)

    colour = vtk.vtkColorTransferFunction()
    colour.AddRGBPoint(0,   0.00, 0.00, 0.00)
    colour.AddRGBPoint(100, 0.00, 0.80, 1.00)   # cyan for mid
    colour.AddRGBPoint(200, 1.00, 1.00, 0.80)   # warm white for bright
    colour.AddRGBPoint(255, 1.00, 1.00, 1.00)
    return opacity, colour


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python custom_transfer_function.py <file.nii.gz>")
        sys.exit(1)

    path   = sys.argv[1]
    preset = sys.argv[2] if len(sys.argv) > 2 else "bone"

    presets = {
        "bone":   bone_window,
        "soft":   soft_tissue_window,
        "mip":    mip_style,
    }
    if preset not in presets:
        print(f"Unknown preset '{preset}'. Choose from: {', '.join(presets)}")
        sys.exit(1)

    print(f"Loading {path} with preset: {preset}")
    volume = load_nifti_file(path)
    print(f"Volume shape: {volume.shape}")

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle(f"MEDVOL — Custom TF: {preset}")
    window.resize(800, 800)

    vtk_widget = QVTKRenderWindowInteractor(window)
    window.setCentralWidget(vtk_widget)

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.05, 0.05, 0.05)
    vtk_widget.GetRenderWindow().AddRenderer(renderer)
    interactor = vtk_widget.GetRenderWindow().GetInteractor()

    # Build VTK pipeline manually with custom TF
    volume_data = np.ascontiguousarray(volume.astype(np.uint8))
    z, y, x = volume_data.shape

    importer = vtk.vtkImageImport()
    importer.CopyImportVoidPointer(volume_data.tobytes(), volume_data.nbytes)
    importer.SetDataScalarTypeToUnsignedChar()
    importer.SetNumberOfScalarComponents(1)
    importer.SetDataExtent(0, x-1, 0, y-1, 0, z-1)
    importer.SetWholeExtent(0, x-1, 0, y-1, 0, z-1)
    importer.Update()
    renderer._data_importer = importer  # prevent GC

    opacity_tf, colour_tf = presets[preset]()

    vol_prop = vtk.vtkVolumeProperty()
    vol_prop.SetColor(colour_tf)
    vol_prop.SetScalarOpacity(opacity_tf)
    vol_prop.SetInterpolationTypeToLinear()
    vol_prop.ShadeOn()
    vol_prop.SetAmbient(0.20)
    vol_prop.SetDiffuse(0.85)
    vol_prop.SetSpecular(0.15)

    mapper = vtk.vtkFixedPointVolumeRayCastMapper()
    mapper.SetInputConnection(importer.GetOutputPort())

    actor = vtk.vtkVolume()
    actor.SetMapper(mapper)
    actor.SetProperty(vol_prop)

    renderer.AddVolume(actor)
    renderer.ResetCamera()
    renderer.GetActiveCamera().Elevation(20)
    renderer.GetActiveCamera().Azimuth(45)

    window.show()
    interactor.Initialize()
    vtk_widget.GetRenderWindow().Render()

    print(f"\nPresets available: {', '.join(presets.keys())}")
    print("Run with:  python custom_transfer_function.py brain.nii.gz soft")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
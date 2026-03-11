"""
VTK-based 3-D volume rendering.

Key design notes
----------------
* vtkImageImport must stay alive for the lifetime of the render — VTK's
  pipeline is lazy and pulls data at Render() time, not when the pipeline is
  built.  We therefore store it as renderer._data_importer so Python never
  garbage-collects it.

* vtkFixedPointVolumeRayCastMapper is used as the primary mapper because it
  works reliably on all hardware inside a Qt widget (the GPU mapper requires
  a fully initialised OpenGL context that isn't guaranteed at startup).

Transfer-function design
------------------------
Input data is uint8 [0, 255] normalised from the original DICOM/NIfTI values.
We split the range into four bands and assign distinct colours + solid opacity
so the result looks like a real CT render rather than a translucent red blob:

  0  –  15   background / air          → fully transparent
  15 –  60   fat / very soft tissue    → low opacity, dark brown
  60 – 160   soft tissue / muscle      → medium opacity, red-flesh tone
  160– 220   dense tissue / cartilage  → higher opacity, pink-bone
  220– 255   cortical bone             → nearly opaque, white-ivory
"""

import numpy as np
import vtk
from PyQt5.QtWidgets import QMessageBox

# ── Transfer functions ────────────────────────────────────────────────────────


def _build_opacity_tf() -> vtk.vtkPiecewiseFunction:
    tf = vtk.vtkPiecewiseFunction()
    # Background — completely transparent
    tf.AddPoint(0, 0.00)
    tf.AddPoint(15, 0.00)
    # Fat / very soft tissue — just barely visible
    tf.AddPoint(30, 0.08)
    tf.AddPoint(60, 0.15)
    # Soft tissue / muscle — clearly visible but still translucent
    tf.AddPoint(100, 0.35)
    tf.AddPoint(160, 0.50)
    # Dense tissue / cartilage
    tf.AddPoint(190, 0.65)
    tf.AddPoint(220, 0.78)
    # Cortical bone — nearly solid
    tf.AddPoint(240, 0.88)
    tf.AddPoint(255, 0.95)
    return tf


def _build_colour_tf() -> vtk.vtkColorTransferFunction:
    tf = vtk.vtkColorTransferFunction()
    # Background
    tf.AddRGBPoint(0, 0.00, 0.00, 0.00)
    # Fat / very soft tissue — dark ochre/brown
    tf.AddRGBPoint(20, 0.30, 0.18, 0.10)
    tf.AddRGBPoint(50, 0.55, 0.30, 0.18)
    # Muscle / soft tissue — distinctly red-flesh, not pinkish
    tf.AddRGBPoint(80, 0.78, 0.28, 0.20)
    tf.AddRGBPoint(130, 0.85, 0.42, 0.30)
    # Dense soft tissue transitioning to bone — warm tan
    tf.AddRGBPoint(165, 0.88, 0.68, 0.50)
    tf.AddRGBPoint(195, 0.92, 0.82, 0.66)
    # Spongy bone — light ivory
    tf.AddRGBPoint(220, 0.96, 0.92, 0.82)
    # Cortical bone — bright white
    tf.AddRGBPoint(255, 1.00, 1.00, 1.00)
    return tf


# ── Main pipeline ─────────────────────────────────────────────────────────────


def render_volume(
    image_volume: np.ndarray,
    renderer: vtk.vtkRenderer,
    render_window: vtk.vtkRenderWindow,
    parent=None,
) -> None:
    """
    Build the full VTK volume-rendering pipeline and display it.

    The vtkImageImport object is stored as renderer._data_importer to
    prevent Python from garbage-collecting it before VTK pulls the data.
    """
    if image_volume is None:
        return

    try:
        volume_data = np.ascontiguousarray(image_volume.astype(np.uint8))
        z, y, x = volume_data.shape

        print(
            f"[vtk] volume shape={volume_data.shape}  "
            f"min={volume_data.min()}  max={volume_data.max()}"
        )

        # ── 1. Import numpy array into VTK ────────────────────────────────
        importer = vtk.vtkImageImport()
        data_str = volume_data.tobytes()
        importer.CopyImportVoidPointer(data_str, len(data_str))
        importer.SetDataScalarTypeToUnsignedChar()
        importer.SetNumberOfScalarComponents(1)
        importer.SetDataExtent(0, x - 1, 0, y - 1, 0, z - 1)
        importer.SetWholeExtent(0, x - 1, 0, y - 1, 0, z - 1)
        importer.SetDataSpacing(1.0, 1.0, 1.0)
        importer.Update()

        # Pin to renderer so Python never GC's it before Render() fires
        renderer._data_importer = importer

        # ── 2. Transfer functions ─────────────────────────────────────────
        opacity_tf = _build_opacity_tf()
        colour_tf = _build_colour_tf()

        # ── 3. Volume property ────────────────────────────────────────────
        vol_prop = vtk.vtkVolumeProperty()
        vol_prop.SetColor(colour_tf)
        vol_prop.SetScalarOpacity(opacity_tf)
        vol_prop.SetInterpolationTypeToLinear()
        vol_prop.ShadeOn()
        vol_prop.SetAmbient(0.20)
        vol_prop.SetDiffuse(0.85)
        vol_prop.SetSpecular(0.20)
        vol_prop.SetSpecularPower(10)

        # ── 4. Mapper ─────────────────────────────────────────────────────
        mapper = vtk.vtkFixedPointVolumeRayCastMapper()
        mapper.SetInputConnection(importer.GetOutputPort())

        # ── 5. Volume actor ───────────────────────────────────────────────
        volume_actor = vtk.vtkVolume()
        volume_actor.SetMapper(mapper)
        volume_actor.SetProperty(vol_prop)

        # ── 6. Lighting ───────────────────────────────────────────────────
        renderer.RemoveAllViewProps()
        renderer.RemoveAllLights()
        renderer.AddVolume(volume_actor)
        renderer.SetBackground(0.05, 0.05, 0.12)

        # Three-point lighting for depth and surface definition
        key = vtk.vtkLight()
        key.SetLightTypeToCameraLight()
        key.SetPosition(1.0, 1.0, 1.0)
        key.SetFocalPoint(0.0, 0.0, 0.0)
        key.SetColor(1.00, 0.95, 0.88)  # warm white
        key.SetIntensity(1.0)
        renderer.AddLight(key)

        fill = vtk.vtkLight()
        fill.SetLightTypeToCameraLight()
        fill.SetPosition(-1.0, -0.5, -0.5)
        fill.SetFocalPoint(0.0, 0.0, 0.0)
        fill.SetColor(0.55, 0.65, 0.80)  # cool blue-white
        fill.SetIntensity(0.40)
        renderer.AddLight(fill)

        rim = vtk.vtkLight()
        rim.SetLightTypeToSceneLight()
        rim.SetPosition(0.0, -2.0, -1.0)
        rim.SetFocalPoint(0.0, 0.0, 0.0)
        rim.SetColor(0.80, 0.80, 0.80)
        rim.SetIntensity(0.25)
        renderer.AddLight(rim)

        # ── 7. Camera ─────────────────────────────────────────────────────
        renderer.ResetCamera()
        cam = renderer.GetActiveCamera()
        cam.Elevation(20)
        cam.Azimuth(45)
        renderer.ResetCameraClippingRange()

        # ── 8. Render ─────────────────────────────────────────────────────
        render_window.Render()
        print("[vtk] Render() completed")

    except Exception as exc:
        print(f"[vtk] ERROR: {exc}")
        import traceback

        traceback.print_exc()
        if parent:
            QMessageBox.critical(parent, "3D Rendering Error", str(exc))

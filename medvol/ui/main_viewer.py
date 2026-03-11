"""
MedicalImageViewer – brutalist phosphor layout.

┌─────────────────────────────────────────────────────────────────────────┐
│  MEDVOL ·  [ DICOM FILE ]  [ SERIES ]  [ NIFTI ]  │ CURSOR │  +  │  −  │  ← command bar (46px)
├────────────────────────────────────────┬────────────────────────────────┤
│                                        │ ┌────────────────────────────┐ │
│                                        │ │ AXIAL    [canvas] 042 ───● │ │
│          3 D   V O L U M E             │ ├────────────────────────────┤ │
│         (VTK – fills left column)      │ │ SAGITTAL [canvas] 071 ───● │ │
│                                        │ ├────────────────────────────┤ │
│                                        │ │ CORONAL  [canvas] 055 ───● │ │
│                                        │ └────────────────────────────┘ │
├────────────────────────────────────────┴────────────────────────────────┤
│  BRIGHTNESS ──────────●────────  +42   │  CONTRAST ──●──────────  −018  │  ← adj bar (38px)
└─────────────────────────────────────────────────────────────────────────┘
"""

import numpy as np
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QSizePolicy,
    QFileDialog, QMessageBox, QFrame,
)

from medvol.core.constants         import CURSOR_MODE, ZOOM_MODE, ZOOM_IN_FACTOR, ZOOM_OUT_FACTOR, APP_STYLESHEET
from medvol.core.loaders           import load_dicom_file, load_dicom_folder, load_nifti_file
from medvol.core.volume_rendering  import render_volume
from medvol.utils.image_processing import adjust_brightness_contrast
from medvol.ui.slice_canvas        import SliceCanvas


class MedicalImageViewer(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MEDVOL — 3D Medical Imaging")
        self.setGeometry(60, 40, 1760, 980)
        self.setStyleSheet(APP_STYLESHEET)

        # ── State ──────────────────────────────────────────────────────────
        self.image_volume:       np.ndarray | None = None
        self.axial_index:        int = 0
        self.sagittal_index:     int = 0
        self.coronal_index:      int = 0
        self.axial_crosshair:    tuple | None = None
        self.sagittal_crosshair: tuple | None = None
        self.coronal_crosshair:  tuple | None = None

        self.current_mode     = CURSOR_MODE
        self.zoom_mode        = False
        self.zoom_in_mode     = False
        self.zoom_out_mode    = False
        self.is_mouse_pressed = False
        self._zoom_limits:    dict = {}
        self._vtk_initialized = False

        self._build_ui()
        self._build_cursors()
        self.set_cursor_mode()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_command_bar())
        root.addLayout(self._build_center(), stretch=1)
        root.addWidget(self._build_adj_bar())

    # ── Command bar ───────────────────────────────────────────────────────────

    def _build_command_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("CommandBar")

        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        # App mark
        mark = QLabel("MEDVOL")
        mark.setObjectName("AppMark")
        sub  = QLabel("VOLUMETRIC IMAGING")
        sub.setObjectName("AppSub")
        row.addWidget(mark)
        row.addWidget(sub)

        # Vertical rule
        row.addWidget(self._vline())

        # File buttons
        for text, slot in (
            ("DICOM FILE",   self.upload_dicom_file),
            ("DICOM SERIES", self.upload_folder),
            ("NIFTI FILE",   self.upload_nifti_folder),
        ):
            b = QPushButton(text)
            b.setObjectName("CmdBtn")
            b.clicked.connect(slot)
            row.addWidget(b)

        row.addWidget(self._vline())

        # Mode / zoom cluster
        self.mode_button = QPushButton("CURSOR")
        self.mode_button.setObjectName("ModeActive")
        self.mode_button.clicked.connect(self.toggle_mode)
        row.addWidget(self.mode_button)

        self.zoom_in_button = QPushButton("ZOOM +")
        self.zoom_in_button.setObjectName("ModeInactive")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_in_button.setEnabled(False)
        row.addWidget(self.zoom_in_button)

        self.zoom_out_button = QPushButton("ZOOM −")
        self.zoom_out_button.setObjectName("ModeInactive")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.zoom_out_button.setEnabled(False)
        row.addWidget(self.zoom_out_button)

        row.addStretch()

        # Volume info (right-aligned)
        self.vol_info = QLabel("NO VOLUME")
        self.vol_info.setObjectName("VolInfo")
        self.vol_info.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(self.vol_info)

        return bar

    # ── Center: 3D left | slice stack right ───────────────────────────────────

    def _build_center(self) -> QHBoxLayout:
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(0)

        # ── Left: VTK 3D panel (60% width) ───────────────────────────────
        vtk_panel = QWidget()
        vtk_panel.setObjectName("VtkPanel")
        vtk_lay = QVBoxLayout(vtk_panel)
        vtk_lay.setContentsMargins(0, 0, 0, 0)
        vtk_lay.setSpacing(0)

        self.vtk_widget = QVTKRenderWindowInteractor()
        self.vtk_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vtk_lay.addWidget(self.vtk_widget)

        hbox.addWidget(vtk_panel, stretch=3)   # 3 parts = ~60%

        # ── Right: three horizontal slice rows stacked ────────────────────
        right = QWidget()
        right.setObjectName("SliceColumn")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)

        self.axial_pane    = self._make_slice_pane("AXIAL",    self.update_axial_index)
        self.sagittal_pane = self._make_slice_pane("SAGITTAL", self.update_sagittal_index)
        self.coronal_pane  = self._make_slice_pane("CORONAL",  self.update_coronal_index)

        right_lay.addWidget(self.axial_pane)
        right_lay.addWidget(self.sagittal_pane)
        right_lay.addWidget(self.coronal_pane)
        right_lay.addStretch()

        hbox.addWidget(right, stretch=2)       # 2 parts = ~40%

        # ── VTK renderer ──────────────────────────────────────────────────
        self.renderer = vtk.vtkRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()

        return hbox

    def _make_slice_pane(self, title, slider_cb) -> SliceCanvas:
        pane = SliceCanvas(title)
        pane.slider.valueChanged.connect(slider_cb)
        pane.mpl_connect("button_press_event",   self.on_mouse_press)
        pane.mpl_connect("button_release_event", self.on_mouse_release)
        pane.mpl_connect("motion_notify_event",  self.on_mouse_motion)
        return pane

    # ── Bottom adjustment bar ─────────────────────────────────────────────────

    def _build_adj_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("AdjBar")

        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        self.brightness_slider, _ = self._adj_block(
            row, "BRIGHTNESS", -255, 255, 0, self.update_views)
        row.addWidget(self._vline("#3a3a36"))
        self.contrast_slider, _ = self._adj_block(
            row, "CONTRAST", -255, 255, 0, self.update_views)
        row.addStretch()

        return bar

    def _adj_block(self, parent_layout, name, lo, hi, init, cb):
        tag = QLabel(name)
        tag.setObjectName("AdjTag")
        tag.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        val = QLabel(f"{init:+d}")
        val.setObjectName("AdjVal")
        val.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        slider = QSlider(Qt.Horizontal)
        slider.setObjectName("AdjSlider")
        slider.setRange(lo, hi)
        slider.setValue(init)
        slider.setMinimumWidth(180)
        slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        slider.valueChanged.connect(cb)
        slider.valueChanged.connect(lambda v, l=val: l.setText(f"{v:+d}"))

        parent_layout.addWidget(tag)
        parent_layout.addWidget(slider, stretch=1)
        parent_layout.addWidget(val)
        return slider, val

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _vline(color="#3a3a36") -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.VLine)
        f.setFixedWidth(2)
        f.setStyleSheet(f"background:{color}; border:none;")
        return f

    # ── Cursors ───────────────────────────────────────────────────────────────

    def _build_cursors(self):
        self.crosshair_cursor = QtGui.QCursor(QtCore.Qt.CrossCursor)

        def _px_cursor(char, col):
            pm = QtGui.QPixmap(32, 32)
            pm.fill(QtCore.Qt.transparent)
            p = QtGui.QPainter(pm)
            f = p.font(); f.setPointSize(22); f.setBold(True)
            p.setFont(f); p.setPen(QtGui.QColor(col))
            p.drawText(0, 0, 32, 32, QtCore.Qt.AlignCenter, char)
            p.end()
            return QtGui.QCursor(pm)

        self.zoom_in_cursor  = _px_cursor("+", "#b8ff2e")
        self.zoom_out_cursor = _px_cursor("−", "#b8ff2e")

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        if not self._vtk_initialized:
            self._vtk_initialized = True
            self.interactor.Initialize()

    # ── Mode control ──────────────────────────────────────────────────────────

    def toggle_mode(self):
        if self.current_mode == CURSOR_MODE:
            self.set_zoom_mode()
        else:
            self.set_cursor_mode()

    def set_cursor_mode(self):
        self.current_mode = CURSOR_MODE
        self.mode_button.setText("CURSOR")
        self.mode_button.setObjectName("ModeActive")
        self.mode_button.setStyle(self.mode_button.style())
        self.zoom_in_button.setEnabled(False)
        self.zoom_out_button.setEnabled(False)
        self._zoom_limits.clear()
        self.zoom_mode = self.zoom_in_mode = self.zoom_out_mode = False
        self.update_views()
        self._set_canvas_cursor(self.crosshair_cursor)

    def set_zoom_mode(self):
        self.current_mode = ZOOM_MODE
        self.mode_button.setText("ZOOM")
        self.mode_button.setObjectName("ModeInactive")
        self.mode_button.setStyle(self.mode_button.style())
        self.zoom_in_button.setEnabled(True)
        self.zoom_out_button.setEnabled(True)
        self._set_canvas_cursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def zoom_in(self):
        if self.current_mode != ZOOM_MODE: return
        self.zoom_mode = self.zoom_in_mode = True
        self.zoom_out_mode = False
        self._set_canvas_cursor(self.zoom_in_cursor)

    def zoom_out(self):
        if self.current_mode != ZOOM_MODE: return
        self.zoom_mode = self.zoom_out_mode = True
        self.zoom_in_mode = False
        self._set_canvas_cursor(self.zoom_out_cursor)

    def _set_canvas_cursor(self, cursor):
        for p in (self.axial_pane, self.sagittal_pane, self.coronal_pane):
            p.setCursor(cursor)

    # ── File loading ──────────────────────────────────────────────────────────

    def upload_dicom_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "DICOM File", "", "DICOM (*.dcm *.DCM);;All (*)")
        if path:
            v = load_dicom_file(path, parent=self)
            if v is not None: self._load_volume(v)

    def upload_folder(self):
        path = QFileDialog.getExistingDirectory(self, "DICOM Series Folder")
        if path:
            v = load_dicom_folder(path, parent=self)
            if v is not None: self._load_volume(v)

    def upload_nifti_folder(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "NIfTI File", "", "NIfTI (*.nii *.nii.gz)")
        if path:
            try:
                self._load_volume(load_nifti_file(path))
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # ── Volume ────────────────────────────────────────────────────────────────

    def _load_volume(self, volume: np.ndarray):
        self.image_volume   = volume
        self.axial_index    = volume.shape[0] // 2
        self.sagittal_index = volume.shape[1] // 2
        self.coronal_index  = volume.shape[2] // 2

        self.axial_pane.slider.setRange(0, volume.shape[0] - 1)
        self.sagittal_pane.slider.setRange(0, volume.shape[1] - 1)
        self.coronal_pane.slider.setRange(0, volume.shape[2] - 1)

        self._zoom_limits.clear()
        self.axial_pane.slider.setValue(self.axial_index)
        self.sagittal_pane.slider.setValue(self.sagittal_index)
        self.coronal_pane.slider.setValue(self.coronal_index)

        z, y, x = volume.shape
        self.vol_info.setText(f"{z}×{y}×{x}  VOX")
        self.update_views()
        QTimer.singleShot(0, self._render_volume_deferred)

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _render_volume_deferred(self):
        if self.image_volume is None: return
        render_volume(self.image_volume, self.renderer,
                      self.vtk_widget.GetRenderWindow(), parent=self)

    def update_views(self):
        if self.image_volume is None: return
        br = self.brightness_slider.value()
        co = self.contrast_slider.value()

        axial_s    = self.image_volume[self.axial_index, :, :]
        sagittal_s = np.rot90(self.image_volume[:, self.sagittal_index, :], k=2)
        coronal_s  = np.flip(self.image_volume[:, :, self.coronal_index], axis=0)

        for raw, pane, idx, ch in (
            (axial_s,    self.axial_pane,    self.axial_index,    self.axial_crosshair),
            (sagittal_s, self.sagittal_pane, self.sagittal_index, self.sagittal_crosshair),
            (coronal_s,  self.coronal_pane,  self.coronal_index,  self.coronal_crosshair),
        ):
            self._draw_slice(pane, adjust_brightness_contrast(raw, br, co), idx, ch)

    def _draw_slice(self, pane: SliceCanvas, image: np.ndarray,
                    index: int, crosshair):
        fig = pane.figure
        ax  = fig.axes[0] if fig.axes else fig.add_axes([0, 0, 1, 1])
        ax.cla()
        ax.set_facecolor("#000000")
        ax.imshow(image, cmap="gray", aspect="auto", vmin=0, vmax=255)
        ax.axis("off")
        if crosshair:
            ax.axvline(crosshair[0], color="#b8ff2e", linewidth=0.8,
                       linestyle="--", alpha=0.75)
            ax.axhline(crosshair[1], color="#b8ff2e", linewidth=0.8,
                       linestyle="--", alpha=0.75)
        if self._zoom_limits.get(id(pane)):
            xl, yl = self._zoom_limits[id(pane)]
            ax.set_xlim(xl); ax.set_ylim(yl)
        fig.patch.set_facecolor("#000000")
        pane.draw()

    # ── Slider callbacks ──────────────────────────────────────────────────────

    def update_axial_index(self, v):
        if self.image_volume is not None:
            v = max(0, min(v, self.image_volume.shape[0] - 1))
        self.axial_index = v; self.update_views()

    def update_sagittal_index(self, v):
        if self.image_volume is not None:
            v = max(0, min(v, self.image_volume.shape[1] - 1))
        self.sagittal_index = v; self.update_views()

    def update_coronal_index(self, v):
        if self.image_volume is not None:
            v = max(0, min(v, self.image_volume.shape[2] - 1))
        self.coronal_index = v; self.update_views()

    # ── Mouse ─────────────────────────────────────────────────────────────────

    def on_mouse_press(self, event):
        if event.button != 1: return
        self.is_mouse_pressed = True
        if self.current_mode == ZOOM_MODE and self.zoom_mode:
            self._perform_zoom(event.canvas, event.xdata, event.ydata)
        elif self.current_mode == CURSOR_MODE:
            self._handle_cursor_motion(event)

    def on_mouse_release(self, event):
        if event.button == 1: self.is_mouse_pressed = False

    def on_mouse_motion(self, event):
        if self.is_mouse_pressed and self.current_mode == CURSOR_MODE:
            self._handle_cursor_motion(event)

    def _handle_cursor_motion(self, event):
        if not event.inaxes or event.xdata is None or self.image_volume is None:
            return
        z_max = self.image_volume.shape[0] - 1
        y_max = self.image_volume.shape[1] - 1
        x_max = self.image_volume.shape[2] - 1
        x = max(0, min(int(event.xdata), x_max))
        y = max(0, min(int(event.ydata), y_max))

        if event.canvas == self.axial_pane.canvas:
            self.sagittal_index  = max(0, min(y, y_max))
            self.coronal_index   = max(0, min(x, x_max))
            self.axial_crosshair = (x, y)
            self.sagittal_pane.slider.setValue(self.sagittal_index)
            self.coronal_pane.slider.setValue(self.coronal_index)
        elif event.canvas == self.sagittal_pane.canvas:
            self.axial_index        = max(0, min(z_max - y, z_max))
            self.coronal_index      = max(0, min(x_max - x, x_max))
            self.sagittal_crosshair = (x, y)
            self.axial_pane.slider.setValue(self.axial_index)
            self.coronal_pane.slider.setValue(self.coronal_index)
        elif event.canvas == self.coronal_pane.canvas:
            self.sagittal_index    = max(0, min(x, y_max))
            self.axial_index       = max(0, min(z_max - y, z_max))
            self.coronal_crosshair = (x, y)
            self.sagittal_pane.slider.setValue(self.sagittal_index)
            self.axial_pane.slider.setValue(self.axial_index)
        self.update_views()

    def _perform_zoom(self, canvas, x, y):
        if not self.zoom_mode or x is None or y is None: return
        pane = next((p for p in (self.axial_pane, self.sagittal_pane, self.coronal_pane)
                     if canvas == p.canvas), None)
        if not pane or not pane.figure.axes: return
        ax = pane.figure.axes[0]
        xmin, xmax = ax.get_xlim(); ymin, ymax = ax.get_ylim()
        f = ZOOM_IN_FACTOR if self.zoom_in_mode else ZOOM_OUT_FACTOR
        xl = (x - (xmax-xmin)*f/2, x + (xmax-xmin)*f/2)
        yl = (y - (ymax-ymin)*f/2, y + (ymax-ymin)*f/2)
        ax.set_xlim(xl); ax.set_ylim(yl)
        self._zoom_limits[id(pane)] = (xl, yl)
        pane.draw()

"""
SliceCanvas – one anatomical slice row in the right panel stack.

Layout (horizontal strip):
  ┌─────────┬─────────────────────────────────────┬──────┬──────────────────┐
  │  AXIAL  │ [fixed square matplotlib canvas]    │ 042  │ ───────●──────── │
  └─────────┴─────────────────────────────────────┴──────┴──────────────────┘
  plane tag       image well                     slice#      nav slider
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSlider, QSizePolicy
from PyQt5.QtCore import Qt

CANVAS_H = 260  # canvas height = width (square)


class SliceCanvas(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("SliceRow")
        self.setFixedHeight(CANVAS_H + 2)  # +2 for bottom border
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # ── Matplotlib square canvas ──────────────────────────────────────
        dpi = 100
        size_in = CANVAS_H / dpi
        self.figure = plt.Figure(figsize=(size_in, size_in), dpi=dpi, facecolor="#000000")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setFixedSize(CANVAS_H, CANVAS_H)
        self.canvas.setStyleSheet("background-color:#000000; border:none;")

        # ── Plane tag (left side label) ───────────────────────────────────
        self.view_label = QLabel(title.upper())
        self.view_label.setObjectName("PlaneTag")
        self.view_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        # ── Slice number readout ──────────────────────────────────────────
        self.slice_readout = QLabel("000")
        self.slice_readout.setObjectName("SliceNum")
        self.slice_readout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        # ── Navigation slider ─────────────────────────────────────────────
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.slider.setFixedHeight(CANVAS_H)
        self.slider.setOrientation(Qt.Horizontal)
        self.slider.valueChanged.connect(lambda v: self.slice_readout.setText(f"{v:03d}"))

        # ── Row layout ────────────────────────────────────────────────────
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self.view_label)
        row.addWidget(self.canvas)
        row.addWidget(self.slice_readout)
        row.addWidget(self.slider, stretch=1)

    # ── Pass-throughs ─────────────────────────────────────────────────────

    def mpl_connect(self, event, callback):
        return self.canvas.mpl_connect(event, callback)

    def setCursor(self, cursor):
        self.canvas.setCursor(cursor)

    def draw(self):
        self.canvas.draw()

    def clear(self):
        self.figure.clf()

    def add_subplot(self):
        return self.figure.add_subplot(111)

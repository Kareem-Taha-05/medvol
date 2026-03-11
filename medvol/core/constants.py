# UI modes
CURSOR_MODE = "cursor"
ZOOM_MODE   = "zoom"

ZOOM_IN_FACTOR  = 0.5
ZOOM_OUT_FACTOR = 2.0

# ── Palette: brutalist phosphor ────────────────────────────────────────────
#
#   CONCRETE  #252523  — base surface, raw mid-dark
#   SLAB      #1c1c1a  — recessed panels, slightly darker
#   WELL      #000000  — image wells, pure black
#   RULE      #3a3a36  — panel separators
#   INK       #e8e8e0  — primary text, warm off-white
#   GHOST     #55554e  — muted / secondary text
#   PHOSPHOR  #b8ff2e  — single accent, acid green
#   PHOSPHOR2 #d4ff6a  — lighter accent for hover
#   DIM_PH    #4a6612  — darkened phosphor for filled sub-pages

APP_STYLESHEET = """
/* ─── Global reset ─────────────────────────────────────────────────────── */
QWidget {
    background-color: #252523;
    color: #e8e8e0;
    font-family: 'Arial Black', 'Impact', 'Franklin Gothic Heavy', sans-serif;
    font-size: 11px;
    letter-spacing: 0.5px;
}

/* ─── Top command bar ──────────────────────────────────────────────────── */
QWidget#CommandBar {
    background-color: #1c1c1a;
    border-bottom: 2px solid #b8ff2e;
    min-height: 46px;
    max-height: 46px;
}

QLabel#AppMark {
    color: #b8ff2e;
    font-family: 'Arial Black', 'Impact', sans-serif;
    font-size: 16px;
    font-weight: 900;
    letter-spacing: 6px;
    padding: 0 20px;
}

QLabel#AppSub {
    color: #55554e;
    font-size: 8px;
    letter-spacing: 4px;
    padding: 0 0 0 4px;
}

/* ─── Command bar buttons ─────────────────────────────────────────────── */
QPushButton#CmdBtn {
    color: #55554e;
    background-color: transparent;
    border: 0px;
    border-left: 2px solid #3a3a36;
    border-radius: 0px;
    padding: 0 18px;
    font-family: 'Arial Black', 'Impact', sans-serif;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 2px;
    min-height: 46px;
    text-align: center;
}

QPushButton#CmdBtn:hover {
    color: #b8ff2e;
    background-color: #252523;
    border-left-color: #b8ff2e;
}

QPushButton#CmdBtn:pressed {
    background-color: #b8ff2e;
    color: #000000;
}

/* ─── Mode toggle buttons (active/inactive) ───────────────────────────── */
QPushButton#ModeActive {
    color: #000000;
    background-color: #b8ff2e;
    border: 0px;
    border-radius: 0px;
    padding: 0 18px;
    font-family: 'Arial Black', 'Impact', sans-serif;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 2px;
    min-height: 46px;
}

QPushButton#ModeActive:hover {
    background-color: #d4ff6a;
}

QPushButton#ModeInactive {
    color: #55554e;
    background-color: transparent;
    border: 0px;
    border-left: 2px solid #3a3a36;
    border-radius: 0px;
    padding: 0 18px;
    font-family: 'Arial Black', 'Impact', sans-serif;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 2px;
    min-height: 46px;
}

QPushButton#ModeInactive:hover {
    color: #b8ff2e;
    border-left-color: #b8ff2e;
}

QPushButton#ModeInactive:disabled {
    color: #2e2e2a;
    border-left-color: #2a2a28;
}

/* ─── Right info strip ────────────────────────────────────────────────── */
QLabel#VolInfo {
    color: #b8ff2e;
    font-family: 'Courier New', monospace;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 2px;
    padding: 0 20px;
}

/* ─── 3D panel (left, large) ──────────────────────────────────────────── */
QWidget#VtkPanel {
    background-color: #000000;
    border-right: 2px solid #3a3a36;
}

/* ─── Slice panels (right column) ─────────────────────────────────────── */
QWidget#SliceRow {
    background-color: #1c1c1a;
    border-bottom: 2px solid #3a3a36;
}

/* ─── Plane label ──────────────────────────────────────────────────────── */
QLabel#PlaneTag {
    color: #b8ff2e;
    font-family: 'Arial Black', 'Impact', sans-serif;
    font-size: 8px;
    font-weight: 900;
    letter-spacing: 5px;
    background-color: #1c1c1a;
    padding: 4px 8px;
    border-right: 2px solid #3a3a36;
    min-width: 70px;
    max-width: 70px;
}

QLabel#SliceNum {
    color: #3a3a36;
    font-family: 'Courier New', monospace;
    font-size: 10px;
    padding: 0 8px;
    background-color: #1c1c1a;
    min-width: 38px;
    max-width: 38px;
}

/* ─── Sliders (slice navigation) ──────────────────────────────────────── */
QSlider::groove:horizontal {
    background: #1c1c1a;
    height: 2px;
    border-radius: 0;
}

QSlider::handle:horizontal {
    background: #b8ff2e;
    border: none;
    width: 8px;
    height: 14px;
    margin: -6px 0;
    border-radius: 0;
}

QSlider::sub-page:horizontal {
    background: #4a6612;
}

QSlider::handle:horizontal:hover {
    background: #d4ff6a;
}

/* ─── Bottom adjustment strip ──────────────────────────────────────────── */
QWidget#AdjBar {
    background-color: #1c1c1a;
    border-top: 2px solid #3a3a36;
    min-height: 38px;
    max-height: 38px;
}

QLabel#AdjTag {
    color: #55554e;
    font-family: 'Arial Black', sans-serif;
    font-size: 8px;
    font-weight: 900;
    letter-spacing: 3px;
    padding: 0 10px;
}

QLabel#AdjVal {
    color: #b8ff2e;
    font-family: 'Courier New', monospace;
    font-size: 10px;
    min-width: 38px;
    max-width: 38px;
    padding: 0 6px;
}

QSlider#AdjSlider::groove:horizontal {
    background: #2e2e2a;
    height: 2px;
}

QSlider#AdjSlider::handle:horizontal {
    background: #e8e8e0;
    border: none;
    width: 8px;
    height: 14px;
    margin: -6px 0;
    border-radius: 0;
}

QSlider#AdjSlider::sub-page:horizontal {
    background: #4a4a44;
}

QSlider#AdjSlider::handle:horizontal:hover {
    background: #b8ff2e;
}

/* ─── Dialogs ───────────────────────────────────────────────────────────── */
QProgressDialog, QMessageBox {
    background-color: #252523;
    color: #e8e8e0;
}

QProgressDialog QPushButton, QMessageBox QPushButton {
    background-color: #1c1c1a;
    color: #e8e8e0;
    border: 2px solid #b8ff2e;
    border-radius: 0;
    padding: 5px 20px;
    min-width: 80px;
    text-align: center;
    font-family: 'Arial Black', sans-serif;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 2px;
}

QProgressDialog QPushButton:hover, QMessageBox QPushButton:hover {
    background-color: #b8ff2e;
    color: #000000;
}
"""

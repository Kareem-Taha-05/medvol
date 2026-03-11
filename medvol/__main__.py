"""
Entry point: python -m medvol
Also called by the `medvol` CLI script defined in pyproject.toml.
"""

import sys
from PyQt5.QtWidgets import QApplication
from medvol.ui.main_viewer import MedicalImageViewer


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MEDVOL")
    app.setApplicationVersion("1.0.0")

    viewer = MedicalImageViewer()
    viewer.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

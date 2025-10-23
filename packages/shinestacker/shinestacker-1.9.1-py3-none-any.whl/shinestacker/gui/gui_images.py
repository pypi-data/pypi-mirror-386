# pylint: disable=C0114, C0115, C0116, E0611, W0718, E1101, C0103, R0914
import webbrowser
import subprocess
import os
import numpy as np
import cv2
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget, QLabel, QStackedWidget
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtCore import Qt, QMargins
from PySide6.QtGui import QPixmap, QImage
from .. config.gui_constants import gui_constants
from .. core.core_utils import running_under_windows, running_under_macos
from .. algorithms.utils import read_img


def open_file(file_path):
    try:
        if running_under_macos():
            subprocess.call(('open', file_path))
        elif running_under_windows():
            os.startfile(file_path)
        else:
            subprocess.call(('xdg-open', file_path))
    except Exception:
        webbrowser.open("file://" + file_path)


class GuiPdfView(QPdfView):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setPageSpacing(0)
        self.setDocumentMargins(QMargins(0, 0, 0, 0))
        self.pdf_document = QPdfDocument()
        err = self.pdf_document.load(file_path)
        if err == QPdfDocument.Error.None_:
            self.setDocument(self.pdf_document)
            first_page_size = self.pdf_document.pagePointSize(0)
            zoom_factor = gui_constants.GUI_IMG_WIDTH / first_page_size.width()
            extra_zoom = 0.75 if running_under_windows() else 1.0
            self.setZoomFactor(zoom_factor * extra_zoom)
            self.setFixedSize(gui_constants.GUI_IMG_WIDTH,
                              int(first_page_size.height() * zoom_factor))
        else:
            raise RuntimeError(f"Can't load file: {file_path}. Error code: {err}.")
        self.setStyleSheet('''
        QWidget {
            border: 2px solid #0000a0;
        }
        QWidget:hover {
            border: 2px solid #a0a0ff;
        }
        ''')

    def sizeHint(self):
        return self.size()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            open_file(self.file_path)
        super().mouseReleaseEvent(event)


class GuiImageView(QWidget):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setFixedWidth(gui_constants.GUI_IMG_WIDTH)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.image_label)
        self.setLayout(self.main_layout)
        try:
            img = read_img(file_path)
            height, width = img.shape[:2]
            scale_factor = gui_constants.GUI_IMG_WIDTH / width
            new_height = int(height * scale_factor)
            img = cv2.resize(img, (gui_constants.GUI_IMG_WIDTH, new_height),
                             interpolation=cv2.INTER_LINEAR)
        except Exception as e:
            raise RuntimeError(f"Can't load file: {file_path}.") from e
        if img.dtype == np.uint16:
            img = (img // 256).astype(np.uint8)
        if len(img.shape) == 3:
            h, w, ch = img.shape
            bytes_per_line = ch * w
            rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        else:
            h, w = img.shape
            bytes_per_line = w
            q_img = QImage(img.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap)
        if pixmap:
            scaled_pixmap = pixmap.scaledToWidth(
                gui_constants.GUI_IMG_WIDTH, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            raise RuntimeError(f"Can't load file: {file_path}.")
        self.setStyleSheet('''
        QWidget {
            border: 2px solid #0000a0;
        }
        QWidget:hover {
            border: 2px solid #a0a0ff;
        }
        ''')

    def sizeHint(self):
        return self.size()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            open_file(self.file_path)
        super().mouseReleaseEvent(event)


class GuiOpenApp(QWidget):
    def __init__(self, app, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.app = app
        self.setFixedWidth(gui_constants.GUI_IMG_WIDTH)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.image_label)
        self.setLayout(self.main_layout)
        pixmap = QPixmap(file_path)
        if pixmap:
            scaled_pixmap = pixmap.scaledToWidth(
                gui_constants.GUI_IMG_WIDTH, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            raise RuntimeError(f"Can't load file: {file_path}.")
        self.setStyleSheet('''
        QWidget {
            border: 2px solid #a00000;
        }
        QWidget:hover {
            border: 2px solid #ffa0a0;
        }
        ''')

    def sizeHint(self):
        return self.size()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.app != 'internal_retouch_app':
                try:
                    os.system(f"{self.app} -f {self.file_path} &")
                except Exception as e:
                    raise RuntimeError(
                        f"Can't open file {self.file_path} with app: {self.app}.\n{str(e)}") from e
            else:
                app = None
                stacked_widget = self.parent().window().findChild(QStackedWidget)
                if stacked_widget:
                    for child in stacked_widget.children():
                        if child.metaObject().className() == 'MainWindow':
                            app = child
                            break
                    else:
                        raise RuntimeError("MainWindow object not found")
                if app:
                    app.retouch_callback(self.file_path)
                else:
                    raise RuntimeError("MainWindow object not found")
        super().mouseReleaseEvent(event)

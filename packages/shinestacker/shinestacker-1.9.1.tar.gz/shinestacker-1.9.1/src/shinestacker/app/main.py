# pylint: disable=C0114, C0115, C0116, C0413, E0611, R0903, E1121, W0201, R0915, R0912
import sys
import argparse
import matplotlib
import matplotlib.backends.backend_pdf
matplotlib.use('agg')
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QStackedWidget,
                               QMenu, QMessageBox, QDialog, QLabel, QListWidget, QPushButton)
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtCore import QEvent, QTimer, Signal
from shinestacker.config.config import config
config.init(DISABLE_TQDM=True, COMBINED_APP=True, DONT_USE_NATIVE_MENU=True)
from shinestacker.config.constants import constants
from shinestacker.gui.main_window import MainWindow
from shinestacker.retouch.image_editor_ui import ImageEditorUI
from shinestacker.app.gui_utils import fill_app_menu
from shinestacker.app.help_menu import add_help_action
from shinestacker.app.open_frames import open_frames
from shinestacker.app.args_parser_opts import (
    add_project_arguments, add_retouch_arguments, extract_positional_filename,
    setup_filename_argument, process_filename_argument
)
from shinestacker.app.gui_utils import make_app


class SelectionDialog(QDialog):
    selection_made = Signal(str, bool)

    def __init__(self, title, message, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.selected_item = ""
        self.setup_ui(message, items)
        self.setMinimumSize(300, 300)

    def setup_ui(self, message, items):
        layout = QVBoxLayout(self)
        if message:
            label = QLabel(message)
            layout.addWidget(label)
        self.list_widget = QListWidget()
        self.list_widget.addItems(items)
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.list_widget)
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setEnabled(False)
        button_layout.addWidget(self.ok_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def on_selection_changed(self):
        selected_items = self.list_widget.selectedItems()
        self.ok_button.setEnabled(len(selected_items) > 0)

    def accept(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            self.selected_item = selected_items[0].text()
            self.selection_made.emit(self.selected_item, True)
            super().accept()

    def reject(self):
        self.selected_item = ""
        self.selection_made.emit("", False)
        super().reject()

    @staticmethod
    def get_selection(title, message, items, parent=None):
        dialog = SelectionDialog(title, message, items, parent)
        result = dialog.exec()
        return dialog.selected_item if result == QDialog.Accepted else ""


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(constants.APP_TITLE)
        self.resize(1400, 900)
        center = QGuiApplication.primaryScreen().geometry().center()
        self.move(center - self.rect().center())
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.project_window = MainWindow()
        self.project_window.set_retouch_callback(self.retouch_callback)
        self.retouch_window = ImageEditorUI()
        self.stacked_widget.addWidget(self.project_window)
        self.stacked_widget.addWidget(self.retouch_window)
        self.app_menu = self.create_menu()
        self.project_window.menuBar().insertMenu(
            self.project_window.menuBar().actions()[0], self.app_menu)
        self.retouch_window.menuBar().insertMenu(
            self.retouch_window.menuBar().actions()[0], self.app_menu)
        add_help_action(self.project_window)
        add_help_action(self.retouch_window)
        file_menu = None
        for action in self.retouch_window.menuBar().actions():
            if action.text() == "&File":
                file_menu = action.menu()
                break
        if file_menu is not None:
            import_action = QAction("Import from Current Project", self)
            import_action.triggered.connect(self.import_from_project)
            file_menu.addAction(import_action)
        else:
            raise RuntimeError("File menu not found!")

    def switch_to_project(self):
        self.switch_app(0)
        self.switch_to_project_action.setChecked(True)
        self.switch_to_retouch_action.setChecked(False)
        self.switch_to_project_action.setEnabled(False)
        self.switch_to_retouch_action.setEnabled(True)
        self.project_window.update_title()
        self.project_window.activateWindow()
        self.project_window.setFocus()

    def switch_to_retouch(self):
        self.switch_app(1)
        self.switch_to_project_action.setChecked(False)
        self.switch_to_retouch_action.setChecked(True)
        self.switch_to_project_action.setEnabled(True)
        self.switch_to_retouch_action.setEnabled(False)
        self.retouch_window.update_title()
        self.retouch_window.activateWindow()
        self.retouch_window.setFocus()

    def create_menu(self):
        app_menu = QMenu(constants.APP_STRING)
        self.switch_to_project_action = QAction("Project", self)
        self.switch_to_project_action.setCheckable(True)
        self.switch_to_project_action.triggered.connect(self.switch_to_project)
        self.switch_to_retouch_action = QAction("Retouch", self)
        self.switch_to_retouch_action.setCheckable(True)
        self.switch_to_retouch_action.triggered.connect(self.switch_to_retouch)
        app_menu.addAction(self.switch_to_project_action)
        app_menu.addAction(self.switch_to_retouch_action)
        app_menu.addSeparator()
        fill_app_menu(self, app_menu, True, True,
                      self.project_window.handle_config,
                      self.retouch_window.handle_config)
        return app_menu

    def quit(self):
        if not self.retouch_window.quit():
            return False
        if not self.project_window.quit():
            return False
        self.close()
        return True

    def switch_app(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def retouch_callback(self, filename):
        self.switch_to_retouch()
        if isinstance(filename, list):
            open_frames(self.retouch_window, None, ";".join(filename))
        else:
            self.retouch_window.io_gui_handler.open_file(filename)

    def import_from_project(self):
        project = self.project_window.project()
        if project is None:
            QMessageBox.warning(self.parent(),
                                "No Active Project", "No project has been created or opened.")
            return
        if len(project.jobs) == 0:
            QMessageBox.warning(self.parent(),
                                "No Jobs In Project", "The current project has no job. "
                                "Create and run a job first.")
            return
        if len(project.jobs) > 1:
            job_names = [job.params['name'] for job in project.jobs]
            job_name = SelectionDialog.get_selection(
                "Job Selection",
                "Please select one of the active jobs:",
                job_names
            )
            job = None
            for job in project.jobs:
                if job.params['name'] == job_name:
                    break
            if job is None:
                return
        else:
            job = project.jobs[0]
        retouch_path = self.project_window.get_retouch_path(job)
        if isinstance(retouch_path, list):
            open_frames(self.retouch_window, None, ";".join(retouch_path))
        else:
            self.retouch_window.io_gui_handler.open_file(retouch_path)


class Application(QApplication):
    def event(self, event):
        if event.type() == QEvent.Quit and event.spontaneous():
            if not self.main_app.quit():
                return True
        return super().event(event)


def main():
    positional_filename, filtered_args = extract_positional_filename()
    parser = argparse.ArgumentParser(
        prog=f'{constants.APP_STRING.lower()}',
        description='Focus stacking App.',
        epilog=f'This app is part of the {constants.APP_STRING} package.')
    setup_filename_argument(parser, use_const=True)
    app_group = parser.add_mutually_exclusive_group()
    app_group.add_argument('-j', '--project', action='store_true', help='''
open project window at startup instead of project windows (default).
''')
    app_group.add_argument('-r', '--retouch', action='store_true', help='''
open retouch window at startup instead of project windows.
''')
    add_project_arguments(parser)
    add_retouch_arguments(parser)
    args = vars(parser.parse_args(filtered_args))
    filename = process_filename_argument(args, positional_filename)
    path = args['path']
    if filename and path:
        print("can't specify both arguments --filename and --path", file=sys.stderr)
        sys.exit(1)

    app = make_app(Application)
    main_app = MainApp()
    app.main_app = main_app

    main_app.show()
    main_app.activateWindow()
    if args['expert']:
        main_app.project_window.set_expert_options()
    if args['view_overlaid']:
        main_app.retouch_window.set_strategy('overlaid')
    elif args['view_side_by_side']:
        main_app.retouch_window.set_strategy('sidebyside')
    elif args['view_top_bottom']:
        main_app.retouch_window.set_strategy('topbottom')
    if filename:
        filenames = filename.split(';')
        filename = filenames[0]
        extension = filename.split('.')[-1]
        if len(filenames) == 1 and extension == 'fsp':
            main_app.project_window.project_controller.open_project(filename)
            main_app.project_window.setFocus()
        else:
            main_app.switch_to_retouch()
            open_frames(main_app.retouch_window, filename, path)
    else:
        retouch = args['retouch']
        if retouch:
            main_app.switch_to_retouch()
        else:
            main_app.switch_to_project()
            if args['new-project']:
                QTimer.singleShot(100, main_app.project_window.project_controller.new_project)
    QTimer.singleShot(100, main_app.setFocus)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

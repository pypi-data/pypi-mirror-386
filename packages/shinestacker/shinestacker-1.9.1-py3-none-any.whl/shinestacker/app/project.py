# pylint: disable=C0114, C0115, C0116, C0413, E0611, R0903, E1121, W0201
import os
import sys
import argparse
import matplotlib
import matplotlib.backends.backend_pdf
matplotlib.use('agg')
from PySide6.QtWidgets import QApplication, QMenu
from PySide6.QtCore import QTimer, QEvent
from shinestacker.config.config import config
config.init(DISABLE_TQDM=True, DONT_USE_NATIVE_MENU=True)
from shinestacker.config.constants import constants
from shinestacker.gui.main_window import MainWindow
from shinestacker.app.gui_utils import fill_app_menu
from shinestacker.app.help_menu import add_help_action
from shinestacker.app.args_parser_opts import (
    add_project_arguments, extract_positional_filename,
    setup_filename_argument, process_filename_argument
)
from shinestacker.app.gui_utils import make_app


class ProjectApp(MainWindow):
    def __init__(self):
        super().__init__()
        self.app_menu = self.create_menu()
        self.menuBar().insertMenu(self.menuBar().actions()[0], self.app_menu)
        add_help_action(self)
        self.set_retouch_callback(self._retouch_callback)

    def create_menu(self):
        app_menu = QMenu(constants.APP_STRING)
        fill_app_menu(self, app_menu, True, False,
                      self.handle_config,
                      lambda: None)
        return app_menu

    def _retouch_callback(self, filename):
        p = ";".join(filename)
        os.system(f'{constants.RETOUCH_APP} -p "{p}" &')


class Application(QApplication):
    def event(self, event):
        if event.type() == QEvent.Quit and event.spontaneous():
            self.window.quit()
        return super().event(event)


def main():
    positional_filename, filtered_args = extract_positional_filename()
    parser = argparse.ArgumentParser(
        prog=f'{constants.APP_STRING.lower()}-project',
        description='Manage and run focus stack jobs.',
        epilog=f'This app is part of the {constants.APP_STRING} package.')
    setup_filename_argument(parser, use_const=True)
    add_project_arguments(parser)
    args = vars(parser.parse_args(filtered_args))
    filename = process_filename_argument(args, positional_filename)
    app = make_app(Application)
    window = ProjectApp()
    if args['expert']:
        window.set_expert_options()
    app.window = window
    window.show()
    if filename:
        QTimer.singleShot(100, lambda: window.project_controller.open_project(filename))
    elif args['new-project']:
        QTimer.singleShot(100, window.project_controller.new_project)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

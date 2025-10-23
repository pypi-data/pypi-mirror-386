# pylint: disable=C0114, C0116, E0602, W0718
import os
import sys
import platform
import matplotlib
from .. config.config import config

if not config.DISABLE_TQDM:
    from tqdm import tqdm
    from tqdm.notebook import tqdm_notebook


def check_path_exists(path):
    if not os.path.exists(path):
        raise RuntimeError('Path does not exist: ' + path)


def make_tqdm_bar(name, size, ncols=80):
    if not config.DISABLE_TQDM:
        if config.JUPYTER_NOTEBOOK:
            tbar = tqdm_notebook(desc=name, total=size)
        else:
            tbar = tqdm(desc=name, total=size, ncols=ncols)
        return tbar
    return None


def get_app_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def running_under_windows() -> bool:
    return platform.system().lower() == 'windows'


def running_under_macos() -> bool:
    return platform.system().lower() == "darwin"


def running_under_linux() -> bool:
    return platform.system().lower() == 'linux'


def make_chunks(ll, max_size):
    return [ll[i:i + max_size] for i in range(0, len(ll), max_size)]


def setup_matplotlib_mode():
    try:
        __IPYTHON__ # noqa
    except Exception:
        matplotlib.use('agg')
    matplotlib.pyplot.set_loglevel("warning")
    matplotlib.rcParams['pdf.fonttype'] = 42

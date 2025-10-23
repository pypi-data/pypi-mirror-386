# pylint: disable=C0114, C0115, C0116, E0602, R0903, R0902
import os
import numpy as np
from .. core.exceptions import InvalidOptionError, RunStopException
from .. config.constants import constants
from .. core.colors import color_str
from .utils import read_img, get_img_metadata, get_first_image_file


class BaseStackAlgo:
    def __init__(self, name, steps_per_frame, float_type=constants.DEFAULT_PY_FLOAT):
        self._name = name
        self._steps_per_frame = steps_per_frame
        self.process = None
        self.filenames = None
        self.shape = None
        self.dtype = None
        self.num_pixel_values = None
        self.max_pixel_value = None
        self.do_step_callback = False
        if float_type == constants.FLOAT_32:
            self.float_type = np.float32
        elif float_type == constants.FLOAT_64:
            self.float_type = np.float64
        else:
            raise InvalidOptionError(
                "float_type", float_type,
                details=" valid values are FLOAT_32 and FLOAT_64"
            )

    def name(self):
        return self._name

    def set_process(self, process):
        self.process = process

    def set_do_step_callback(self, enable):
        self.do_step_callback = enable

    def idx_tot_str(self, idx):
        return f"{idx + 1}/{len(self.filenames)}"

    def image_str(self, idx):
        return f"frame {self.idx_tot_str(idx)}, " \
               f"{os.path.basename(self.filenames[idx])}"

    def num_images(self):
        return len(self.filenames)

    def init(self, filenames):
        self.filenames = filenames
        self.shape, self.dtype = get_img_metadata(read_img(get_first_image_file(filenames)))
        self.num_pixel_values = constants.NUM_UINT8 \
            if self.dtype == np.uint8 else constants.NUM_UINT16
        self.max_pixel_value = constants.MAX_UINT8 \
            if self.dtype == np.uint8 else constants.MAX_UINT16

    def total_steps(self, n_frames):
        return self._steps_per_frame * n_frames

    def print_message(self, msg):
        self.process.sub_message_r(color_str(msg, constants.LOG_COLOR_LEVEL_3))

    def check_running(self, cleanup_callback=None):
        if self.process.callback(constants.CALLBACK_CHECK_RUNNING,
                                 self.process.id, self.process.name) is False:
            if cleanup_callback is not None:
                cleanup_callback()
            raise RunStopException(self.name)

    def after_step(self, step):
        if self.do_step_callback:
            self.process.callback(constants.CALLBACK_AFTER_STEP,
                                  self.process.id, self.process.name, step)

# pylint: disable=C0114, C0115, C0116, E1101, R0902, R0913, R0917, R0914, R0912, R0915
import numpy as np
import cv2
from .. config.constants import constants
from .. core.exceptions import InvalidOptionError
from .utils import read_img, read_and_validate_img, img_bw
from .base_stack_algo import BaseStackAlgo


class DepthMapStack(BaseStackAlgo):
    def __init__(self, map_type=constants.DEFAULT_DM_MAP,
                 energy=constants.DEFAULT_DM_ENERGY,
                 kernel_size=constants.DEFAULT_DM_KERNEL_SIZE,
                 blur_size=constants.DEFAULT_DM_BLUR_SIZE,
                 smooth_size=constants.DEFAULT_DM_SMOOTH_SIZE,
                 temperature=constants.DEFAULT_DM_TEMPERATURE,
                 levels=constants.DEFAULT_DM_LEVELS,
                 float_type=constants.DEFAULT_DM_FLOAT):
        super().__init__("depth map", 2, float_type)
        self.map_type = map_type
        self.energy = energy
        self.kernel_size = kernel_size
        self.blur_size = blur_size
        self.smooth_size = smooth_size
        self.temperature = temperature
        self.levels = levels

    def get_sobel_map(self, gray_images):
        energies = np.zeros(gray_images.shape, dtype=self.float_type)
        for i in range(gray_images.shape[0]):
            img = gray_images[i]
            energies[i] = np.abs(cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)) + \
                np.abs(cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3))
        return energies

    def get_laplacian_map(self, gray_images):
        laplacian = np.zeros(gray_images.shape, dtype=self.float_type)
        for i in range(gray_images.shape[0]):
            blurred = cv2.GaussianBlur(gray_images[i], (self.blur_size, self.blur_size), 0)
            laplacian[i] = np.abs(cv2.Laplacian(blurred, cv2.CV_64F, ksize=self.kernel_size))
        return laplacian

    def smooth_energy(self, energy_map):
        if self.smooth_size <= 0:
            return energy_map
        smoothed = np.zeros(energy_map.shape, dtype=np.float32)
        for i in range(energy_map.shape[0]):
            energy_32f = energy_map[i].astype(np.float32)
            smoothed_32f = cv2.bilateralFilter(energy_32f, self.smooth_size, 25, 25)
            smoothed[i] = smoothed_32f.astype(energy_map.dtype)
        return smoothed

    def get_focus_map(self, energies):
        if self.map_type == constants.DM_MAP_AVERAGE:
            sum_energies = np.sum(energies, axis=0)
            return np.divide(energies, sum_energies, where=sum_energies != 0)
        if self.map_type == constants.DM_MAP_MAX:
            max_energy = np.max(energies, axis=0)
            relative = np.exp((energies - max_energy) / self.temperature)
            return relative / np.sum(relative, axis=0)
        raise InvalidOptionError("map_type", self.map_type, details=f" valid values are "
                                 f"{constants.DM_MAP_AVERAGE} and {constants.DM_MAP_MAX}.")

    def focus_stack(self):
        n_images = len(self.filenames)
        gray_images = np.empty((n_images, *self.shape), dtype=self.float_type)
        for i, img_path in enumerate(self.filenames):
            self.print_message(f": reading and validating {self.image_str(i)}")
            img = read_and_validate_img(img_path, self.shape, self.dtype)
            gray = img_bw(img)
            gray_images[i] = gray.astype(self.float_type)
            self.after_step(i)
            self.check_running()
        if self.energy == constants.DM_ENERGY_SOBEL:
            energies = self.get_sobel_map(gray_images)
        elif self.energy == constants.DM_ENERGY_LAPLACIAN:
            energies = self.get_laplacian_map(gray_images)
        else:
            raise InvalidOptionError(
                'energy', self.energy, details=f" valid values are "
                f"{constants.DM_ENERGY_SOBEL} and {constants.DM_ENERGY_LAPLACIAN}."
            )
        max_energy = np.max(energies)
        if max_energy > 0:
            energies = energies / max_energy
        if self.smooth_size > 0:
            energies = self.smooth_energy(energies)
        weights = self.get_focus_map(energies)
        blended_pyramid = None
        for i, img_path in enumerate(self.filenames):
            self.print_message(f": reading {self.image_str(i)}")
            img = read_img(img_path).astype(self.float_type)
            weight = weights[i]
            gp_img = [img]
            gp_weight = [weight]
            for _ in range(self.levels - 1):
                gp_img.append(cv2.pyrDown(gp_img[-1]))
                gp_weight.append(cv2.pyrDown(gp_weight[-1]))
            lp_img = [gp_img[-1]]
            for j in range(self.levels - 1, 0, -1):
                size = (gp_img[j - 1].shape[1], gp_img[j - 1].shape[0])
                expanded = cv2.pyrUp(gp_img[j], dstsize=size)
                lp_img.append(gp_img[j - 1] - expanded)
            current_blend = [lp_img[j] * gp_weight[self.levels - 1 - j][..., np.newaxis]
                             for j in range(self.levels)]
            blended_pyramid = current_blend if blended_pyramid is None \
                else [np.add(bp, cb) for bp, cb in zip(blended_pyramid, current_blend)]
            self.after_step(i + n_images)
            self.check_running()
        result = blended_pyramid[0]
        self.print_message(': blend levels')
        for j in range(1, self.levels):
            size = (blended_pyramid[j].shape[1], blended_pyramid[j].shape[0])
            result = cv2.pyrUp(result, dstsize=size) + blended_pyramid[j]
        return np.clip(np.absolute(result), 0, self.num_pixel_values).astype(self.dtype)

import cv2
import numpy as np
import urllib.request
from typing import Optional, Union, Literal, Tuple
import os

from PIL import ImageGrab

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame

from .pygame import numpy_to_pygame_surface, pygame_surface_to_numpy


def get_image_from_cam(cap: cv2.VideoCapture) -> Optional[np.ndarray]:
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame from camera")
        return None
    return frame


def get_image_from_url(url: str) -> Optional[np.ndarray]:
    try:
        with urllib.request.urlopen(url, timeout=5) as req:
            arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
            return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"Error loading image from URL: {e}")
        return None


def get_image(source: Union[cv2.VideoCapture, str], output: Literal['numpy', 'pygame'] = 'numpy') -> Optional[
    Union[np.ndarray, "pygame.Surface"]]:
    if isinstance(source, str):
        img = get_image_from_url(source)
    elif isinstance(source, cv2.VideoCapture):
        img = get_image_from_cam(source)
    else:
        raise ValueError("Invalid source type. Expected cv2.VideoCapture or str (URL).")

    if img is None:
        return None

    if output == 'pygame':
        return numpy_to_pygame_surface(img)
    return img


def take_screenshot(
        region: Optional[Tuple[int, int, int, int]] = None,
        mode: str = "RGB",
) -> np.ndarray:
    img = np.array(ImageGrab.grab(region))
    if mode == "RGB":
        return img.copy()
    elif mode == "BGR":
        img[:, :, ::-1].copy()
    else:
        raise ValueError("Invalid mode format. Use 'RGB' or 'BGR'.")


def rotate(image, angle, center=None, scale=1):
    if isinstance(center, np.ndarray):
        center = center.tolist()
    h, w = image.shape[:2]
    if center is None:
        center = (w // 2, h // 2)
    rotate_matrix = cv2.getRotationMatrix2D(center, angle, scale)
    image = cv2.warpAffine(src=image, M=rotate_matrix, dsize=(w, h))
    return image


def overlay(main_img, overlay_img, pos: tuple = (0, 0)):
    '''
    Overlay function to blend an overlay image onto a main image at a specified position.

    :param main_img (numpy.ndarray): The main image onto which the overlay will be applied.
    :param overlay_img (numpy.ndarray): The overlay image to be blended onto the main image.
                                        *** for rgba can use `cv2.imread('path',cv2.IMREAD_UNCHANGED)`
    :param pos (tuple): A tuple (x, y) representing the position where the overlay should be applied.

    :return: main_img (numpy.ndarray): The main image with the overlay applied in the specified position.
    '''

    if main_img.shape[2] == 4:
        main_img = cv2.cvtColor(main_img, cv2.COLOR_RGBA2RGB)

    x, y = pos
    h_overlay, w_overlay, _ = overlay_img.shape
    h_main, w_main, _ = main_img.shape

    x_start = max(0, x)
    x_end = min(x + w_overlay, w_main)
    y_start = max(0, y)
    y_end = min(y + h_overlay, h_main)

    img_main_roi = main_img[y_start:y_end, x_start:x_end]
    img_overlay_roi = overlay_img[(y_start - y):(y_end - y), (x_start - x):(x_end - x)]

    if overlay_img.shape[2] == 4:
        img_a = img_overlay_roi[:, :, 3] / 255.0
        img_rgb = img_overlay_roi[:, :, :3]
        img_overlay_roi = img_rgb * img_a[:, :, np.newaxis] + img_main_roi * (1 - img_a[:, :, np.newaxis])

    img_main_roi[:, :] = img_overlay_roi

    return main_img


def crop_img(image, xywhn, shift=(0, 0), resize=None):
    wh_ = np.array(image.shape[1::-1])
    xyn = np.array(xywhn[:2])
    whn = np.array(xywhn[2:])
    x1y1_ = ((xyn - whn / 2) * wh_).astype(int)
    x2y2_ = ((xyn + whn / 2) * wh_).astype(int)

    x1_, y1_ = x1y1_ + shift
    x2_, y2_ = x2y2_ + shift

    image_crop = image[y1_:y2_, x1_:x2_]

    if resize:
        return cv2.resize(image_crop, resize)
    return image_crop


def controller(img, brightness=0, contrast=0):
    """Adjust brightness and contrast of an image."""

    if brightness != 0:
        shadow = brightness if brightness > 0 else 0
        max_val = 255 if brightness > 0 else 255 + brightness
        alpha = (max_val - shadow) / 255
        gamma = shadow
        img = cv2.addWeighted(img, alpha, img, 0, gamma)

    if contrast != 0:
        alpha = float(131 * (contrast + 127)) / (127 * (131 - contrast))
        gamma = 127 * (1 - alpha)
        img = cv2.addWeighted(img, alpha, img, 0, gamma)

    return img

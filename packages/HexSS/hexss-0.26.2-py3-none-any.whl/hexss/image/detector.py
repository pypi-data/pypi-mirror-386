from pathlib import Path
from typing import Union, Optional, List, Dict
import hexss
from hexss.box import Box
from hexss.image import Image
from PIL import Image as PILImage, ImageFont
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    hexss.check_packages('ultralytics', auto_install=True)
    from ultralytics import YOLO


class Detection:
    def __init__(self, idx: int, name: str, conf: float,
                 xywhn: np.ndarray, xywh: np.ndarray, xyxyn: np.ndarray, xyxy: np.ndarray, box: Box):
        """
        Args:
            idx (int): Index of the detected class.
            name (str): Name of the detected class.
            conf (float): Confidence score of the detection.
            xywhn (np.ndarray): Bounding box in normalized (x, y, width, height) format.
            xywh (np.ndarray): Bounding box in pixel (x, y, width, height) format.
            xyxyn (np.ndarray): Bounding box in normalized (x1, y1, x2, y2) format.
            xyxy (np.ndarray): Bounding box in pixel (x1, y1, x2, y2) format.
            box (Box): Box object representing the bounding box.
        """
        self.idx = idx
        self.name = name
        self.conf = conf
        self.xywhn = xywhn
        self.xywh = xywh
        self.xyxyn = xyxyn
        self.xyxy = xyxy
        self.image: Optional[Image] = None
        self.box = box

    def set_image(self, image: Union[PILImage.Image, np.ndarray], xyxy: np.ndarray) -> None:
        """
        Crop and assign the corresponding bounding box image.

        Args:
            image (Union[PILImage.Image, np.ndarray]): Original image.
            xyxy (np.ndarray): Bounding box in pixel (x1, y1, x2, y2) format.
        """
        if isinstance(image, np.ndarray):
            x1, y1, x2, y2 = map(int, xyxy)
            self.image = Image(image[y1:y2, x1:x2])
        else:
            self.image = Image(image.crop(xyxy.tolist()))


class Detector:
    def __init__(
            self,
            model_path: str | Path | None = None,
            device: str = "cpu",
            conf_thresh: float = 0.25,
            iou_thresh: float = 0.45
    ):
        """
        Args:
            model_path: Path to a .pt file or None for default YOLO
            device: "cpu" or "cuda"
            conf_thresh: Minimum confidence for detections
            iou_thresh: IoU threshold for NMS
        """
        if model_path is None:
            self.model = YOLO()
        else:
            self.model_path = Path(model_path)
            self.model = YOLO(self.model_path)
        self.model.conf = conf_thresh
        self.model.iou = iou_thresh
        self.model.to(device)
        self.class_names: List[str] = list(self.model.names.values())  # {0: 'person', 1: 'bicycle', 2: 'car', ...}
        self.counts: Dict[int, int] = {}
        self.detections: List[Detection] = []

    def detect(self, image: Union[Image, PILImage.Image, np.ndarray]) -> List[Detection]:
        if isinstance(image, Image):
            image = image.image
        elif isinstance(image, PILImage.Image):
            pass
        elif isinstance(image, np.ndarray):
            pass
        else:
            raise TypeError(
                f"Unsupported image type: {type(image)}. Supported types: hexss.Image, PIL.Image, np.ndarray.")

        result = self.model(source=image, verbose=False)[0]

        self.detections.clear()
        counts: Dict[int, int] = {}
        boxes = result.boxes
        for cls, conf, xywhn, xywh, xyxyn, xyxy in zip(
                boxes.cls, boxes.conf, boxes.xywhn, boxes.xywh, boxes.xyxyn, boxes.xyxy
        ):
            cls_int = int(cls)
            counts[cls_int] = counts.get(cls_int, 0) + 1
            detection = Detection(
                idx=cls_int,
                name=self.class_names[cls_int],
                conf=float(conf),
                xywhn=xywhn.cpu().numpy(),
                xywh=xywh.cpu().numpy(),
                xyxyn=xyxyn.cpu().numpy(),
                xyxy=xyxy.cpu().numpy(),
                box=Box(size=result.orig_shape[::-1], xywhn=xywhn.cpu().numpy())
            )

            detection.set_image(image, xyxy)
            self.detections.append(detection)
            self.counts = counts  # {0: 40, 1: 30, 2: 10}
        return self.detections

    def draw_boxes(
            self,
            image: Union[Image, PILImage.Image, np.ndarray],
            thickness: int = 2,
            font_size: int = 14
    ) -> PILImage.Image:
        image = Image(image)
        draw = image.draw()
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default(font_size)

        for det in self.detections:
            x1, y1, x2, y2 = map(int, det.xyxy)
            label = f"{det.name} {det.conf:.2f}"
            draw.rectangle([x1, y1, x2, y2], outline="red", width=thickness)
            draw.text((x1, y1), label, fill="black", font=font, stroke_width=thickness, stroke_fill="white")

        return image

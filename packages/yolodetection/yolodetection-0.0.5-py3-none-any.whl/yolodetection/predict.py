import json
import uuid
from pathlib import Path
from ultralytics import YOLO


class YOLOInstance:
    def __init__(self, images, weights):
        """
        :param images: path to images
        :param weights: path to weights
        """
        self.model = YOLO(weights)
        self.inputs = images
    def detect(self, save=True):
        detections = detect(self.inputs, self.model)
        if save:
            save_as_json(detections)
        return detections

def detect(images, model, conf=0.3, iou=0.5):
    """
    Use YOLO to detect objects in images
    :param images: path to images
    :param model: YOLO model instance
    :param conf: confidence threshold
    :param iou: IOU threshold
    :return: json serialized results
    """
    results = model.predict(source=images, conf=conf, iou=iou, save=True)
    return serialize_results(results, model.names)

def serialize_results(results, classes):
    all_detections = {}
    for r in results:
        all_detections[r.path] = serialize_detection(r, classes)
    return all_detections

def serialize_detection(result, classes):
    output = []
    for box in result.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        output.append({
            "class": classes[int(box.cls[0])],
            "confidence": float(box.conf[0]),
            "bbox": [x1, y1, x2, y2]
        })
    return output

def save_as_json(data):
    output_path = Path.cwd() / "outputs" / f"{uuid.uuid4()}_detections.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Results saved to {output_path}")

yolo = YOLOInstance(Path.cwd() / "images", "models/best.pt")
yolo.detect()
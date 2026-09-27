# ============================================================
# SATQUERY AI — OBJECT DETECTION AGENT
# ============================================================

import os
import requests
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO


# ------------------------------------------------------------
# MODEL CONFIGURATION
# ------------------------------------------------------------

# YOLO model used as the baseline detector.
# NOTE:
# This is a general-purpose pretrained detector.
# It is NOT a specialised satellite/remote-sensing model.
MODEL_NAME = os.getenv("OBJECT_DETECTION_MODEL", "yolo11n.pt")

_model = None


# ------------------------------------------------------------
# LOAD MODEL
# ------------------------------------------------------------

def load_detection_model():
    """
    Load the YOLO model only when it is actually needed.
    This avoids loading the model every time the Streamlit
    application starts.
    """

    global _model

    if _model is None:
        _model = YOLO(MODEL_NAME)

    return _model


# ------------------------------------------------------------
# DOWNLOAD IMAGE
# ------------------------------------------------------------

def download_image(image_url):
    """
    Download satellite image from the URL returned by
    the Satellite Agent.
    """

    response = requests.get(
        image_url,
        timeout=30
    )

    response.raise_for_status()

    return Image.open(
        BytesIO(response.content)
    ).convert("RGB")


# ------------------------------------------------------------
# QUERY → DETECTION FILTER
# ------------------------------------------------------------

def get_requested_classes(query):
    """
    Decide which object classes are relevant to the user's query.

    These names correspond to classes available in the
    general-purpose pretrained detector.
    """

    query_lower = query.lower()

    requested = []

    if any(word in query_lower for word in [
        "car",
        "cars",
        "vehicle",
        "vehicles"
    ]):
        requested.append("car")

    if any(word in query_lower for word in [
        "bus",
        "buses"
    ]):
        requested.append("bus")

    if any(word in query_lower for word in [
        "truck",
        "trucks"
    ]):
        requested.append("truck")

    if any(word in query_lower for word in [
        "person",
        "people",
        "persons"
    ]):
        requested.append("person")

    if any(word in query_lower for word in [
        "airplane",
        "aircraft",
        "plane",
        "planes"
    ]):
        requested.append("airplane")

    if any(word in query_lower for word in [
        "boat",
        "boats",
        "ship",
        "ships"
    ]):
        requested.append("boat")

    if any(word in query_lower for word in [
        "motorcycle",
        "motorcycles",
        "bike",
        "bikes"
    ]):
        requested.append("motorcycle")

    return requested


# ------------------------------------------------------------
# RUN OBJECT DETECTION
# ------------------------------------------------------------

def run_object_detection(
    image_url,
    query,
    confidence_threshold=0.25
):
    """
    Run object detection on the satellite image.

    Returns:
        detections
        counts
        annotated_image
        image_size
        status
    """

    image = download_image(image_url)

    width, height = image.size

    model = load_detection_model()

    requested_classes = get_requested_classes(query)

    # --------------------------------------------------------
    # RUN YOLO
    # --------------------------------------------------------

    results = model.predict(
        source=image,
        conf=confidence_threshold,
        verbose=False
    )

    detections = []

    for result in results:

        boxes = result.boxes

        if boxes is None:
            continue

        for box in boxes:

            class_id = int(
                box.cls[0].item()
            )

            confidence = float(
                box.conf[0].item()
            )

            class_name = model.names[class_id]

            # ------------------------------------------------
            # FILTER IF USER REQUESTED SPECIFIC OBJECTS
            # ------------------------------------------------

            if requested_classes:

                if class_name not in requested_classes:
                    continue

            coordinates = box.xyxy[0].tolist()

            x1, y1, x2, y2 = coordinates

            detections.append({
                "object": class_name,
                "confidence": round(
                    confidence,
                    3
                ),
                "bbox": [
                    round(x1),
                    round(y1),
                    round(x2),
                    round(y2)
                ]
            })

    # --------------------------------------------------------
    # COUNT OBJECTS
    # --------------------------------------------------------

    counts = {}

    for detection in detections:

        object_name = detection["object"]

        counts[object_name] = (
            counts.get(object_name, 0) + 1
        )

    # --------------------------------------------------------
    # CREATE ANNOTATED IMAGE
    # --------------------------------------------------------

    annotated_image = image.copy()

    draw = ImageDraw.Draw(
        annotated_image
    )

    try:
        font = ImageFont.truetype(
            "arial.ttf",
            18
        )
    except:
        font = ImageFont.load_default()

    for detection in detections:

        x1, y1, x2, y2 = detection["bbox"]

        object_name = detection["object"]

        confidence = detection["confidence"]

        label = (
            f"{object_name} "
            f"{confidence:.2f}"
        )

        # Bounding box
        draw.rectangle(
            [
                x1,
                y1,
                x2,
                y2
            ],
            outline="cyan",
            width=3
        )

        # Label background
        try:

            text_box = draw.textbbox(
                (x1, y1),
                label,
                font=font
            )

            draw.rectangle(
                text_box,
                fill="black"
            )

        except:

            pass

        # Label
        draw.text(
            (x1, y1),
            label,
            fill="cyan",
            font=font
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if detections:

        status = "OBJECTS_DETECTED"

    else:

        status = "NO_OBJECTS_DETECTED"

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "agent": "Object Detection Agent",
        "status": status,
        "query": query,
        "image_size": f"{width} × {height}",
        "requested_classes": requested_classes,
        "detections": detections,
        "counts": counts,
        "total_objects": len(detections),
        "annotated_image": annotated_image
    }


# ============================================================
# TEST FUNCTION
# ============================================================

if __name__ == "__main__":

    print(
        "SATQuery AI — Object Detection Agent"
    )

    print(
        "Model:",
        MODEL_NAME
    )
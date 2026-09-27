# ============================================================
# SATQUERY AI — VISION AGENT
# ============================================================

import os
import requests

from PIL import Image
from io import BytesIO

from object_detection_agent import run_object_detection


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)

_gemini_client = None


# ============================================================
# DOWNLOAD SATELLITE IMAGE
# ============================================================

def download_satellite_image(image_url):

    response = requests.get(
        image_url,
        timeout=30
    )

    response.raise_for_status()

    return Image.open(
        BytesIO(response.content)
    ).convert("RGB")


# ============================================================
# QUERY → VLM PROMPT
# ============================================================

def build_vlm_prompt(query):

    return f"""
You are a satellite-image analysis assistant.

Analyze the provided satellite image and answer the user's
query using ONLY visual evidence that can reasonably be
observed in the image.

User query:
{query}

Your response should contain:

1. A short visual summary.
2. Important visual findings.
3. Any uncertainty or limitations.
4. A confidence level:
   HIGH, MEDIUM, or LOW.

Do not invent objects, locations, measurements, or facts that
cannot be supported by the image.
"""


# ============================================================
# GEMINI VLM
# ============================================================

def _run_vlm(image_bytes, query):

    if not GEMINI_API_KEY:

        return {
            "status": "VLM_NOT_CONFIGURED",
            "summary": (
                "Gemini API key is not configured."
            ),
            "findings": [],
            "confidence": "LOW"
        }

    try:

        from google import genai

        global _gemini_client

        if _gemini_client is None:

            _gemini_client = genai.Client(
                api_key=GEMINI_API_KEY
            )

        prompt = build_vlm_prompt(query)

        response = _gemini_client.interactions.create(

            model=GEMINI_MODEL,

            input=[
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image",
                    "data": image_bytes,
                    "mime_type": "image/jpeg"
                }
            ]
        )

        output = response.output_text.strip()

        findings = []

        for line in output.splitlines():

            line = line.strip()

            if line.startswith("-"):

                findings.append(
                    line.lstrip("-").strip()
                )

            elif line.startswith("•"):

                findings.append(
                    line.lstrip("•").strip()
                )

        if not findings:

            findings = [
                output
            ]

        # ----------------------------------------------------
        # CONFIDENCE EXTRACTION
        # ----------------------------------------------------

        confidence = "MEDIUM"

        output_upper = output.upper()

        if "HIGH" in output_upper:
            confidence = "HIGH"

        elif "LOW" in output_upper:
            confidence = "LOW"

        return {

            "status": "VLM_ANALYZED",

            "summary": output,

            "findings": findings,

            "confidence": confidence

        }

    except Exception as e:

        return {

            "status": "VLM_ERROR",

            "summary": (
                "Vision-language analysis failed."
            ),

            "findings": [
                str(e)
            ],

            "confidence": "LOW"

        }


# ============================================================
# VISION AGENT
# ============================================================

def run_vision_agent(
    image_url,
    query,
    agent_type="VLM Reasoning"
):

    # --------------------------------------------------------
    # DOWNLOAD IMAGE
    # --------------------------------------------------------

    image = download_satellite_image(
        image_url
    )

    width, height = image.size


    # ========================================================
    # OBJECT DETECTION
    # ========================================================

    if agent_type == "Object Detection":

        try:

            detection_result = run_object_detection(

                image_url=image_url,

                query=query

            )

            findings = []

            # -----------------------------------------------
            # DETECTION SUMMARY
            # -----------------------------------------------

            if detection_result["total_objects"] > 0:

                findings.append(
                    f"Detected "
                    f"{detection_result['total_objects']} "
                    f"object(s) in the scene."
                )

            else:

                findings.append(
                    "No supported objects were detected."
                )


            # -----------------------------------------------
            # OBJECT COUNTS
            # -----------------------------------------------

            for object_name, count in (
                detection_result["counts"].items()
            ):

                findings.append(
                    f"{object_name}: {count}"
                )


            # -----------------------------------------------
            # RETURN
            # -----------------------------------------------

            return {

                "agent": "Object Detection",

                "query": query,

                "image_size": (
                    f"{width} × {height}"
                ),

                "status": (
                    detection_result["status"]
                ),

                "findings": findings,

                "detections": (
                    detection_result["detections"]
                ),

                "counts": (
                    detection_result["counts"]
                ),

                "total_objects": (
                    detection_result["total_objects"]
                ),

                "annotated_image": (
                    detection_result["annotated_image"]
                ),

                "confidence": (
                    "PRELIMINARY"
                    if detection_result["total_objects"]
                    else "LOW"
                )

            }

        except Exception as e:

            return {

                "agent": "Object Detection",

                "query": query,

                "image_size": (
                    f"{width} × {height}"
                ),

                "status": "DETECTION_ERROR",

                "findings": [
                    f"Object detection failed: {str(e)}"
                ],

                "detections": [],

                "counts": {},

                "total_objects": 0,

                "annotated_image": None,

                "confidence": "LOW"

            }


    # ========================================================
    # SEGMENTATION
    # ========================================================

    elif agent_type == "Segmentation":

        return {

            "agent": "Segmentation",

            "query": query,

            "image_size": (
                f"{width} × {height}"
            ),

            "status": "IMAGE_RECEIVED",

            "findings": [

                "Segmentation module selected.",

                "Land-cover / region segmentation "
                "will analyse the scene."

            ]

        }


    # ========================================================
    # CHANGE DETECTION
    # ========================================================

    elif agent_type == "Change Detection":

        return {

            "agent": "Change Detection",

            "query": query,

            "image_size": (
                f"{width} × {height}"
            ),

            "status": "IMAGE_RECEIVED",

            "findings": [

                "Change detection module selected.",

                "A second temporal satellite scene "
                "is required for true change analysis."

            ]

        }


    # ========================================================
    # OCR
    # ========================================================

    elif agent_type == "OCR":

        return {

            "agent": "OCR",

            "query": query,

            "image_size": (
                f"{width} × {height}"
            ),

            "status": "IMAGE_RECEIVED",

            "findings": [

                "OCR module selected.",

                "Text extraction requires sufficiently "
                "high-resolution imagery."

            ]

        }


    # ========================================================
    # VLM REASONING
    # ========================================================

    else:

        try:

            # Convert PIL image to JPEG bytes

            image_buffer = BytesIO()

            image.save(
                image_buffer,
                format="JPEG"
            )

            image_bytes = (
                image_buffer.getvalue()
            )


            vlm_result = _run_vlm(
                image_bytes,
                query
            )


            return {

                "agent": "VLM Reasoning",

                "query": query,

                "image_size": (
                    f"{width} × {height}"
                ),

                "status": (
                    vlm_result["status"]
                ),

                "findings": (
                    vlm_result["findings"]
                ),

                "summary": (
                    vlm_result["summary"]
                ),

                "confidence": (
                    vlm_result["confidence"]
                )

            }

        except Exception as e:

            return {

                "agent": "VLM Reasoning",

                "query": query,

                "image_size": (
                    f"{width} × {height}"
                ),

                "status": "VLM_ERROR",

                "findings": [
                    str(e)
                ],

                "summary": (
                    "VLM analysis failed."
                ),

                "confidence": "LOW"

            }
# ============================================================
# SATQUERY AI — EVIDENCE AGENT
# ============================================================

def build_evidence(
    query,
    query_analysis,
    vision_result,
    satellite_data,
    change_result=None
):
    """
    Evidence Agent

    Combines:
    - User query
    - Query Intelligence
    - Satellite metadata
    - Vision Agent findings
    - Object detection
    - Change Detection
    - Confidence

    into one structured evidence package
    for the Answer / Reasoning Agent.
    """

    # ========================================================
    # SAFETY: HANDLE MISSING DATA
    # ========================================================

    if not isinstance(query_analysis, dict):
        query_analysis = {}

    if not isinstance(vision_result, dict):
        vision_result = {}

    if not isinstance(satellite_data, dict):
        satellite_data = {}

    if not isinstance(change_result, dict):
        change_result = {}


    # ========================================================
    # QUERY INFORMATION
    # ========================================================

    agent = query_analysis.get(
        "agent",
        "Unknown"
    )

    reason = query_analysis.get(
        "reason",
        "No routing reason available."
    )

    task = query_analysis.get(
        "task",
        "No task information available."
    )


    # ========================================================
    # SATELLITE INFORMATION
    # ========================================================

    scene_id = satellite_data.get(
        "scene_id",
        "Unknown"
    )

    observation_date = satellite_data.get(
        "date",
        "Unknown"
    )

    cloud_cover = satellite_data.get(
        "cloud_cover",
        "Unknown"
    )

    image_url = satellite_data.get(
        "image_url",
        None
    )


    # ========================================================
    # VISION INFORMATION
    # ========================================================

    vision_status = vision_result.get(
        "status",
        "UNKNOWN"
    )

    vision_agent = vision_result.get(
        "agent",
        agent
    )

    findings = vision_result.get(
        "findings",
        []
    )

    vision_confidence = vision_result.get(
        "confidence",
        "UNKNOWN"
    )


    # ========================================================
    # OBJECT DETECTION
    # ========================================================

    detections = vision_result.get(
        "detections",
        []
    )

    object_counts = vision_result.get(
        "counts",
        {}
    )

    total_objects = vision_result.get(
        "total_objects",
        len(detections)
    )


    # ========================================================
    # CHANGE DETECTION INFORMATION
    # ========================================================

    change_status = change_result.get(
        "status",
        "NOT_AVAILABLE"
    )

    change_confidence = change_result.get(
        "confidence",
        "UNKNOWN"
    )

    change_finding = change_result.get(
        "finding",
        "No change-detection finding available."
    )

    change_percentage = change_result.get(
        "change_percentage",
        0
    )

    raw_change_percentage = change_result.get(
        "raw_change_percentage",
        0
    )

    region_count = change_result.get(
        "region_count",
        0
    )

    change_details = change_result.get(
        "change_details",
        []
    )

    change_boxes = change_result.get(
        "boxes",
        []
    )


    # ========================================================
    # BUILD CHANGE EVIDENCE
    # ========================================================

    change_available = bool(
        change_result
    )

    change_evidence = {

        "available": change_available,

        "status": change_status,

        "confidence": change_confidence,

        "finding": change_finding,

        "changed_area_percentage": change_percentage,

        "raw_changed_area_percentage": (
            raw_change_percentage
        ),

        "changed_region_count": region_count,

        "regions": change_details,

        "bounding_boxes": change_boxes

    }


    # ========================================================
    # BUILD STRUCTURED EVIDENCE
    # ========================================================

    evidence = {

        # ----------------------------------------------------
        # USER QUERY
        # ----------------------------------------------------

        "query": query,


        # ----------------------------------------------------
        # QUERY UNDERSTANDING
        # ----------------------------------------------------

        "query_understanding": {

            "selected_agent": agent,

            "reason": reason,

            "task": task

        },


        # ----------------------------------------------------
        # SATELLITE EVIDENCE
        # ----------------------------------------------------

        "satellite_evidence": {

            "scene_id": scene_id,

            "observation_date": observation_date,

            "cloud_cover": cloud_cover,

            "image_available": (
                image_url is not None
            )

        },


        # ----------------------------------------------------
        # VISION EVIDENCE
        # ----------------------------------------------------

        "vision_evidence": {

            "agent": vision_agent,

            "status": vision_status,

            "findings": findings,

            "confidence": vision_confidence

        },


        # ----------------------------------------------------
        # OBJECT DETECTION EVIDENCE
        # ----------------------------------------------------

        "object_detection_evidence": {

            "detection_available": (
                len(detections) > 0
            ),

            "total_objects": total_objects,

            "object_counts": object_counts,

            "detections": detections

        },


        # ----------------------------------------------------
        # CHANGE DETECTION EVIDENCE
        # ----------------------------------------------------

        "change_detection_evidence": change_evidence,


        # ----------------------------------------------------
        # GENERAL STATUS
        # ----------------------------------------------------

        "evidence_status": "AVAILABLE"

    }


    # ========================================================
    # OVERALL CONFIDENCE
    # ========================================================

    confidence_values = []


    # Vision confidence
    if vision_confidence in [
        "HIGH",
        "MEDIUM",
        "LOW"
    ]:
        confidence_values.append(
            vision_confidence
        )


    # Change confidence
    if change_confidence in [
        "HIGH",
        "MEDIUM",
        "LOW"
    ]:
        confidence_values.append(
            change_confidence
        )


    # --------------------------------------------------------
    # Calculate overall confidence
    # --------------------------------------------------------

    if not confidence_values:

        if image_url:

            evidence["confidence"] = "LOW"

        else:

            evidence["confidence"] = "INSUFFICIENT"

    elif "LOW" in confidence_values:

        evidence["confidence"] = "LOW"

    elif "MEDIUM" in confidence_values:

        evidence["confidence"] = "PRELIMINARY"

    else:

        evidence["confidence"] = "PRELIMINARY"


    # ========================================================
    # EVIDENCE SOURCES
    # ========================================================

    evidence["sources"] = [

        "Natural-language user query",

        "Query Intelligence",

        "Satellite imagery metadata",

        "Retrieved satellite scene",

        "Vision Agent output",

        "Object Detection Agent output",

        "Change Detection Agent output"

    ]


    # ========================================================
    # HUMAN-READABLE SUMMARY
    # ========================================================

    summary_parts = []


    # Query
    summary_parts.append(
        f"User query: {query}"
    )


    # Vision
    if findings:

        if isinstance(findings, list):

            for finding in findings[:5]:

                summary_parts.append(
                    f"Vision finding: {finding}"
                )

        else:

            summary_parts.append(
                f"Vision finding: {findings}"
            )


    # Objects
    if total_objects > 0:

        summary_parts.append(
            f"Objects detected: {total_objects}"
        )


    # Changes
    if change_available:

        if change_status == "CHANGE_DETECTED":

            summary_parts.append(

                f"Change detection identified "
                f"{region_count} significant region(s), "
                f"covering approximately "
                f"{change_percentage:.2f}% "
                f"of the image."
            )

            for region in change_details[:5]:

                location = region.get(
                    "location",
                    "Unknown location"
                )

                area = region.get(
                    "area_percentage",
                    0
                )

                summary_parts.append(

                    f"Changed region: {location}, "
                    f"approximately {area:.2f}% "
                    f"of the image."
                )

        else:

            summary_parts.append(
                "No major change was detected."
            )


    evidence["human_readable_summary"] = (
        "\n".join(summary_parts)
    )


    # ========================================================
    # DEBUG OUTPUT
    # ========================================================

    print()
    print("=" * 70)
    print("SATQUERY AI — EVIDENCE AGENT")
    print("=" * 70)

    print(
        "Query:",
        query
    )

    print(
        "Selected Agent:",
        agent
    )

    print(
        "Vision Status:",
        vision_status
    )

    print(
        "Objects:",
        total_objects
    )

    print(
        "Change Status:",
        change_status
    )

    print(
        "Changed Regions:",
        region_count
    )

    print(
        "Changed Area:",
        f"{change_percentage:.2f}%"
    )

    print(
        "Overall Confidence:",
        evidence.get(
            "confidence",
            "UNKNOWN"
        )
    )

    print("=" * 70)
    print()


    return evidence


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("SATQuery AI — Evidence Agent")
    print("=" * 70)

    test_result = build_evidence(

        query="What changed between these satellite images?",

        query_analysis={
            "agent": "Change Detection Agent",
            "reason": "User is asking for temporal changes.",
            "task": "Change detection"
        },

        vision_result={
            "status": "VLM_ANALYZED",
            "agent": "Vision Agent",
            "findings": [
                "Satellite scene analyzed."
            ],
            "confidence": "MEDIUM",
            "detections": [],
            "counts": {},
            "total_objects": 0
        },

        satellite_data={
            "scene_id": "TEST_SCENE",
            "date": "2026-01-01",
            "cloud_cover": 0,
            "image_url": "https://example.com/image.jpg"
        },

        change_result={
            "status": "CHANGE_DETECTED",
            "confidence": "MEDIUM",
            "finding": "Changed regions detected.",
            "change_percentage": 4.5,
            "region_count": 2,
            "change_details": [
                {
                    "region": "Change 1",
                    "location": "Center-Right",
                    "area_percentage": 2.1
                }
            ],
            "boxes": []
        }
    )

    print(
        test_result["human_readable_summary"]
    )

    print()
    print("Evidence Agent loaded successfully.")
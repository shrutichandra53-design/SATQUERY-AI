# ============================================================
# SATQUERY AI - QUERY ROUTER
# ============================================================


def understand_query(query):

    """
    Understand the user's natural-language query
    and decide which specialist agent should handle it.
    """

    text = query.lower().strip()

    # --------------------------------------------------------
    # CHANGE DETECTION
    # --------------------------------------------------------

    change_words = [
        "change",
        "changed",
        "difference",
        "before and after",
        "new construction",
        "newly constructed",
        "demolished",
        "increased",
        "decreased",
        "growth",
        "development",
        "compare"
    ]

    if any(word in text for word in change_words):

        return {
            "agent": "CHANGE DETECTION",
            "reason": "The query asks about changes over time.",
            "task": "Compare satellite observations."
        }


    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    ocr_words = [
        "text",
        "read",
        "writing",
        "sign",
        "board",
        "label",
        "number",
        "letters",
        "ocr"
    ]

    if any(word in text for word in ocr_words):

        return {
            "agent": "OCR AGENT",
            "reason": "The query requires reading text.",
            "task": "Extract visible text from the image."
        }


    # --------------------------------------------------------
    # OBJECT DETECTION
    # --------------------------------------------------------

    object_words = [
        "how many",
        "count",
        "buildings",
        "cars",
        "vehicles",
        "airplanes",
        "aircraft",
        "ships",
        "houses",
        "people",
        "objects",
        "find buildings",
        "detect"
    ]

    if any(word in text for word in object_words):

        return {
            "agent": "OBJECT DETECTION",
            "reason": "The query requires locating or counting objects.",
            "task": "Detect relevant objects in the satellite image."
        }


    # --------------------------------------------------------
    # SEGMENTATION
    # --------------------------------------------------------

    segmentation_words = [
        "area",
        "region",
        "land",
        "water",
        "river",
        "lake",
        "road",
        "forest",
        "vegetation",
        "building area",
        "land cover",
        "segment",
        "boundary"
    ]

    if any(word in text for word in segmentation_words):

        return {
            "agent": "SEGMENTATION AGENT",
            "reason": "The query requires identifying image regions.",
            "task": "Generate a pixel-level region mask."
        }


    # --------------------------------------------------------
    # VLM REASONING
    # --------------------------------------------------------

    reasoning_words = [
        "describe",
        "what is",
        "what do you see",
        "explain",
        "analyze",
        "why",
        "identify",
        "summarize",
        "scene"
    ]

    if any(word in text for word in reasoning_words):

        return {
            "agent": "VLM REASONING",
            "reason": "The query requires visual reasoning.",
            "task": "Interpret the satellite image and answer the question."
        }


    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    return {
        "agent": "VLM REASONING",
        "reason": "No specific specialist was identified.",
        "task": "Use general visual reasoning to answer the query."
    }
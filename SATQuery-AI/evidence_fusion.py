# ============================================================
# SATQUERY AI — EVIDENCE FUSION
# ============================================================

def fuse_evidence(agent_results):
    """
    Combine outputs from multiple specialist agents.

    Input:
        agent_results = list of results returned by Vision Agents

    Output:
        Structured fused evidence
    """

    evidence = []

    # --------------------------------------------------------
    # 1. COLLECT FINDINGS
    # --------------------------------------------------------

    for result in agent_results:

        agent_name = result.get(
            "agent",
            "Unknown Agent"
        )

        findings = result.get(
            "findings",
            []
        )

        confidence = result.get(
            "confidence",
            "LOW"
        )

        for finding in findings:

            evidence.append({
                "source": agent_name,
                "finding": finding,
                "confidence": confidence
            })

    # --------------------------------------------------------
    # 2. COLLECT OBJECT DETECTIONS
    # --------------------------------------------------------

    object_counts = {}

    for result in agent_results:

        counts = result.get(
            "counts",
            {}
        )

        for object_name, count in counts.items():

            object_counts[object_name] = (
                object_counts.get(object_name, 0)
                + count
            )

    # --------------------------------------------------------
    # 3. REMOVE DUPLICATE FINDINGS
    # --------------------------------------------------------

    unique_evidence = []

    seen = set()

    for item in evidence:

        key = (
            item["source"],
            item["finding"]
        )

        if key not in seen:

            seen.add(key)

            unique_evidence.append(item)

    # --------------------------------------------------------
    # 4. DETERMINE OVERALL CONFIDENCE
    # --------------------------------------------------------

    confidence_values = [
        item["confidence"]
        for item in unique_evidence
    ]

    if not confidence_values:

        overall_confidence = "LOW"

    elif all(
        confidence == "HIGH"
        for confidence in confidence_values
    ):

        overall_confidence = "HIGH"

    elif any(
        confidence == "MEDIUM"
        for confidence in confidence_values
    ):

        overall_confidence = "MEDIUM"

    else:

        overall_confidence = "LOW"

    # --------------------------------------------------------
    # 5. RETURN FUSED EVIDENCE
    # --------------------------------------------------------

    return {

        "evidence": unique_evidence,

        "object_counts": object_counts,

        "total_evidence_items": len(
            unique_evidence
        ),

        "confidence": overall_confidence,

        "status": "EVIDENCE_FUSED"
    }


# ============================================================
# BUILD HUMAN-READABLE EVIDENCE
# ============================================================

def build_evidence_summary(fused_result):
    """
    Convert fused evidence into a simple text summary.
    """

    lines = []

    # --------------------------------------------------------
    # OBJECT COUNTS
    # --------------------------------------------------------

    object_counts = fused_result.get(
        "object_counts",
        {}
    )

    if object_counts:

        lines.append(
            "Detected objects:"
        )

        for object_name, count in object_counts.items():

            lines.append(
                f"- {object_name}: {count}"
            )

    # --------------------------------------------------------
    # OTHER FINDINGS
    # --------------------------------------------------------

    evidence = fused_result.get(
        "evidence",
        []
    )

    if evidence:

        lines.append(
            "\nVisual findings:"
        )

        for item in evidence:

            lines.append(
                f"- [{item['source']}] "
                f"{item['finding']}"
            )

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    lines.append(
        f"\nOverall confidence: "
        f"{fused_result.get('confidence', 'LOW')}"
    )

    return "\n".join(lines)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    sample_results = [

        {
            "agent": "Object Detection Agent",

            "findings": [
                "Detected 5 object(s) in the scene.",
                "car: 5"
            ],

            "counts": {
                "car": 5
            },

            "confidence": "HIGH"
        },

        {
            "agent": "VLM Reasoning",

            "findings": [
                "Several vehicles are visible."
            ],

            "confidence": "MEDIUM"
        }
    ]

    fused = fuse_evidence(
        sample_results
    )

    print(
        build_evidence_summary(
            fused
        )
    )
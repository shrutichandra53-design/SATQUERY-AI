# ============================================================
# SATQUERY AI — ANSWER AGENT
# ============================================================

import os
import json

from google import genai


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Use a known Gemini Flash model.
# You can override this from .env if required.
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)

_client = None


# ============================================================
# INITIALIZE GEMINI
# ============================================================

def get_gemini_client():

    global _client

    if _client is None:

        # Read the key again in case .env was loaded
        # after this module was imported.
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. "
                "Please check your .env file."
            )

        _client = genai.Client(
            api_key=api_key
        )

    return _client


# ============================================================
# SAFE TEXT CONVERSION
# ============================================================

def safe_text(value):

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return str(value).strip()


# ============================================================
# FORMAT EVIDENCE
# ============================================================

def format_evidence(evidence):

    if not evidence:
        return "No evidence available."

    lines = []

    for item in evidence:

        if isinstance(item, dict):

            source = safe_text(
                item.get(
                    "source",
                    "Unknown Source"
                )
            )

            finding = safe_text(
                item.get(
                    "finding",
                    ""
                )
            )

            confidence = safe_text(
                item.get(
                    "confidence",
                    "LOW"
                )
            )

            if finding:

                lines.append(
                    f"Source: {source}\n"
                    f"Finding: {finding}\n"
                    f"Confidence: {confidence}"
                )

        else:

            text = safe_text(item)

            if text:
                lines.append(
                    f"Finding: {text}"
                )

    if not lines:
        return "No usable evidence available."

    return "\n\n".join(lines)


# ============================================================
# FORMAT OBJECT COUNTS
# ============================================================

def format_object_counts(object_counts):

    if not object_counts:
        return "No detected object counts available."

    lines = []

    for object_name, count in object_counts.items():

        object_name = safe_text(
            object_name
        )

        lines.append(
            f"{object_name}: {count}"
        )

    return "\n".join(lines)


# ============================================================
# FORMAT CHANGE DETECTION
# ============================================================

def format_change_detection(fused_result):

    if not isinstance(fused_result, dict):
        return "No change-detection information available."

    change_count = fused_result.get(
        "change_count",
        None
    )

    changed_area = fused_result.get(
        "changed_area_percentage",
        None
    )

    finding = fused_result.get(
        "change_finding",
        ""
    )

    change_details = fused_result.get(
        "change_details",
        []
    )

    lines = []

    if change_count is not None:

        lines.append(
            f"Detected change regions: {change_count}"
        )

    if changed_area is not None:

        lines.append(
            f"Changed area percentage: {changed_area}"
        )

    if finding:

        lines.append(
            f"Change finding: {safe_text(finding)}"
        )

    if isinstance(change_details, list):

        for detail in change_details:

            if isinstance(detail, dict):

                label = safe_text(
                    detail.get(
                        "label",
                        "Change"
                    )
                )

                description = safe_text(
                    detail.get(
                        "description",
                        ""
                    )
                )

                if description:

                    lines.append(
                        f"{label}: {description}"
                    )

    if not lines:

        return "No change-detection information available."

    return "\n".join(lines)


# ============================================================
# BUILD DESCRIPTIVE ANSWER PROMPT
# ============================================================

def build_answer_prompt(
    query,
    fused_result
):

    if not isinstance(fused_result, dict):
        fused_result = {}

    evidence = fused_result.get(
        "evidence",
        []
    )

    object_counts = fused_result.get(
        "object_counts",
        {}
    )

    confidence = safe_text(
        fused_result.get(
            "confidence",
            "LOW"
        )
    ).upper()

    if confidence not in {
        "HIGH",
        "MEDIUM",
        "LOW"
    }:

        confidence = "LOW"

    evidence_text = format_evidence(
        evidence
    )

    object_text = format_object_counts(
        object_counts
    )

    change_text = format_change_detection(
        fused_result
    )

    # --------------------------------------------------------
    # DESCRIPTIVE PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are the final Answer Agent of SATQuery AI.

SATQuery AI is an agentic satellite-image analysis system.

Specialist components have already analyzed the satellite
imagery. You must now convert their available evidence into
a clear, descriptive and user-friendly answer.

============================================================
USER QUERY
============================================================

{query}


============================================================
AVAILABLE EVIDENCE
============================================================

{evidence_text}


============================================================
DETECTED OBJECTS
============================================================

{object_text}


============================================================
CHANGE DETECTION INFORMATION
============================================================

{change_text}


============================================================
OVERALL CONFIDENCE
============================================================

{confidence}


============================================================
YOUR TASK
============================================================

Answer the user's query using ONLY the information provided
above.

The answer should sound like a human expert explaining the
satellite-image analysis to the user.

Do NOT simply repeat the evidence.

Instead, combine the relevant findings into a meaningful
description.

For example, if the evidence says that several vehicles were
detected, explain the observation naturally.

If the query asks about changes between two images, describe
what the change-detection evidence indicates.

If object counts are available, use the exact counts.

If multiple relevant findings are available, connect them
into one coherent explanation.

============================================================
IMPORTANT RULES
============================================================

1. Answer the user's question directly.

2. Be descriptive but easy to understand.

3. Use ONLY the supplied evidence.

4. Never invent objects, numbers, dates, locations,
   measurements or events.

5. Never guess what caused a detected change unless the
   evidence explicitly states the cause.

6. If the evidence is insufficient, clearly say so.

7. If confidence is MEDIUM or LOW, communicate that the
   result should be interpreted with some uncertainty.

8. Do not mention prompts or internal reasoning.

9. Do not describe chain-of-thought.

10. Do not claim that the system can see something that was
    not provided by the specialist results.

11. Object counts must remain exactly as provided.

12. The final answer should normally be 2 to 5 sentences.

13. For a complex query, the answer can be slightly longer.

14. The evidence field should explain which available
    findings support the answer.

15. Return ONLY valid JSON.

============================================================
RETURN FORMAT
============================================================

Return exactly:

{{
    "answer": "A clear descriptive answer to the user's query.",
    "evidence": "A concise explanation of the evidence supporting the answer.",
    "confidence": "{confidence}"
}}

The confidence value must be exactly:

HIGH
MEDIUM
LOW

Do not put the JSON inside markdown code fences.
"""


    return prompt


# ============================================================
# PARSE GEMINI RESPONSE
# ============================================================

def parse_gemini_response(response):

    raw_text = getattr(
        response,
        "text",
        None
    )

    if not raw_text:

        return {
            "answer": (
                "The Answer Agent did not receive "
                "a response from Gemini."
            ),
            "evidence": (
                "No language-model response was received."
            ),
            "confidence": "LOW"
        }

    raw_text = raw_text.strip()

    # --------------------------------------------------------
    # Remove markdown fences if Gemini adds them
    # --------------------------------------------------------

    if raw_text.startswith("```"):

        raw_text = raw_text.replace(
            "```json",
            "",
            1
        )

        raw_text = raw_text.replace(
            "```",
            ""
        )

        raw_text = raw_text.strip()

    # --------------------------------------------------------
    # Try JSON parsing
    # --------------------------------------------------------

    try:

        data = json.loads(
            raw_text
        )

        if not isinstance(data, dict):

            raise ValueError(
                "Response is not a JSON object."
            )

        answer = safe_text(
            data.get(
                "answer",
                ""
            )
        )

        evidence = safe_text(
            data.get(
                "evidence",
                ""
            )
        )

        confidence = safe_text(
            data.get(
                "confidence",
                "LOW"
            )
        ).upper()

        if confidence not in {
            "HIGH",
            "MEDIUM",
            "LOW"
        }:

            confidence = "LOW"

        if not answer:

            answer = (
                "There is not enough evidence "
                "to answer the query confidently."
            )

        if not evidence:

            evidence = (
                "The answer is based on the available "
                "satellite-image analysis evidence."
            )

        return {
            "answer": answer,
            "evidence": evidence,
            "confidence": confidence
        }

    except Exception:

        # ----------------------------------------------------
        # Gemini sometimes returns normal text.
        # Keep that text instead of throwing it away.
        # ----------------------------------------------------

        return {
            "answer": raw_text,
            "evidence": (
                "The answer was generated from the "
                "available fused satellite-image evidence."
            ),
            "confidence": "LOW"
        }


# ============================================================
# GENERATE FINAL ANSWER
# ============================================================

def generate_answer(
    query,
    fused_result
):

    if not isinstance(fused_result, dict):

        fused_result = {}

    try:

        # ----------------------------------------------------
        # Gemini client
        # ----------------------------------------------------

        client = get_gemini_client()

        # ----------------------------------------------------
        # Build prompt
        # ----------------------------------------------------

        prompt = build_answer_prompt(
            query=query,
            fused_result=fused_result
        )

        # ----------------------------------------------------
        # Gemini generation
        # ----------------------------------------------------

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        # ----------------------------------------------------
        # Parse response
        # ----------------------------------------------------

        parsed = parse_gemini_response(
            response
        )

        # ----------------------------------------------------
        # Preserve fused confidence
        # ----------------------------------------------------

        original_confidence = safe_text(
            fused_result.get(
                "confidence",
                parsed.get(
                    "confidence",
                    "LOW"
                )
            )
        ).upper()

        if original_confidence not in {
            "HIGH",
            "MEDIUM",
            "LOW"
        }:

            original_confidence = (
                parsed.get(
                    "confidence",
                    "LOW"
                )
            )

        # ----------------------------------------------------
        # Return final result
        # ----------------------------------------------------

        return {

            "agent":
                "Answer Agent",

            "status":
                "ANSWER_GENERATED",

            "query":
                query,

            "answer":
                parsed.get(
                    "answer",
                    "Unable to generate a final answer."
                ),

            "evidence":
                parsed.get(
                    "evidence",
                    ""
                ),

            "confidence":
                original_confidence,

            "object_counts":
                fused_result.get(
                    "object_counts",
                    {}
                )
        }

    except Exception as e:

        # ----------------------------------------------------
        # Return visible error information
        # ----------------------------------------------------

        return {

            "agent":
                "Answer Agent",

            "status":
                "ANSWER_GENERATION_FAILED",

            "query":
                query,

            "answer":
                "I could not generate the final answer.",

            "evidence":
                (
                    "The Answer Agent encountered an error "
                    "while processing the satellite-image "
                    "evidence."
                ),

            "confidence":
                "LOW",

            "object_counts":
                fused_result.get(
                    "object_counts",
                    {}
                ),

            "error":
                str(e)
        }


# ============================================================
# SIMPLE ANSWER BUILDER
# ============================================================

def build_simple_answer(
    query,
    fused_result
):

    if not isinstance(fused_result, dict):

        fused_result = {}

    object_counts = fused_result.get(
        "object_counts",
        {}
    )

    evidence = fused_result.get(
        "evidence",
        []
    )

    confidence = safe_text(
        fused_result.get(
            "confidence",
            "LOW"
        )
    ).upper()

    # --------------------------------------------------------
    # OBJECT COUNT ANSWER
    # --------------------------------------------------------

    if object_counts:

        parts = []

        for object_name, count in object_counts.items():

            parts.append(
                f"{count} {object_name}"
            )

        if len(parts) == 1:

            answer = (
                "The satellite image analysis detected "
                + parts[0]
                + "."
            )

        else:

            answer = (
                "The satellite image analysis detected "
                + ", ".join(parts)
                + "."
            )

        evidence_text = (
            "This answer is based on the object "
            "detections produced by the image analysis."
        )

    # --------------------------------------------------------
    # EVIDENCE ANSWER
    # --------------------------------------------------------

    elif evidence:

        first_evidence = evidence[0]

        if isinstance(
            first_evidence,
            dict
        ):

            answer = safe_text(
                first_evidence.get(
                    "finding",
                    ""
                )
            )

        else:

            answer = safe_text(
                first_evidence
            )

        evidence_text = (
            "This answer is based on the available "
            "satellite-image analysis evidence."
        )

        if not answer:

            answer = (
                "There is not enough evidence "
                "to answer the query confidently."
            )

    # --------------------------------------------------------
    # NO EVIDENCE
    # --------------------------------------------------------

    else:

        answer = (
            "There is not enough evidence "
            "to answer the query confidently."
        )

        evidence_text = (
            "No usable satellite-image evidence "
            "was available."
        )

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {

        "agent":
            "Answer Agent",

        "status":
            "SIMPLE_ANSWER_GENERATED",

        "query":
            query,

        "answer":
            answer,

        "evidence":
            evidence_text,

        "confidence":
            confidence,

        "object_counts":
            object_counts
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    sample_fused_result = {

        "evidence": [

            {
                "source":
                    "Object Detection Agent",

                "finding":
                    "Detected 5 cars in the satellite image.",

                "confidence":
                    "HIGH"
            },

            {
                "source":
                    "VLM Reasoning",

                "finding":
                    "Several vehicles are visible in the analyzed area.",

                "confidence":
                    "MEDIUM"
            }

        ],

        "object_counts": {

            "car": 5

        },

        "confidence":
            "MEDIUM"
    }

    print()
    print("================================================")
    print("SATQUERY AI — ANSWER AGENT TEST")
    print("================================================")

    result = generate_answer(
        query="How many cars are visible?",
        fused_result=sample_fused_result
    )

    print()

    print("Status:")
    print(
        result.get(
            "status"
        )
    )

    print()

    print("Answer:")
    print(
        result.get(
            "answer"
        )
    )

    print()

    print("Evidence:")
    print(
        result.get(
            "evidence"
        )
    )

    print()

    print("Object Counts:")
    print(
        result.get(
            "object_counts"
        )
    )

    print()

    print("Confidence:")
    print(
        result.get(
            "confidence"
        )
    )

    if result.get("error"):

        print()

        print("ERROR:")
        print(
            result.get(
                "error"
            )
        )

    print()
    print("================================================")
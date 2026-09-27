
# ============================================================
# SATQUERY AI — AGENTIC ORCHESTRATOR
# ============================================================

from vision_agent import run_vision_agent
from evidence_fusion import fuse_evidence
from answer_agent import generate_answer


# ============================================================
# QUERY UNDERSTANDING
# ============================================================

def understand_query(query):

    q = query.lower()

    agents = []

    # --------------------------------------------------------
    # OBJECT DETECTION
    # --------------------------------------------------------

    object_words = [
        "car", "cars",
        "vehicle", "vehicles",
        "bus", "buses",
        "truck", "trucks",
        "airplane", "aircraft",
        "plane", "planes",
        "boat", "boats",
        "ship", "ships",
        "person", "people",
        "persons",
        "motorcycle", "motorcycles",
        "bike", "bikes",
        "object", "objects",
        "count", "how many"
    ]

    if any(word in q for word in object_words):
        agents.append("Object Detection")


    # --------------------------------------------------------
    # SEGMENTATION
    # --------------------------------------------------------

    segmentation_words = [
        "land cover",
        "land-cover",
        "vegetation",
        "forest",
        "forests",
        "water body",
        "water bodies",
        "river",
        "rivers",
        "road",
        "roads",
        "building",
        "buildings",
        "area",
        "region",
        "segment",
        "segmentation"
    ]

    if any(word in q for word in segmentation_words):
        agents.append("Segmentation")


    # --------------------------------------------------------
    # CHANGE DETECTION
    # --------------------------------------------------------

    change_words = [
        "change",
        "changed",
        "changes",
        "difference",
        "differences",
        "before and after",
        "compare",
        "comparison",
        "compare images",
        "temporal",
        "development",
        "growth",
        "increase",
        "decrease"
    ]

    if any(word in q for word in change_words):
        agents.append("Change Detection")


    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    ocr_words = [
        "text",
        "read",
        "label",
        "labels",
        "written",
        "writing",
        "sign",
        "signs",
        "name",
        "names"
    ]

    if any(word in q for word in ocr_words):
        agents.append("OCR")


    # --------------------------------------------------------
    # VLM REASONING
    # --------------------------------------------------------

    vlm_words = [
        "what",
        "describe",
        "analyze",
        "analyse",
        "explain",
        "identify",
        "scene",
        "image",
        "visible",
        "looks like",
        "what do you see"
    ]

    if any(word in q for word in vlm_words):

        if "VLM Reasoning" not in agents:
            agents.append("VLM Reasoning")


    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    if not agents:
        agents.append("VLM Reasoning")


    return agents


# ============================================================
# RUN ORCHESTRATOR
# ============================================================

def run_orchestrator(image_url, query):

    # --------------------------------------------------------
    # 1. QUERY UNDERSTANDING
    # --------------------------------------------------------

    selected_agents = understand_query(query)

    print()
    print("================================================")
    print("SATQUERY AI — ORCHESTRATOR")
    print("================================================")

    print("User Query:", query)
    print("Selected Agents:", selected_agents)


    # --------------------------------------------------------
    # 2. RUN SPECIALIST AGENTS
    # --------------------------------------------------------

    agent_results = []

    for agent in selected_agents:

        print(f"\nRunning {agent}...")

        try:

            result = run_vision_agent(
                image_url=image_url,
                query=query,
                agent_type=agent
            )

            agent_results.append(result)

            print(f"{agent} completed.")

        except Exception as e:

            print(f"{agent} failed:", str(e))

            agent_results.append({

                "agent": agent,

                "status": "AGENT_ERROR",

                "query": query,

                "findings": [
                    f"{agent} failed: {str(e)}"
                ],

                "confidence": "LOW"

            })


    # --------------------------------------------------------
    # 3. EVIDENCE FUSION
    # --------------------------------------------------------

    print("\nFusing evidence...")

    try:

        fused_result = fuse_evidence(
            agent_results
        )

    except Exception as e:

        fused_result = {

            "evidence": [],

            "object_counts": {},

            "total_evidence_items": 0,

            "confidence": "LOW",

            "status": "FUSION_ERROR",

            "error": str(e)

        }


    # --------------------------------------------------------
    # 4. ANSWER AGENT
    # --------------------------------------------------------

    print("\nGenerating final answer...")

    try:

        answer_result = generate_answer(
            query=query,
            fused_result=fused_result
        )

    except Exception as e:

        answer_result = {

            "agent": "Answer Agent",

            "status": "ANSWER_GENERATION_FAILED",

            "query": query,

            "answer": (
                "Unable to generate the final answer: "
                + str(e)
            ),

            "confidence": "LOW"

        }


    # --------------------------------------------------------
    # 5. FINAL RESULT
    # --------------------------------------------------------

    result = {

        "agent": "SATQuery AI Orchestrator",

        "query": query,

        "selected_agents": selected_agents,

        "agent_results": agent_results,

        "fused_evidence": fused_result,

        "fused_findings": fused_result.get(
            "evidence",
            []
        ),

        "object_counts": fused_result.get(
            "object_counts",
            {}
        ),

        "confidence": fused_result.get(
            "confidence",
            "LOW"
        ),

        "answer": answer_result.get(
            "answer",
            "No final answer generated."
        ),

        "answer_agent": answer_result,

        "status": "ORCHESTRATION_COMPLETE"

    }


    # --------------------------------------------------------
    # PRINT FINAL ANSWER
    # --------------------------------------------------------

    print()
    print("================================================")
    print("SATQUERY AI — FINAL ANSWER")
    print("================================================")

    print(result["answer"])

    print()
    print("Confidence:", result["confidence"])

    print("================================================")

    return result


# ============================================================
# SIMPLE SUMMARY
# ============================================================

def get_orchestration_summary(
    orchestration_result
):

    lines = []

    query = orchestration_result.get(
        "query",
        ""
    )

    lines.append(
        f"Query: {query}"
    )


    agents = orchestration_result.get(
        "selected_agents",
        []
    )

    lines.append(
        "Agents used: "
        + ", ".join(agents)
    )


    object_counts = orchestration_result.get(
        "object_counts",
        {}
    )

    if object_counts:

        lines.append(
            "\nDetected objects:"
        )

        for object_name, count in object_counts.items():

            lines.append(
                f"- {object_name}: {count}"
            )


    answer = orchestration_result.get(
        "answer",
        ""
    )

    if answer:

        lines.append(
            "\nFinal Answer:"
        )

        lines.append(
            answer
        )


    confidence = orchestration_result.get(
        "confidence",
        "LOW"
    )

    lines.append(
        f"\nConfidence: {confidence}"
    )

    return "\n".join(lines)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("SATQuery AI — Orchestrator Test")
    print()

    print(
        "Query 1:",
        understand_query(
            "How many cars are visible?"
        )
    )

    print(
        "Query 2:",
        understand_query(
            "What is happening in this image?"
        )
    )

    print(
        "Query 3:",
        understand_query(
            "Has the area changed?"
        )
    )

    print(
        "Query 4:",
        understand_query(
            "Are there any vehicles and buildings?"
        )
    )

    print(
        "Query 5:",
        understand_query(
            "Can you read the text in this image?"
        )
    )
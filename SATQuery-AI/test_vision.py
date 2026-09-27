from vision_agent import run_vision_agent


IMAGE_URL = "PASTE_YOUR_SATELLITE_IMAGE_URL_HERE"


result = run_vision_agent(
    image_url=IMAGE_URL,
    query="Describe the major features visible in this satellite image.",
    agent_type="VLM Reasoning"
)


print("\n==============================")
print("VISION AGENT RESULT")
print("==============================")

print("Status:")
print(result.get("status"))

print("\nVLM Status:")
print(result.get("vlm_status"))

print("\nFindings:")

for finding in result.get("findings", []):
    print("-", finding)

print("\nSummary:")
print(result.get("summary"))

print("\nConfidence:")
print(result.get("vlm_confidence"))
import requests
import json
import os
import base64
import time
from pathlib import Path

# ----------------- CONFIG -----------------

API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable not set")

URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"

SCAN_INTERVAL = 0.5  # seconds
PROCESSED = set()

# ----------------- HELPERS -----------------

def encode_image_to_base64(image_path: Path) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def analyze_image(image_path: Path) -> str:
    """
    Sends image to OpenRouter Gemini model.
    Returns "Yes" or "No".
    """

    base64_image = encode_image_to_base64(image_path)
    data_url = f"data:image/jpeg;base64,{base64_image}"

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "You are a surveillance-focused computer vision AI analyzing a single image.\n\n"
                        "Task:\nDetermine whether the image contains a credible threat.\n\n"
                        "Threat definition:\nWeapons or actions that indicate potential harm, including firearms, "
                        "knives, improvised weapons, explosives, or aggressive behavior. Consider whether a person "
                        "is holding or using the object.\n\n"
                        "Contextual reasoning:\nEvaluate context and intent before deciding.\n"
                        "- Everyday tools in normal settings (e.g., kitchen knife on a cutting board) are not threats.\n"
                        "- Weapons brandished, aimed, concealed, or used aggressively increase threat likelihood.\n"
                        "- Do not assume intent without visible contextual evidence.\n\n"
                        "Output rule:\nRespond with ONLY one word:\n"
                        "- \"Yes\" if a credible threat is present.\n"
                        "- \"No\" if no credible threat is present.\n\n"
                        "Constraints:\n"
                        "- Base the decision only on visible information in the image.\n"
                        "- If the image is ambiguous or low quality, default to \"No\".\n"
                        "- Prefer false negatives over false positives."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": data_url
                    }
                }
            ]
        }
    ]

    payload = {
        "model": "google/gemini-3-flash-preview",
        "messages": messages
    }

    response = requests.post(URL, headers=HEADERS, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


# ----------------- MAIN LOOP -----------------

def main():
    print("[AI] Monitoring images for suspicious activity...")
    print(f"[AI] Directory: {IMAGES_DIR}")

    IMAGES_DIR.mkdir(exist_ok=True)

    while True:
        try:
            for image_path in IMAGES_DIR.glob("*.jpg"):
                if image_path in PROCESSED:
                    continue

                try:
                    result = analyze_image(image_path)
                    print(f"[AI] {image_path.name} → {result}")

                    if result == "Yes":
                        print(f"[ALERT] 🚨 Credible threat detected in {image_path.name}")

                except Exception as e:
                    print(f"[AI] Error processing {image_path.name}: {e}")

                PROCESSED.add(image_path)

            time.sleep(SCAN_INTERVAL)

        except KeyboardInterrupt:
            print("\n[AI] Shutting down.")
            break


# ----------------- ENTRY -----------------

if __name__ == "__main__":
    main()

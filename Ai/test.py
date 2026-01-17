import requests
import json
import os
import base64
from pathlib import Path 

API_KEY = os.environ.get("API_KEY")
url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
image_path = "Ai/images/image.png"
base64_image = encode_image_to_base64(image_path)
data_url = f"data:image/jpeg;base64,{base64_image}"
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "You are a surveillance-focused computer vision AI analyzing a single image.\n\nTask:\nDetermine whether the image contains a credible threat.\n\nThreat definition:\nWeapons or actions that indicate potential harm, including firearms, knives, improvised weapons, explosives, or aggressive behavior. Consider whether a person is holding or using the object.\n\nContextual reasoning:\nEvaluate context and intent before deciding.\n- Everyday tools in normal settings (e.g., kitchen knife on a cutting board) are not threats.\n- Weapons brandished, aimed, concealed, or used aggressively increase threat likelihood.\n- Do not assume intent without visible contextual evidence.\n\nOutput rule:\nRespond with ONLY one word:\n- \"Yes\" if a credible threat is present.\n- \"No\" if no credible threat is present.\n\nConstraints:\n- Base the decision only on visible information in the image.\n- If the image is ambiguous or low quality, default to \"No\".\n- Prefer false negatives over false positives."
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

response = requests.post(url, headers=headers, json=payload)
data = response.json()
print(data["choices"][0]["message"]["content"])

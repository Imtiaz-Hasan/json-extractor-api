from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import io
import pytesseract
from PIL import Image
import json
import re

app = FastAPI()

# Enable CORS for external frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageRequest(BaseModel):
    imageBase64: str

@app.post("/")
async def extract_json(request: ImageRequest):
    try:
        # Remove prefix from base64 string
        base64_str = request.imageBase64.split(",")[1]
        image_data = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(image_data))

        # Perform OCR
        ocr_text = pytesseract.image_to_string(image)
        ocr_text = ocr_text.replace("\n", " ").strip()

        # Try to extract JSON object from OCR text
        json_match = re.search(r"\{[\s\S]*?\}", ocr_text)
        if not json_match:
            raise ValueError("No JSON found")

        extracted_json = json.loads(json_match.group())

        return {
            "success": True,
            "data": extracted_json,
            "message": "Successfully extracted JSON from image"
        }
    except Exception as e:
        return {
            "success": False,
            "data": {},
            "message": f"Failed to extract JSON: {str(e)}"
        }

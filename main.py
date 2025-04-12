from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import io
import pytesseract
from PIL import Image
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageRequest(BaseModel):
    imageBase64: str

@app.post("/")
async def extract_json(request: ImageRequest):
    try:
        base64_str = request.imageBase64.split(",")[1]
        image_data = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(image_data))

        ocr_text = pytesseract.image_to_string(image)

        # Try to extract JSON block from text
        json_match = re.search(r"\{.*\}", ocr_text, re.DOTALL)
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

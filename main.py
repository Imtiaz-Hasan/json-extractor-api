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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageRequest(BaseModel):
    imageBase64: str

def validate_json_data(data):
    required_fields = ['name', 'organization', 'address', 'mobile']
    return all(field in data for field in required_fields)

@app.post("/")
async def extract_json(request: ImageRequest):
    try:
        # Image preprocessing
        base64_str = request.imageBase64.split(",")[1]
        image_data = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(image_data))
        
        # Enhance OCR configuration
        custom_config = r'--oem 3 --psm 6'
        ocr_text = pytesseract.image_to_string(image, config=custom_config)
        
        # Clean and normalize text
        ocr_text = re.sub(r'[\n\r]+', ' ', ocr_text)
        ocr_text = re.sub(r'\s+', ' ', ocr_text).strip()
        
        # Enhanced JSON extraction pattern
        json_pattern = r'\{(?:[^{}]|\{[^{}]*\})*\}'
        potential_jsons = re.finditer(json_pattern, ocr_text)
        
        for match in potential_jsons:
            try:
                json_str = match.group()
                # Normalize quotes and fix common OCR issues
                json_str = json_str.replace("'", '"')
                extracted_json = json.loads(json_str)
                
                if validate_json_data(extracted_json):
                    return {
                        "success": True,
                        "data": extracted_json,
                        "message": "Successfully extracted JSON from image"
                    }
            except json.JSONDecodeError:
                continue
            except Exception as e:
                continue
        
        return {
            "success": False,
            "data": {},
            "message": "No valid JSON object with required fields found"
        }
    
    except Exception as e:
        return {
            "success": False,
            "data": {},
            "message": f"Failed to process image: {str(e)}"
        }

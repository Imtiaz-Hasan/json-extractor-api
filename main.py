from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import io
import pytesseract
from PIL import Image, ImageEnhance
import json
import re
from typing import Dict, Any

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

def validate_json_data(data: Dict[str, Any]) -> bool:
    required_fields = ['name', 'organization', 'address', 'mobile']
    return all(field in data and isinstance(data[field], str) and data[field].strip() for field in required_fields)

@app.post("/")
async def extract_json(request: ImageRequest):
    try:
        # Image preprocessing
        base64_str = request.imageBase64.split(",")[1]
        image_data = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Enhance image quality
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)  # Increase contrast
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)  # Increase sharpness
        
        # Enhanced OCR configuration with better accuracy
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist={}[]":,./\\-_@#$%^&*()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        ocr_text = pytesseract.image_to_string(image, config=custom_config)
        
        # Improved text cleaning and normalization
        ocr_text = re.sub(r'[\n\r]+', ' ', ocr_text)
        ocr_text = re.sub(r'\s+', ' ', ocr_text).strip()
        ocr_text = re.sub(r'[\u201c\u201d]', '"', ocr_text)  # Replace smart quotes
        ocr_text = re.sub(r'[\u2018\u2019]', "'", ocr_text)  # Replace smart single quotes
        
        # Enhanced JSON extraction pattern
        json_pattern = r'\{(?:[^{}]|\{[^{}]*\})*\}'
        potential_jsons = re.finditer(json_pattern, ocr_text)
        
        for match in potential_jsons:
            try:
                json_str = match.group()
                # Advanced normalization and OCR error correction
                json_str = json_str.replace("'", '"')
                json_str = re.sub(r'(\w+)\s*:', r'"\1":', json_str)  # Fix unquoted keys
                json_str = re.sub(r':\s*([^"\s{\[]+)([,}])', r': "\1"\2', json_str)  # Fix unquoted values
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

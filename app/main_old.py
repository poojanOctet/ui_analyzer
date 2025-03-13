from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import base64
import os

load_dotenv()
app = FastAPI()

static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response Models
class AnalysisResponse(BaseModel):
    analysis: dict
    status: str
    analyzed_at: str
    request_id: str

class ErrorResponse(BaseModel):
    detail: str
    error_code: str
    timestamp: str

SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 20 * 1024 * 1024 # 20MB

async def validate_image(file: UploadFile) -> None:
    # Validate file size
    content = await file.read()
    file_size = len(content)
    await file.seek(0)

    if file_size > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum limit of {MAX_IMAGE_SIZE/1024/1024}MB"
        )
    
    # Validate file type
    if file.content_type not in SUPPORTED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type, Supported types: {', '.join(SUPPORTED_IMAGE_TYPES)}"
        )

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, 'index.html'))

@app.post("/analyze-ui")
async def analyze_ui(file: UploadFile, 
                     focus_areas: Optional[List[str]] = ["visual_design", "ux", "accessibility", "best_practices", "positive_aspects"]):
    try:
        # Validate image
        await validate_image(file)

        # Read and encode image
        image_content = await file.read()
        base64_image = base64.b64encode(image_content).decode("utf-8")

        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Update the analysis prompt to be more structured
        analysis_prompt = """Analyze this UI/Website screenshot and provide detailed feedback in the following format:

1. Positive Aspects & Best Practices Followed
   - List key strengths
   - Highlight what's working well

2. Areas for Improvement
   - Visual Design (colors, typography, layout)
   - User Experience (navigation, flow, interactions)
   - Accessibility Concerns
   - Best Practices Not Being Followed

3. Specific Suggested Improvements
   - Actionable recommendations
   - Priority improvements

Please be detailed and specific in your analysis."""

        # API request
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": analysis_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4096,  # Increased token limit for more detailed responses
            temperature=0.7    # Reduced temperature for more consistent responses
        )

        # Structure the response
        analysis_result = {
            "analysis": {
                "content": response.choices[0].message.content,
                "focus_areas": focus_areas,
                "model_used": "gpt-4o-mini", 
                "analyzed_at": datetime.utcnow().isoformat()
            },
            "status": "success",
            "analyzed_at": datetime.utcnow().isoformat(),
            "request_id": response.id
        }
        print(f"Successfully analyzed UI image. Request ID: {response.id}")

        return analysis_result
    
    except Exception as e:
        error_response = ErrorResponse(
            detail=str(e),
            error_code="ANALYSIS_ERROR",
            timestamp=datetime.utcnow().isoformat()
        )
        
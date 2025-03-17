from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import base64, os, asyncio, sys

# Set event loop policy for Windows compatibility (Python 3.13)
# if os.name == 'nt':
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Force legacy event loop policy on Windows
# if sys.platform == "win32":
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
MAX_IMAGE_SIZE = 20 * 1024 * 1024   # 20MB

async def validate_image(file: UploadFile) -> None:
    content = await file.read()
    file_size = len(content)
    await file.seek(0)

    if file_size > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400,
                            detail=f"File size exceeds maximum limit of {MAX_IMAGE_SIZE/1024/1024}MB")
    
    if file.content_type not in SUPPORTED_IMAGE_TYPES:
        raise HTTPException(status_code=400,
                            detail=f"Unsupported file type, Supported types: {', '.join(SUPPORTED_IMAGE_TYPES)}")
    
def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
    
@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, 'index.html'))

# def sync_get_playwright_screenshot(url):
#     print(f"Capturing screenshot for: {url}")
#     try:
#         with sync_playwright() as p:
#             print("Launching browser...")
#             browser = p.chromium.launch(headless=True)
#             page = browser.new_page()
#             print("navigating to URL...")
#             page.goto(url)
#             page.wait_for_load_state('networkidle')
#             print("Taking screenshot...")
#             screenshot = page.screenshot(full_page=True, type='png')
#             # page.close()
#             browser.close()
#             return screenshot
#     except Exception as e:
#         print(f"Playwright error: {e}")
#         raise


# async def get_playwright_screenshot(url):
#     loop = asyncio.get_event_loop()
#     return await loop.run_in_executor(None, sync_get_playwright_screenshot, url)

async def get_playwright_screenshot(url: str):
    print(f"Capturing screenshot for: {url}")
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            response = await page.goto(url, timeout=30000)
            print('response', response)
            if response is None or not response.ok:
                raise Exception(f"Failed to load {url}, status: {response.status}")
            await page.wait_for_timeout(3000)
            print("Taking screenshot...")
            screenshot = await page.screenshot(full_page=True, type='png')
            return screenshot
        finally:
            await browser.close()


@app.post("/analyze-ui")
async def analyze_ui(
    file: Optional[UploadFile] = None,
    url: Optional[str] = None,
    focus_areas: Optional[List[str]] = ["visual_design", "ux", "accessibility", "best_practices", "positive_aspects"]
):
    try:
        if file and url:
            raise HTTPException(status_code=400, detail="Please provide either a file OR a URL, not both")
        
        if not file and not url:
            raise HTTPException(status_code=400, detail="Please provide either a file or a URL")
        
        # Handle image from file upload
        if file:
            await validate_image(file)
            image_content = await file.read()

        # Handle screenshot from URL using Playwright
        elif url:
            if not is_valid_url(url):
                raise HTTPException(status_code=400,
                                    detail="Invalid URL format. Please provide a valid URL with scheme (http/https) and domain")
            
            try:
                image_content = await get_playwright_screenshot(url)
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504,
                                    detail="Timeout while loading page or taking screenshot")
            except Exception as e:
                raise HTTPException(status_code=500,
                                    detail=f"Error capturing screenshot: {str(e)}")
            
        # Encode image to base64
        base64_image = base64.b64encode(image_content).decode("utf-8")

        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        analysis_prompt = """Analyze this UI/Websute screenshot and provide detailed feedback in the following format:
        
        1. Positive Aspects & Best Practices Followed
            - List key strengths
            - Highlight what's working well
            
        2. Area for Improvement
            - Visual Design (colors, typography, layout)
            - User Experience (navigation, flow, interations)
            - Accessibility Concerns
            - Best Practices Not being Followed
            
        3. Specific Suggested Improvements
            - Actionable recommendations
            - Priority improvements
            
        Please be detailed and specific in your analysis.
        Also provide a score for "visual_design", "ux", "accessibility" like A+, A, B+, B, C+, C; A+ being the best.
        NOTE: DO NOT INCLUDE ANY SUGGESTIONS RELATED TO 'SEO'"""

        # API request to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": analysis_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.7
        )

        # Structure the response
        analysis_result = {
            "analysis": {
                "content": response.choices[0].message.content,
                "focus_areas": focus_areas,
                "model_used": "gpt-4o-mini",
                "analyzed_at": datetime.utcnow().isoformat(),
                "source": "url" if url else "file_upload"
            },
            "status": "success",
            "analyzed_at": datetime.utcnow().isoformat(),
            "request_id": response.id
        }
        print(f"Successfully analyzed UI image. Request ID: {response.id}")

        return analysis_result
    
    except HTTPException as e:
        raise e
    except Exception as e:
        error_response = ErrorResponse(
            detail=str(e),
            error_code="ANALYSIS_ERROR",
            timestamp=datetime.utcnow().isoformat()
        )
        raise HTTPException(status_code=500, detail=error_response.dict())
    
@app.get("/screenshot")
async def get_screenshot(url: str):
    if not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    
    try:
        screenshot = await get_playwright_screenshot(url)
        return Response(content=screenshot, media_type="image/png")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout while loading page")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error capturing screenshot: {str(e)}")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

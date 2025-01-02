from fastapi import FastAPI, Request, Form, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from crewai import Agent, Task, Crew, Process
from textwrap import dedent
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Check if OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable is not set")

app = FastAPI()

# Create directories if they don't exist
Path("templates").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True)
Path("previews").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)

# Initialize or load sites metadata
SITES_DB_PATH = Path("data/sites.json")
if not SITES_DB_PATH.exists():
    with open(SITES_DB_PATH, "w") as f:
        json.dump({"sites": []}, f)

def load_sites():
    with open(SITES_DB_PATH, "r") as f:
        return json.load(f)

def save_sites(sites_data):
    with open(SITES_DB_PATH, "w") as f:
        json.dump(sites_data, f, indent=2)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/previews", StaticFiles(directory="previews"), name="previews")

# Templates
templates = Jinja2Templates(directory="templates")

# Crew AI Agents
web_designer = Agent(
    role='Web Designer',
    goal='Create beautiful and functional static websites',
    backstory=dedent("""
        Expert web designer with years of experience in creating 
        modern, responsive websites. Skilled in HTML, CSS, and 
        design principles.
    """),
    verbose=True,
    allow_delegation=False,
    tools=[],
)

content_writer = Agent(
    role='Content Writer',
    goal='Write engaging and effective web content',
    backstory=dedent("""
        Professional content writer specializing in web copy. 
        Experienced in creating compelling headlines, clear value 
        propositions, and persuasive calls-to-action.
    """),
    verbose=True,
    allow_delegation=False,
    tools=[],
)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.post("/generate")
async def generate_site(
    request: Request,
    business_type: str = Form(...),
    key_features: str = Form(...),
    style_preference: str = Form(...),
):
    # Create tasks for the crew
    design_task = Task(
        description=dedent(f"""
            Create a modern, responsive static website for a {business_type}.
            Style preferences: {style_preference}
            The site should include:
            - Navigation bar
            - Hero section
            - Features section with: {key_features}
            - Contact section
            - Footer
            
            Return only the complete HTML code with embedded CSS.
        """),
        expected_output="Complete HTML file with embedded CSS for the website",
        agent=web_designer
    )

    content_task = Task(
        description=dedent(f"""
            Write compelling content for a {business_type} website.
            Key features to highlight: {key_features}
            
            Return the content in this format:
            HERO_TITLE: 
            HERO_SUBTITLE:
            FEATURE1_TITLE:
            FEATURE1_DESCRIPTION:
            [continue for all features]
        """),
        expected_output="Website content in the specified format",
        agent=content_writer
    )

    try:
        # Create and run the crew
        crew = Crew(
            agents=[content_writer, web_designer],
            tasks=[content_task, design_task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()

        # Extract HTML from the result
        html_content = str(result).split('```html')[-1].split('```')[0].strip()

        # Generate site ID and save the site
        sites_data = load_sites()
        site_id = len(sites_data["sites"]) + 1
        preview_path = f'previews/site_{site_id}.html'
        
        # Save the HTML content
        with open(preview_path, 'w') as f:
            f.write(html_content)

        # Save site metadata
        site_metadata = {
            "id": site_id,
            "business_type": business_type,
            "key_features": key_features,
            "style_preference": style_preference,
            "created_at": datetime.now().isoformat(),
            "versions": [{
                "version": 1,
                "file_path": f"site_{site_id}.html",
                "created_at": datetime.now().isoformat(),
                "parameters": {
                    "business_type": business_type,
                    "key_features": key_features,
                    "style_preference": style_preference
                }
            }]
        }
        sites_data["sites"].append(site_metadata)
        save_sites(sites_data)

        return {
            "success": True,
            "site_id": site_id,
            "preview_url": f"/previews/site_{site_id}.html"
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/sites", response_class=JSONResponse)
async def list_sites():
    """List all generated sites with their metadata."""
    try:
        sites_data = load_sites()
        return sites_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sites/{site_id}", response_class=JSONResponse)
async def get_site(site_id: int):
    """Get metadata for a specific site."""
    try:
        sites_data = load_sites()
        site = next((s for s in sites_data["sites"] if s["id"] == site_id), None)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        return site
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sites/{site_id}/versions")
async def create_version(
    site_id: int,
    business_type: str = Form(...),
    key_features: str = Form(...),
    style_preference: str = Form(...),
):
    """Create a new version of an existing site."""
    try:
        # Load existing site data
        sites_data = load_sites()
        site = next((s for s in sites_data["sites"] if s["id"] == site_id), None)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        # Create tasks for the crew
        content_task = Task(
            description=dedent(f"""
                Write compelling content for a {business_type} website.
                Key features to highlight: {key_features}
                
                Return the content in this format:
                HERO_TITLE: 
                HERO_SUBTITLE:
                FEATURE1_TITLE:
                FEATURE1_DESCRIPTION:
                [continue for all features]
            """),
            expected_output="Website content in the specified format",
            agent=content_writer
        )

        design_task = Task(
            description=dedent(f"""
                Create a modern, responsive static website for a {business_type}.
                Style preferences: {style_preference}
                The site should include:
                - Navigation bar
                - Hero section
                - Features section with: {key_features}
                - Contact section
                - Footer
                
                Return only the complete HTML code with embedded CSS.
            """),
            expected_output="Complete HTML file with embedded CSS for the website",
            agent=web_designer
        )

        # Create and run the crew
        crew = Crew(
            agents=[content_writer, web_designer],
            tasks=[content_task, design_task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()

        # Extract HTML from the result
        html_content = str(result).split('```html')[-1].split('```')[0].strip()

        # Save the new version
        version_number = len(site["versions"]) + 1
        version_file = f'site_{site_id}_v{version_number}.html'
        preview_path = f'previews/{version_file}'
        
        with open(preview_path, 'w') as f:
            f.write(html_content)

        # Update site metadata
        new_version = {
            "version": version_number,
            "file_path": version_file,
            "created_at": datetime.now().isoformat(),
            "parameters": {
                "business_type": business_type,
                "key_features": key_features,
                "style_preference": style_preference
            }
        }
        site["versions"].append(new_version)
        save_sites(sites_data)

        return {
            "success": True,
            "site_id": site_id,
            "version": version_number,
            "preview_url": f"/previews/{version_file}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/preview/{site_id}")
async def preview_site(site_id: str):
    """Preview a specific version of a site."""
    return FileResponse(f"previews/{site_id}")
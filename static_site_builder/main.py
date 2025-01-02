from fastapi import FastAPI, Request, Form, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import shutil
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

        # Save the generated site
        site_id = len(os.listdir('previews')) + 1
        preview_path = f'previews/site_{site_id}.html'
        
        with open(preview_path, 'w') as f:
            f.write(html_content)

        return {
            "success": True,
            "preview_url": f"/previews/site_{site_id}.html"
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/preview/{site_id}")
async def preview_site(site_id: str):
    return FileResponse(f"previews/site_{site_id}.html")
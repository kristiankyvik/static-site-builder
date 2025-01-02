# Static Site Builder with AI 🚀

A web application that generates custom static websites using AI. Built with FastAPI and Crew AI, this tool allows users to create professional websites by simply describing their business and features.

## Features

- AI-powered content generation
- Modern, responsive design
- Multiple style options
- Real-time preview
- Easy-to-use interface

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd static-site-builder
```

2. Install the required packages:
```bash
pip install fastapi uvicorn jinja2 python-multipart crewai chromadb
```

3. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Project Structure

```
static_site_builder/
├── main.py              # Main application file
├── templates/           # HTML templates
│   └── index.html      # Main page template
├── static/             # Static files
├── previews/           # Generated sites
└── README.md           # This file
```

## Running the Application

1. Start the server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. Open your web browser and navigate to:
```
http://localhost:8000
```

## Using the Site Builder

1. Fill out the form with:
   - Business Type: The kind of business you want to create a site for
   - Key Features: List your main features or services (one per line)
   - Style Preference: Choose from Modern, Classic, Bold, or Elegant

2. Click "Generate Site" to create your static site

3. Preview your generated site in the right panel

## API Endpoints

- `GET /`: Main page with the site builder interface
- `POST /generate`: Generate a new static site
- `GET /previews/{site_id}.html`: View a generated site

## Example Usage

```python
# Generate a site via API
import requests

data = {
    "business_type": "AI Software Development Company",
    "key_features": """Custom AI Solutions
Machine Learning Integration
Data Analytics
Cloud Infrastructure
API Development""",
    "style_preference": "modern"
}

response = requests.post("http://localhost:8000/generate", data=data)
preview_url = response.json()["preview_url"]
```

## Configuration

The application can be configured through environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `PORT`: Server port (default: 8000)
- `HOST`: Server host (default: 0.0.0.0)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- AI powered by [Crew AI](https://github.com/joaomdmoura/crewAI)
- Styling with modern CSS
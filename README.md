# AI Smart QR Studio

## Project Overview

AI Smart QR Studio is a polished, production-ready portfolio project for generating modern QR codes using AI-enhanced content and theme suggestions. It combines a responsive frontend experience with a FastAPI backend for validation, scan-quality analysis, Gemini-powered AI features, and server-side QR rendering.

## Features

- Live QR preview with instant updates for every input and customization
- Support for multiple QR types: URL, Text, Email, Phone, SMS, WiFi, WhatsApp, Google Maps, Contact (vCard), Social Links
- Custom color, gradient, dot style, eye style, size, margin, and error correction controls
- Logo upload support for branded QR codes
- AI theme suggestions and content generation via backend APIs
- URL validation and QR scan-quality analysis
- Download as PNG or SVG
- Local history support using LocalStorage
- QR scanner integration planned for future enhancement

## Tech Stack

- Frontend: HTML5, CSS3, Vanilla JavaScript, ES6 modules
- Backend: Python, FastAPI, Uvicorn
- AI: Google Gemini-compatible backend wrapper
- QR rendering: QRCode.js for live preview and `segno` / `Pillow` for backend downloads
- Data persistence: LocalStorage for client-side history

## Folder Structure

```text
qr-code-generator/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── routers/
│   │   ├── ai.py
│   │   ├── analysis.py
│   │   ├── download.py
│   │   └── validator.py
│   └── services/
│       ├── gemini_service.py
│       ├── qr_service.py
│       ├── quality_service.py
│       └── validator_service.py
├── frontend/
│   ├── index.html
│   ├── studio.html
│   ├── css/
│   │   ├── style.css
│   │   └── studio.css
│   └── js/
│       ├── api.js
│       ├── app.js
│       ├── qrcode-loader.js
│       └── qr.js
├── images/
├── README.md
└── requirements.txt
```

## Installation

1. Clone the repository:

```bash
git clone <repo-url>
cd qr-code-generator
```

1. Create and activate a Python virtual environment:

```bash
python -m venv .venv
```

- Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

- macOS / Linux:

```bash
source .venv/bin/activate
```

1. Install backend dependencies:

```bash
pip install -r requirements.txt
```

> Note: This project also includes `backend/requirements.txt` for backend-specific dependency tracking.

## Running the Frontend

The frontend is static and can be opened directly in the browser for quick preview.

Recommended local development flow:

```bash
cd frontend
python -m http.server 8001
```

Then open: `http://localhost:8001`

## Running the FastAPI Backend

With your virtual environment active, start the backend server:

```bash
uvicorn backend.main:app --reload --port 8000
```

Visit the interactive API docs at:

```text
http://localhost:8000/docs
```

## Gemini API Setup

To enable AI-powered theme and content generation, configure Gemini credentials in a `.env` file at the project root:

```env
GEMINI_API_URL=https://api.your-ai-provider/v1/generate
GEMINI_API_KEY=your_api_key_here
BACKEND_ALLOWED_ORIGINS=http://localhost:8001,http://localhost:3000
LOG_LEVEL=INFO
```

> The backend includes fallback stubs so you can run the app locally without Gemini credentials.

## Screenshots

Include screenshots in `images/` and display them here once available.

Example:

```md
![Studio Page](images/studio-screenshot.png)
![Landing Page](images/landing-screenshot.png)
```

## Future Enhancements

- Add full Gemini/OpenAI integration with structured prompt templates
- Implement browser-based QR scanning with live camera capture
- Persist user history and saved QR designs in SQLite or MongoDB
- Add authentication and project sharing
- Improve accessibility and keyboard navigation across the app
- Add E2E tests and CI/CD workflows

## License

This repository does not currently include a `LICENSE` file. Add one if you want to define reuse terms or apply an open source license.

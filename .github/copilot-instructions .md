# AI Smart QR Studio

You are my senior full-stack software engineer.

We are building a production-quality portfolio project called **AI Smart QR Studio**.

The goal is to create a modern AI-powered QR Code Generator that demonstrates frontend development, backend development, API design, AI integration, responsive UI/UX, and clean software architecture.

The project must look like a real SaaS product rather than a college project.

Tech Stack

Frontend

- HTML5
- CSS3
- Vanilla JavaScript (ES6 Modules)
- No React or frontend frameworks

Backend

- Python
- FastAPI
- Uvicorn

AI

- Google Gemini API
- API key must remain only on the backend

QR Generation

- QRCode.js on frontend for live preview
- Python qrcode library for backend downloads if needed

Database

- LocalStorage initially
- Backend designed so SQLite/MongoDB can be added later

Design Requirements

The UI should be premium and modern.

Design style:

- Glassmorphism
- Soft shadows
- Rounded corners
- Gradient accents
- Dark and Light mode
- Responsive
- Mobile-first
- Smooth transitions
- Accessible
- Professional typography

Primary Colors

Primary:
`#4F46E5`

Secondary:
`#7C3AED`

Background:

`#F8FAFC`

Dark Background:

`#0F172A`

Card:

rgba(255,255,255,0.15)

Accent:

`#06B6D4`

Project Structure

project/
│
├── backend/
│
│   ├── main.py
│   ├── requirements.txt
│   │
│   ├── routes/
│   │      ai.py
│   │      qr.py
│   │      validator.py
│   │      scanner.py
│   │
│   ├── services/
│   │      gemini_service.py
│   │      validator_service.py
│   │      quality_service.py
│   │      qr_service.py
│   │
│   ├── utils/
│   │
│   └── .env
│
├── frontend/
│
│   ├── index.html
│   ├── studio.html
│   │
│   ├── css/
│   │      style.css
│   │      studio.css
│   │      responsive.css
│   │
│   ├── js/
│   │      app.js
│   │      studio.js
│   │      api.js
│   │      qr.js
│   │      scanner.js
│   │      history.js
│   │      theme.js
│   │
│   ├── assets/
│   └── images/
│
└── README.md

Landing Page

The landing page should contain:

- Sticky navigation
- Hero section
- Call To Action
- Feature cards
- AI showcase
- How It Works
- FAQ
- Footer

Buttons

- Get Started
- Explore Features

The Get Started button opens studio.html.

Studio Page

The Studio page should contain

Left Panel

- QR Type selector
- Content input
- AI Prompt input
- Customization controls
- Logo upload
- Download buttons

Right Panel

- Live QR Preview
- Scan Quality
- URL Validation
- AI Suggestions

Below

- History
- QR Scanner

Supported QR Types

- URL
- Text
- Email
- Phone
- SMS
- WiFi
- WhatsApp
- Google Maps
- Contact (vCard)
- Social Links

Customization

Allow users to customize

- Foreground color
- Background color
- Gradient
- Dot style
- Eye style
- Size
- Margin
- Error correction
- Logo

Live Preview

Every customization should immediately update the preview.

AI Features

Gemini should provide

Theme Suggestions

Returns

- Primary Color
- Secondary Color
- Background Color
- Eye Style
- Dot Style
- Suggested Title
- CTA
- Tagline

AI Content Generator

Generate

- Business Description
- Portfolio Bio
- Event Invitation
- Restaurant Description
- Marketing CTA

FastAPI APIs

POST /ai/theme

POST /ai/content

POST /validator/url

POST /analysis/quality

POST /download

History

Store generated QR codes in LocalStorage.

Scanner

Use browser camera.

Allow scanning QR codes.

Coding Standards

Write clean modular code.

Use semantic HTML.

Comment important sections.

Use reusable CSS classes.

Use CSS variables.

Avoid inline CSS.

Avoid inline JavaScript.

Separate logic into modules.

Follow SOLID principles where applicable.

Make the code production ready.

Never generate placeholder code unless requested.

Generate complete working code for each file.

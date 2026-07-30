Project: AI Smart QR Studio

Tech Stack:
- Frontend: HTML5, CSS3, Vanilla JavaScript
- Backend: Python FastAPI
- AI: Google Gemini API
- QR Generation: qr-code-styling (Frontend)
- Validation & Analysis: FastAPI services

Current Project Structure:

backend/
│
├── main.py
├── routers/
│   ├── ai.py
│   ├── analysis.py
│   ├── validator.py
│   └── download.py
│
├── services/
│   ├── gemini_service.py
│   ├── quality_service.py
│   ├── validator_service.py
│   └── qr_service.py
│
└── .env

frontend/
│
├── studio.html
├── js/
│   ├── api.js
│   ├── qr.js
│   ├── app.js
│   └── qrcode-loader.js

----------------------------------------------------

IMPORTANT ARCHITECTURE

Gemini NEVER generates QR images.

QRCodeStyling is the only component responsible for generating QR codes.

Gemini only acts as an intelligent assistant that converts natural language into structured data and design recommendations.

The flow is:

User
   ↓
Frontend
   ↓
FastAPI
   ↓
Gemini
   ↓
Structured JSON
   ↓
Frontend updates form fields
   ↓
QRGenerator.generate()
   ↓
QRCodeStyling generates QR

Never allow Gemini to generate HTML, CSS or QR images.

----------------------------------------------------

AI PANEL COMPONENTS

The AI section contains the following UI.

----------------------------------------------------

1. AI Prompt

<textarea id="ai-prompt"></textarea>

Purpose:

This is where the user writes a natural language request.

Examples:

"Create a premium QR for my restaurant."

"Generate a WiFi QR for my office."

"Create a QR for my portfolio using modern blue colors."

This field is only input.

It does not generate anything by itself.

----------------------------------------------------

2. Generate with AI Button

<button id="ai-generate">

This is the primary AI feature.

When clicked:

Read the AI Prompt.

Send it to

POST /ai/generate

Example request

{
    "prompt":"Create a premium coffee shop QR"
}

Gemini should understand the request and return structured JSON.

Example response

{
    "success":true,
    "data":{
        "type":"url",
        "payload":"https://coffee.com",

        "title":"Coffee House",

        "tagline":"Fresh Coffee Every Day",

        "cta":"Scan to View Menu",

        "style":{
            "foreground":"#5A3825",
            "background":"#FFF8EF",
            "gradient":"linear",
            "dotStyle":"rounded",
            "eyeStyle":"rounded",
            "margin":8,
            "ecc":"H"
        }
    }
}

Frontend should automatically

• Fill QR content
• Update QR type
• Change foreground color
• Change background color
• Apply gradient
• Apply dot style
• Apply eye style
• Apply ECC
• Update AI Suggestions card
• Automatically regenerate QR

No page refresh.

----------------------------------------------------

3. Suggest Theme Button

<button id="ai-theme">

This button has a different responsibility.

It does NOT generate QR payload.

It ONLY suggests a visual theme.

Call

POST /ai/theme

Example prompt

"Suggest a luxury restaurant theme."

Gemini returns

{
    "theme":"Luxury Restaurant",

    "foreground":"#8B0000",

    "background":"#FFF8E1",

    "gradient":"linear",

    "dotStyle":"classy-rounded",

    "eyeStyle":"rounded",

    "margin":8,

    "ecc":"H"
}

Notice

No payload.

No URL.

No QR content.

Only design.

Display the returned theme inside the AI Suggestions card.

Do not automatically change the QR.

----------------------------------------------------

4. AI Suggestions Card

<div id="ai-suggestion-list"></div>

Purpose:

Display AI-generated content.

For example

Title

Tagline

Call To Action

Theme Name

Design Explanation

Recommendations

This component is display-only.

It never calls Gemini.

----------------------------------------------------

5. Apply Theme Button

<button id="apply-theme">

This button DOES NOT call Gemini.

Instead,

use the theme already stored from the previous /ai/theme response.

When clicked

Update

Foreground Color

Background Color

Gradient

Dot Style

Eye Style

Margin

Error Correction

Then regenerate the QR using

qrGenerator.generate()

No backend request.

Everything happens on the frontend.

----------------------------------------------------

BACKEND ENDPOINTS

POST /ai/generate

Purpose

Convert natural language into

QR payload

QR type

Recommended styling

Marketing content

Title

Tagline

CTA

----------------------------------------------------

POST /ai/theme

Purpose

Generate ONLY

Theme

Foreground color

Background color

Gradient

Dot Style

Eye Style

Margin

ECC

No payload generation.

----------------------------------------------------

POST /ai/improve

Purpose

Analyze an existing QR configuration.

Input

{
    "payload":"https://...",
    "style":{
        ...
    }
}

Return

Scanning improvements

Accessibility suggestions

Logo recommendations

Contrast improvements

ECC recommendations

----------------------------------------------------

GEMINI RESPONSIBILITIES

Gemini should

✔ Understand natural language

✔ Detect QR type

✔ Extract payload

✔ Suggest QR styling

✔ Suggest branding

✔ Suggest title

✔ Suggest tagline

✔ Suggest CTA

✔ Recommend better colors

✔ Recommend better ECC

Gemini should NEVER

✖ Generate QR images

✖ Return HTML

✖ Return CSS

✖ Return JavaScript

✖ Return markdown

Always return valid JSON.

----------------------------------------------------

FRONTEND RESPONSIBILITIES

api.js

Call backend APIs.

Handle loading.

Handle errors.

Parse JSON.

qr.js

Generate QR using qr-code-styling.

Apply styles.

Update preview.

Generate downloads.

studio.html

Display AI panel.

Display suggestions.

Handle Apply Theme.

----------------------------------------------------

OBJECTIVE

Build a modular AI assistant for the QR generator where:

- Gemini is responsible for intelligence.
- FastAPI manages communication.
- qr-code-styling generates the QR.
- The frontend updates automatically without reloading.
- Every AI feature is separated into its own endpoint and has a single responsibility following clean architecture principles.
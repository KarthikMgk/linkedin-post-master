# LinkedIn Post Generator

AI-powered LinkedIn post generation tool with multi-input synthesis and engagement optimization.

## Features

- **Multi-Input Processing**: Combine text, PDFs, images, and URLs in a single request
- **Engagement Optimization**: Psychological hooks, headline optimization, pattern interrupts
- **Conversational Refinement**: Iteratively improve posts through dialogue
- **Smart Synthesis**: AI automatically determines primary vs. supporting content

## Tech Stack

- **Frontend**: React (SPA)
- **Backend**: Python FastAPI
- **AI**: Claude API (Sonnet 4.5)
- **Processing**: PyPDF2, Pytesseract (OCR)

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- Anthropic API key
- Tesseract OCR installed (for image text extraction)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
```

5. Add your API key to `.env`:
```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

6. Install Tesseract OCR (for image processing):
- **Mac**: `brew install tesseract`
- **Ubuntu**: `sudo apt-get install tesseract-ocr`
- **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki

7. Run the backend:
```bash
python main.py
```

Backend will be available at: http://localhost:8000

### Frontend Setup (Coming Next)

Frontend React application setup instructions will be added once backend is verified.

## API Endpoints

- `GET /` - Health check
- `GET /api/health` - Detailed health check with Claude API status
- `POST /api/generate` - Generate LinkedIn post from inputs
- `POST /api/refine` - Refine existing post with feedback

## Development Status

✅ Phase 1: Backend Foundation (In Progress)
- [x] Project structure created
- [x] FastAPI backend setup
- [x] Claude API integration
- [x] Multi-input processing (text, PDF, images)
- [x] Content generation agent
- [ ] Frontend React app
- [ ] End-to-end testing

⏳ Phase 2: Differentiation Features (Upcoming)
⏳ Phase 3: Personalization (Upcoming)
⏳ Phase 4: Advanced Intelligence (Upcoming)

## License

Personal project - Not yet licensed for public use.

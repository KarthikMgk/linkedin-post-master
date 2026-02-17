# Setup Guide - LinkedIn Post Generator

## Quick Start (5 minutes)

### Step 1: Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Tesseract OCR** (for image text extraction):
   ```bash
   # macOS
   brew install tesseract

   # Ubuntu/Debian
   # sudo apt-get install tesseract-ocr

   # Windows
   # Download from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

5. **Create `.env` file with your API key:**
   ```bash
   cp .env.example .env
   # Then edit .env and add your API key
   ```

   Edit `.env` file:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
   ```

6. **Start the backend server:**
   ```bash
   python main.py
   ```

   Backend will run on: http://localhost:8000

### Step 2: Frontend Setup

1. **Open a NEW terminal window** (keep backend running)

2. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

3. **Install dependencies:**
   ```bash
   npm install
   ```

4. **Start the React app:**
   ```bash
   npm start
   ```

   Frontend will open automatically at: http://localhost:3000

### Step 3: Test the Application

1. Visit http://localhost:3000 in your browser
2. Enter some text in the "Text Content" field
3. Click "Generate Post"
4. Your optimized LinkedIn post should appear!

## Troubleshooting

### "Module not found" errors (Python)
- Make sure your virtual environment is activated: `source venv/bin/activate`
- Reinstall requirements: `pip install -r requirements.txt`

### "Command not found: tesseract"
- Install Tesseract OCR (see Step 1.4 above)
- On Mac: `brew install tesseract`

### Backend won't start
- Check that port 8000 is not in use
- Verify your API key in `.env` file
- Check for error messages in terminal

### Frontend won't connect to backend
- Make sure backend is running on port 8000
- Check browser console for errors (F12)
- Verify proxy setting in `frontend/package.json`

### API Key Issues
- Get your API key from: https://console.anthropic.com/
- Make sure it starts with `sk-ant-`
- Ensure it's properly set in `backend/.env`

## Next Steps

Once everything is running:

1. **Test with your real content** - Try different types of inputs
2. **Try the refinement feature** - Generate a post, then refine it
3. **Experiment with PDFs and images** - Test multi-input synthesis
4. **Track engagement** - Post to LinkedIn and measure results!

## Development Notes

- **Backend:** http://localhost:8000
- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs (FastAPI auto-generated)

To stop servers: Press `Ctrl+C` in each terminal window

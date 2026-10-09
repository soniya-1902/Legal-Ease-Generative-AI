# LegalEase — AI-Powered Legal Document Generator

LegalEase is a Streamlit + FastAPI application that accepts a document type, parties, terms and effective date, generates a structured legal-document draft with Gemini, lets the user edit it, and exports TXT, DOCX and PDF files.

> **Important:** LegalEase generates drafts for informational and document-preparation purposes. It is not a substitute for advice from a qualified lawyer, and users should review documents for jurisdiction-specific requirements before signing or relying on them.

## Architecture

```text
Streamlit frontend (8501)
        |
        | POST /generate
        v
FastAPI backend (8000)
        |
        v
GeminiDocumentGenerator
        |
        v
Google Gemini API

Generated text -> editable preview -> TXT / DOCX / PDF
```

## Project structure

```text
LegalEase/
├── backend/
│   ├── ai_core/gemini_generator.py
│   ├── api/routes.py
│   ├── services/document_formatter.py
│   ├── utils/text_utils.py
│   ├── config.py
│   └── main.py
├── frontend/app.py
├── tests/test_api.py
├── assets/logo.png
├── .env.example
├── .gitignore
├── Dockerfile
├── Procfile
├── requirements.txt
└── README.md
```

## VS Code setup

### 1. Open the folder

Open the `LegalEase` folder in VS Code.

### 2. Create a virtual environment

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows CMD:

```cmd
py -3 -m venv .venv
.venv\Scripts\activate.bat
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Gemini

Copy `.env.example` to `.env` and put your Gemini API key in `GEMINI_API_KEY`.

For real Gemini generation:

```env
GEMINI_API_KEY=your_real_key
MOCK_AI=false
```

For UI/API testing without a key:

```env
MOCK_AI=true
```

### 5. Start FastAPI

From the project root:

```bash
uvicorn backend.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/docs` to test the API interactively.

### 6. Start Streamlit

Open a second VS Code terminal, activate the same environment, then run:

```bash
streamlit run frontend/app.py
```

Open the URL Streamlit displays, normally `http://localhost:8501`.

### 7. Test the complete application

1. Select or enter a document type.
2. Enter the parties.
3. Enter semicolon-separated terms.
4. Enter the effective date.
5. Click **Generate Document**.
6. Review/edit the generated text.
7. Download TXT, DOCX or PDF.

### 8. Run automated tests

```bash
pytest -q
```

The tests use `MOCK_AI=true` so they do not consume Gemini API quota.

## API example

`POST /generate`

```json
{
  "document_type": "Non-Disclosure Agreement",
  "parties": "Jane Doe (Disclosing Party), TechNova Inc. (Receiving Party)",
  "terms": "Confidential information must be protected; Disclosure is limited to authorized personnel; Agreement may be terminated with 15 days notice",
  "effective_date": "September 30, 2026"
}
```

Response:

```json
{
  "document_type": "Non-Disclosure Agreement",
  "content": "...generated draft...",
  "model": "gemini-3.8-flash",
  "mock": false
}
```

## Deployment

The included `Dockerfile` runs the FastAPI service. A Streamlit deployment can run `frontend/app.py` separately with `BACKEND_URL` pointing to the deployed API.

# Alternative Financial Data API

A B2B Alternative Financial Data API designed as a "pick and shovel" provider for quants, fintech startups, and developers. It ingests unstructured financial text, extracts structured entities using Generative AI, and serves them via a fast REST API.

## Tech Stack
- **Framework:** FastAPI (Python 3.11+)
- **Validation:** Pydantic
- **Database:** SQLite (MVP) / SQLAlchemy ORM
- **AI Integration:** OpenAI GPT-3.5+

## Getting Started

1. **Set up the virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Add your `.env` file to the root directory with `OPENAI_API_KEY` and `API_KEY`.

4. **Run the Application:**
   ```bash
   uvicorn main:app --reload
   ```

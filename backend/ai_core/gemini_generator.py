import os

from dotenv import load_dotenv

load_dotenv(override=True)


class GeminiDocumentGenerator:
    """Handles communication with Google's Gemini API."""

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "Please add it to the .env file."
            )

        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "google-genai package is missing. "
                "Run: pip install -r requirements.txt"
            ) from exc

        self.client = genai.Client(api_key=self.api_key)

    @staticmethod
    def build_prompt(document_type, parties, terms, effective_date):
        term_block = "\n".join(f"- {term}" for term in terms)
        prompt = f"""
You are an AI legal document drafting assistant for an application called LegalEase.

Create a professional legal document draft using only the information provided.

IMPORTANT RULES:
1. Do not invent names, addresses, money amounts, dates, governing laws, or registration numbers.
2. Do not change the meaning of user-supplied terms.
3. Use placeholders such as [MISSING: GOVERNING LAW] when important information is missing.
4. Do not claim that the document is guaranteed legally valid or enforceable.
5. State that this is an AI-assisted draft and should be reviewed by a qualified legal professional.

DOCUMENT TYPE:
{document_type}

PARTIES:
{parties}

EFFECTIVE DATE:
{effective_date}

USER SUPPLIED TERMS:
{term_block}

DOCUMENT FORMAT:
1. Start with a professional document title and an introductory section.
2. Clearly identify the parties and effective date.
3. Create numbered sections with descriptive headings.
4. Convert the supplied terms into clear professional clauses.
5. Add only normal structural boilerplate necessary to make the document readable.
6. Include termination and confidentiality provisions where appropriate.
7. Include dispute/governing-law placeholders if those details were not supplied.
8. Include signature blocks at the end where appropriate.

Return only the document. Do not put the response inside a code block.
"""
        return prompt.strip()

    def generate_document(self, document_type, parties, terms, effective_date):
        prompt = self.build_prompt(document_type, parties, terms, effective_date)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.2, "max_output_tokens": 6000},
            )
        except Exception as exc:
            raise RuntimeError(f"Gemini API request failed: {exc}") from exc

        text = getattr(response, "text", None)
        if not text or not text.strip():
            raise RuntimeError("Gemini returned an empty response.")
        return text.strip()
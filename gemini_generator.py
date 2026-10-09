from __future__ import annotations

from dataclasses import dataclass

from backend.config import get_settings
from backend.utils.text_utils import sanitize_text, split_terms

try:
    from google import genai
except ImportError:  # pragma: no cover
    genai = None


@dataclass
class GenerationResult:
    text: str
    model: str
    mock: bool


class GeminiDocumentGenerator:
    """Gemini-backed legal-document draft generator with a deterministic test mode."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = None
        if not self.settings.mock_ai and self.settings.gemini_api_key:
            if genai is None:
                raise RuntimeError("google-genai is not installed. Run: pip install -r requirements.txt")
            self.client = genai.Client(api_key=self.settings.gemini_api_key)

    def _build_prompt(
        self, document_type: str, parties: str, terms: str, effective_date: str
    ) -> str:
        term_lines = "\n".join(f"- {term}" for term in split_terms(terms)) or "- No additional terms supplied."
        return f"""You are a careful legal-document drafting assistant.

Create a professional DRAFT of the requested legal document from the supplied facts.
Do not invent names, dates, addresses, money amounts, governing laws, or obligations.
If a material fact is missing, use a clear placeholder such as [INSERT AMOUNT] instead of guessing.
Use neutral, professional language and clearly separated sections.
Include a short title, recitals/background when appropriate, definitions when useful, substantive clauses,
termination/dispute provisions when appropriate, and signature blocks. Preserve every supplied term.
Do not claim that the document is legally valid in any particular jurisdiction.
Do not include markdown fences. Plain text only.

DOCUMENT TYPE:
{sanitize_text(document_type)}

PARTIES:
{sanitize_text(parties)}

EFFECTIVE DATE:
{sanitize_text(effective_date)}

USER-SUPPLIED TERMS:
{term_lines}

Return only the draft document.
"""

    def _mock_document(self, document_type: str, parties: str, terms: str, effective_date: str) -> str:
        title = sanitize_text(document_type).upper()
        party_lines = sanitize_text(parties)
        date = sanitize_text(effective_date)
        term_items = split_terms(terms)
        terms_block = "\n".join(f"{i}. {term}" for i, term in enumerate(term_items, 1)) or "1. No additional terms were provided."
        return f"""{title}

DRAFT - FOR REVIEW

Effective Date: {date or '[INSERT EFFECTIVE DATE]'}

PARTIES
{party_lines or '[INSERT PARTIES]'}

1. PURPOSE
The parties intend to enter into this {sanitize_text(document_type) or 'agreement'} on the terms stated in this draft.

2. AGREED TERMS
{terms_block}

3. GENERAL PROVISIONS
The parties will perform their respective obligations in good faith. Any material information not supplied by the user is intentionally left as a placeholder and should be completed before execution.

4. REVIEW AND SIGNATURE
This document is an AI-assisted draft and should be reviewed for accuracy and applicable legal requirements before signing.

______________________________
Party 1

______________________________
Party 2
"""

    def generate_document(
        self, document_type: str, parties: str, terms: str, effective_date: str
    ) -> GenerationResult:
        if self.settings.mock_ai or not self.settings.gemini_api_key:
            return GenerationResult(
                text=self._mock_document(document_type, parties, terms, effective_date),
                model="mock-template",
                mock=True,
            )

        prompt = self._build_prompt(document_type, parties, terms, effective_date)
        try:
            response = self.client.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
            )
        except Exception as exc:
            raise RuntimeError(f"Gemini generation failed: {exc}") from exc

        text = sanitize_text(getattr(response, "text", "") or "")
        if not text:
            raise RuntimeError("Gemini returned an empty response.")
        return GenerationResult(text=text, model=self.settings.gemini_model, mock=False)

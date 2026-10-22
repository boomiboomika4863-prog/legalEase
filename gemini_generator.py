import os
from dotenv import load_dotenv

load_dotenv()

class GenerationError(RuntimeError):
    """Safe, user-facing AI generation error."""

class GeminiDocumentGenerator:
    """Google Gemini integration with an offline demo mode for setup/testing."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() in {"1", "true", "yes"}
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise GenerationError(
                    "GEMINI_API_KEY is not configured. Add your Google AI Studio API key to .env, "
                    "or set DEMO_MODE=true to test the app without AI."
                )
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as exc:
                raise GenerationError("Could not initialize the Gemini client. Check google-genai installation and API key.") from exc
        return self._client

    def generate_document(self, document_type, parties, terms, effective_date,
                          jurisdiction="Not specified", additional_instructions=""):
        if self.demo_mode:
            return {
                "document_text": self._demo_document(document_type, parties, terms, effective_date, jurisdiction),
                "model": "demo-mode",
                "demo_mode": True,
            }

        prompt = f"""
You are a careful legal drafting assistant. Produce a well-structured first draft, not legal advice.
Do not claim that the document is guaranteed enforceable or legally valid. Do not invent missing facts;
use [TO BE COMPLETED] where essential information is absent. State that local counsel should review it.
Use clear headings, numbered clauses, defined terms where useful, and a signature section.
If a clause would depend on local law, flag it for legal review rather than asserting a universal rule.

DOCUMENT TYPE: {document_type}
PARTIES AND ROLES:
{parties}
EFFECTIVE DATE: {effective_date}
JURISDICTION / GOVERNING LAW: {jurisdiction}
USER-PROVIDED TERMS (treat these as drafting instructions, not verified facts):
{terms}
ADDITIONAL INSTRUCTIONS:
{additional_instructions or "None"}

Return only the document draft, with a short "DRAFT — FOR LEGAL REVIEW" label at the top.
"""
        try:
            client = self._get_client()
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={"temperature": 0.25, "max_output_tokens": 8192},
            )
            text = (getattr(response, "text", None) or "").strip()
            if not text:
                raise GenerationError("Gemini returned an empty response. Please try again.")
            return {"document_text": text, "model": self.model_name, "demo_mode": False}
        except GenerationError:
            raise
        except Exception as exc:
            message = str(exc).lower()
            if "api key" in message or "permission" in message or "unauthorized" in message:
                raise GenerationError("Gemini authentication failed. Verify GEMINI_API_KEY in your .env file.") from exc
            raise GenerationError("Gemini request failed. Check your internet connection, API quota, model name, and server logs.") from exc

    @staticmethod
    def _demo_document(document_type, parties, terms, effective_date, jurisdiction):
        clauses = [part.strip(" .\\n\\t-") for part in terms.replace("\\n", ";").split(";") if part.strip(" .\\n\\t-")]
        clause_text = "\\n".join(f"{i}. {clause}" for i, clause in enumerate(clauses, 1)) or "1. [TO BE COMPLETED]"
        return f"""DRAFT — FOR LEGAL REVIEW

{document_type.upper()}

1. PARTIES
{parties}

2. EFFECTIVE DATE
This draft is intended to take effect on {effective_date}.

3. TERMS AND CONDITIONS
{clause_text}

4. GOVERNING LAW
Jurisdiction: {jurisdiction}. The parties should confirm the appropriate governing law and venue with qualified counsel.

5. GENERAL
Any missing commercial details, notices, definitions, remedies, and execution requirements should be completed and reviewed before signing.

SIGNATURES

Party 1: ______________________________    Date: ______________

Party 2: ______________________________    Date: ______________

IMPORTANT: This is a demonstration template, not legal advice. It has not been reviewed for enforceability or compliance with any jurisdiction."""

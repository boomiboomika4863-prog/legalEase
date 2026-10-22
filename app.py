import os
import requests
import streamlit as st
from dotenv import load_dotenv
from utils.exporters import format_txt, format_docx, format_pdf

load_dotenv()
st.set_page_config(page_title="LegalEase | AI Legal Drafting", page_icon="⚖️", layout="wide")
API_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

st.markdown("""
<style>
.block-container {max-width: 1180px; padding-top: 1.8rem;}
.hero {padding: 1.4rem 1.6rem; border-radius: 16px; background: linear-gradient(120deg,#14213d,#243b63); color: white; margin-bottom: 1rem;}
.hero h1 {color:white; margin:0;}
.note {font-size: .92rem; color: #666;}
</style>
""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="hero"><h1>⚖️ LegalEase</h1><p>AI-powered legal document drafting workspace</p></div>', unsafe_allow_html=True)
st.caption("Create a first draft, review it, edit the wording, and export it. AI output can be wrong and is not legal advice.")

if "document_text" not in st.session_state:
    st.session_state.document_text = ""
if "model_used" not in st.session_state:
    st.session_state.model_used = ""

with st.sidebar:
    st.header("Document details")
    document_type = st.selectbox("Document type", [
        "Employment Contract", "Non-Disclosure Agreement (NDA)", "Residential Lease Agreement",
        "Freelance Work Contract", "Service Agreement", "Employment Offer Letter", "General Agreement", "Other"
    ])
    if document_type == "Other":
        document_type = st.text_input("Specify document type", value="General Agreement")
    parties = st.text_area("Parties and roles", placeholder="Jane Doe (Service Provider); TechNova Inc. (Client)", height=100)
    effective_date = st.text_input("Effective date", placeholder="e.g. 10 April 2026")
    jurisdiction = st.text_input("Jurisdiction / governing law", placeholder="e.g. Tamil Nadu, India (confirm with counsel)", value="")
    terms = st.text_area("Terms and conditions", placeholder="Payment due within 30 days; Confidentiality must be maintained; Either party may terminate with 15 days' notice", height=180)
    additional = st.text_area("Additional instructions (optional)", placeholder="Tone, clause details, formatting preferences...", height=90)
    logo_file = st.file_uploader("Optional company logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
    generate = st.button("✨ Generate document", type="primary", use_container_width=True)

if generate:
    missing = []
    if not parties.strip(): missing.append("parties and roles")
    if not effective_date.strip(): missing.append("effective date")
    if not terms.strip(): missing.append("terms and conditions")
    if missing:
        st.error("Please fill in: " + ", ".join(missing) + ".")
    else:
        payload = {
            "document_type": document_type, "parties": parties, "terms": terms,
            "effective_date": effective_date, "jurisdiction": jurisdiction or "Not specified",
            "additional_instructions": additional,
        }
        try:
            with st.spinner("Drafting your document..."):
                response = requests.post(f"{API_URL}/generate", json=payload, timeout=150)
            if response.ok:
                data = response.json()
                st.session_state.document_text = data["document_text"]
                st.session_state.model_used = data.get("model", "")
                st.success("Draft generated. Review and edit it before use.")
                if data.get("demo_mode"):
                    st.info("Demo mode is enabled: this is a sample template, not AI-generated content.")
            else:
                try: detail = response.json().get("detail", response.text)
                except Exception: detail = response.text
                st.error(f"Backend returned {response.status_code}: {detail}")
        except requests.RequestException:
            st.error(f"Could not reach the backend at {API_URL}. Start FastAPI in a separate terminal and try again.")

left, right = st.columns([1.15, 0.85], gap="large")
with left:
    st.subheader("Document editor")
    edited = st.text_area("Generated draft (editable)", value=st.session_state.document_text, height=540,
                          key="document_editor", placeholder="Your generated document will appear here.")
    st.session_state.document_text = edited
    if st.session_state.model_used:
        st.caption(f"Generation source: {st.session_state.model_used}")
with right:
    st.subheader("Preview")
    if st.session_state.document_text.strip():
        st.markdown(
            "<div style='border:1px solid #d8dee9;border-radius:12px;padding:18px;max-height:540px;overflow-y:auto;background:#fff;color:#222;white-space:pre-wrap;font-family:Georgia,serif;line-height:1.55'>"
            + __import__("html").escape(st.session_state.document_text)
            + "</div>", unsafe_allow_html=True
        )
    else:
        st.info("Generate a draft to see a preview here.")
    st.markdown("### Export")
    export_text = st.session_state.document_text
    logo_bytes = logo_file.getvalue() if logo_file else None
    safe_name = "".join(ch.lower() if ch.isalnum() else "_" for ch in document_type).strip("_") or "legal_document"
    if export_text.strip():
        st.download_button("Download TXT", format_txt(export_text), file_name=f"{safe_name}.txt", mime="text/plain", use_container_width=True)
        try:
            docx_data = format_docx(export_text, document_type, logo_bytes)
            st.download_button("Download DOCX", docx_data, file_name=f"{safe_name}.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        except Exception as exc:
            st.error(f"DOCX export failed: {exc}")
        try:
            pdf_data = format_pdf(export_text, document_type, logo_bytes)
            st.download_button("Download PDF", pdf_data, file_name=f"{safe_name}.pdf", mime="application/pdf", use_container_width=True)
        except Exception as exc:
            st.error(f"PDF export failed: {exc}")
    else:
        st.caption("Export buttons appear after a draft is available.")

st.divider()
st.caption("Privacy reminder: avoid entering unnecessary sensitive personal information. Review every clause with a qualified lawyer in the relevant jurisdiction before signing.")

from __future__ import annotations

import base64
import html
import os
from datetime import date

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="LegalEase", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
.hero { padding: 1.5rem 1.8rem; border-radius: 18px; background: linear-gradient(135deg,#171b36,#241642); margin-bottom: 1rem; }
.hero h1 { margin:0; font-size:2.4rem; }
.hero p { color:#cbd5e1; margin-bottom:0; }
.preview { background:#0b1020; border:1px solid #303852; border-radius:14px; padding:22px; max-height:650px; overflow-y:auto; white-space:pre-wrap; line-height:1.65; }
.notice { padding:.8rem 1rem; border-left:4px solid #a78bfa; background:#171b2b; border-radius:8px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>⚖️ LegalEase</h1><p>AI-powered legal document drafting, editing and export.</p></div>', unsafe_allow_html=True)
st.markdown('<div class="notice">LegalEase creates AI-assisted drafts. Review facts, jurisdiction-specific requirements and final wording with a qualified legal professional when appropriate.</div>', unsafe_allow_html=True)

if "document" not in st.session_state:
    st.session_state.document = ""
if "meta" not in st.session_state:
    st.session_state.meta = {}

with st.sidebar:
    st.header("Document settings")
    doc_type = st.selectbox(
        "Document type",
        ["Employment Contract", "Non-Disclosure Agreement", "Lease Agreement", "Service Agreement", "Freelance Work Contract", "Employment Offer Letter", "Custom"],
    )
    if doc_type == "Custom":
        doc_type = st.text_input("Custom document type", placeholder="e.g. Partnership Agreement")
    font_name = st.selectbox("DOCX font", ["Times New Roman", "Arial", "Calibri", "Georgia"])
    logo_file = st.file_uploader("Optional logo", type=["png", "jpg", "jpeg"])

st.subheader("1. Enter document details")
col1, col2 = st.columns(2)
with col1:
    parties = st.text_area(
        "Parties involved",
        placeholder="Jane Doe (Service Provider), TechNova Inc. (Client)",
        height=140,
    )
with col2:
    effective_date = st.date_input("Effective date", value=date.today())
    terms = st.text_area(
        "Terms & conditions",
        placeholder="Payment within 30 days; Confidentiality must be maintained; Either party may terminate with 15 days notice",
        height=140,
        help="Separate terms with semicolons or put each term on a new line.",
    )

if st.button("✨ Generate Document", type="primary", use_container_width=True):
    if not doc_type.strip() or not parties.strip():
        st.error("Document type and parties are required.")
    else:
        payload = {
            "document_type": doc_type,
            "parties": parties,
            "terms": terms,
            "effective_date": effective_date.strftime("%B %d, %Y"),
        }
        try:
            with st.spinner("Generating your document draft..."):
                response = requests.post(f"{BACKEND_URL}/generate", json=payload, timeout=120)
            if response.ok:
                data = response.json()
                st.session_state.document = data["content"]
                st.session_state.meta = data
                st.success(f"Document generated using {data['model']}.")
            else:
                try:
                    detail = response.json().get("detail", response.text)
                except Exception:
                    detail = response.text
                st.error(f"Generation failed: {detail}")
        except requests.RequestException as exc:
            st.error(f"Cannot connect to FastAPI at {BACKEND_URL}. Start the backend first. Details: {exc}")

if st.session_state.document:
    st.divider()
    st.subheader("2. Preview and edit")
    edited = st.text_area(
        "Editable document",
        value=st.session_state.document,
        height=520,
        label_visibility="collapsed",
    )
    st.session_state.document = edited

    with st.expander("Styled preview", expanded=True):
        safe = html.escape(edited).replace("\n", "<br>")
        st.markdown(f'<div class="preview">{safe}</div>', unsafe_allow_html=True)

    st.subheader("3. Download")
    logo_b64 = None
    if logo_file is not None:
        logo_b64 = base64.b64encode(logo_file.getvalue()).decode("ascii")

    export_payload = {
        "content": st.session_state.document,
        "document_type": doc_type,
        "logo_base64": logo_b64,
        "font_name": font_name,
    }

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Prepare TXT", use_container_width=True):
            try:
                r = requests.post(f"{BACKEND_URL}/export/txt", json=export_payload, timeout=30)
                r.raise_for_status()
                st.download_button("⬇️ Download TXT", r.content, file_name="legalease-document.txt", mime="text/plain", use_container_width=True)
            except requests.RequestException as exc:
                st.error(f"TXT export failed: {exc}")
    with c2:
        if st.button("Prepare DOCX", use_container_width=True):
            try:
                r = requests.post(f"{BACKEND_URL}/export/docx", json=export_payload, timeout=60)
                r.raise_for_status()
                st.download_button("⬇️ Download DOCX", r.content, file_name="legalease-document.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            except requests.RequestException as exc:
                st.error(f"DOCX export failed: {exc}")
    with c3:
        if st.button("Prepare PDF", use_container_width=True):
            try:
                r = requests.post(f"{BACKEND_URL}/export/pdf", json=export_payload, timeout=60)
                r.raise_for_status()
                st.download_button("⬇️ Download PDF", r.content, file_name="legalease-document.pdf", mime="application/pdf", use_container_width=True)
            except requests.RequestException as exc:
                st.error(f"PDF export failed: {exc}")

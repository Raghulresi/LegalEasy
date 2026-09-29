import html
import os
from datetime import date

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="LegalEase", page_icon="⚖️", layout="wide")

st.markdown(
    """
    <style>
    .main-title { text-align: center; font-size: 2.6rem; font-weight: 700; margin-bottom: 5px; }
    .subtitle { text-align: center; color: #777; margin-bottom: 25px; }
    .preview {
        background: #111827; color: #f9fafb; padding: 25px; border-radius: 15px;
        min-height: 450px; white-space: pre-wrap; font-family: Georgia, serif;
        line-height: 1.7; overflow: auto;
    }
    .notice { background: #fff7ed; color: #292524; border: 1px solid #fed7aa;
        padding: 15px; border-radius: 10px; margin-bottom: 20px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">⚖️ LegalEase</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">AI-Powered Legal Document Generator</div>',
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="notice"><b>Important:</b> LegalEase creates AI-assisted legal document drafts.
    Always review the final document with a qualified legal professional before relying on it.</div>
    """,
    unsafe_allow_html=True,
)

if "document" not in st.session_state:
    st.session_state.document = ""
if "model" not in st.session_state:
    st.session_state.model = ""
if "docx_bytes" not in st.session_state:
    st.session_state.docx_bytes = None
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

with st.form("document_form"):
    col1, col2 = st.columns(2)
    with col1:
        document_type = st.selectbox(
            "Document Type",
            [
                "Employment Contract",
                "Non-Disclosure Agreement (NDA)",
                "Lease Agreement",
                "Service Agreement",
                "Freelance Work Contract",
                "Employment Offer Letter",
                "General Agreement",
                "Custom",
            ],
        )
        if document_type == "Custom":
            document_type = st.text_input(
                "Custom Document Type", placeholder="Business Agreement"
            )
        parties = st.text_area(
            "Parties Involved",
            placeholder="Jane Doe (Service Provider), TechNova Inc. (Client)",
            height=130,
        )
    with col2:
        effective_date = st.date_input(
            "Effective Date", value=date.today(), format="DD/MM/YYYY"
        )
        terms_raw = st.text_area(
            "Terms & Conditions",
            placeholder=(
                "Payment within 30 days;\nConfidentiality must be maintained;\n"
                "Either party may terminate with 15 days notice"
            ),
            height=130,
        )
        logo = st.file_uploader(
            "Upload Company Logo (Optional)", type=["png", "jpg", "jpeg"]
        )
    generate = st.form_submit_button("✨ Generate Document", use_container_width=True)

if generate:
    if not parties.strip():
        st.error("Please enter the parties involved.")
    elif not terms_raw.strip():
        st.error("Please enter at least one term.")
    elif not document_type.strip():
        st.error("Please enter a document type.")
    else:
        terms = [
            term.strip()
            for term in terms_raw.replace(";", "\n").splitlines()
            if term.strip()
        ]
        payload = {
            "document_type": document_type.strip(),
            "parties": parties.strip(),
            "terms": terms,
            "effective_date": effective_date.strftime("%B %d, %Y"),
        }
        with st.spinner("Generating legal document with Gemini..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/generate", json=payload, timeout=120
                )
                response.raise_for_status()
                result = response.json()
                st.session_state.document = result["content"]
                st.session_state.model = result.get("model", "")
                st.session_state.docx_bytes = None
                st.session_state.pdf_bytes = None
                st.success("Document generated successfully!")
            except requests.RequestException as exc:
                detail = ""
                if getattr(exc, "response", None) is not None:
                    try:
                        detail = exc.response.json().get("detail", "")
                    except Exception:
                        detail = exc.response.text[:500]
                st.error("Backend error: " + (detail or str(exc)))

if st.session_state.document:
    st.divider()
    st.subheader("Generated Document")
    tab_preview, tab_edit = st.tabs(["📄 Preview", "✏️ Edit Document"])
    with tab_preview:
        safe_document = html.escape(st.session_state.document).replace("\n", "<br>")
        st.markdown(
            f'<div class="preview">{safe_document}</div>', unsafe_allow_html=True
        )
        if st.session_state.model:
            st.caption(f"Generated using: {st.session_state.model}")
    with tab_edit:
        edited_document = st.text_area(
            "Edit your document", value=st.session_state.document, height=650
        )
        if st.button("💾 Save Edits", use_container_width=True):
            st.session_state.document = edited_document
            st.session_state.docx_bytes = None
            st.session_state.pdf_bytes = None
            st.success("Changes saved.")

    st.subheader("Download Document")
    txt_data = st.session_state.document.encode("utf-8")
    st.download_button(
        "⬇️ Download TXT",
        data=txt_data,
        file_name="legalease_document.txt",
        mime="text/plain",
        use_container_width=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📘 Prepare DOCX", use_container_width=True):
            try:
                form_data = {
                    "document_type": document_type,
                    "content": st.session_state.document,
                }
                uploaded_files = (
                    {"logo": (logo.name, logo.getvalue(), logo.type)} if logo else None
                )
                response = requests.post(
                    f"{BACKEND_URL}/export/docx",
                    data=form_data,
                    files=uploaded_files,
                    timeout=60,
                )
                response.raise_for_status()
                st.session_state.docx_bytes = response.content
                st.success("DOCX ready.")
            except requests.RequestException as exc:
                st.error(f"DOCX export failed: {exc}")
        if st.session_state.docx_bytes:
            st.download_button(
                "⬇️ Download DOCX",
                data=st.session_state.docx_bytes,
                file_name="legalease_document.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
    with col2:
        if st.button("📕 Prepare PDF", use_container_width=True):
            try:
                form_data = {
                    "document_type": document_type,
                    "content": st.session_state.document,
                }
                uploaded_files = (
                    {"logo": (logo.name, logo.getvalue(), logo.type)} if logo else None
                )
                response = requests.post(
                    f"{BACKEND_URL}/export/pdf",
                    data=form_data,
                    files=uploaded_files,
                    timeout=60,
                )
                response.raise_for_status()
                st.session_state.pdf_bytes = response.content
                st.success("PDF ready.")
            except requests.RequestException as exc:
                st.error(f"PDF export failed: {exc}")
        if st.session_state.pdf_bytes:
            st.download_button(
                "⬇️ Download PDF",
                data=st.session_state.pdf_bytes,
                file_name="legalease_document.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

st.divider()
st.caption(
    "LegalEase | AI-assisted legal document drafting | Always verify the final "
    "document for your jurisdiction and circumstances."
)
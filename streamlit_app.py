
import os
import requests
import streamlit as st

# ============================================================
# SummarAI - Streamlit Frontend
# Backend: FastAPI
# ============================================================

st.set_page_config(
    page_title="SummarAI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")


# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
        /* ===== BLACK / DARK UI ===== */
        .stApp {
            background: #000000;
            color: #f5f5f5;
        }

        .main .block-container {
            background: #000000;
        }

        [data-testid="stSidebar"] {
            background: #050505;
            border-right: 1px solid #1f1f1f;
        }

        [data-testid="stSidebar"] * {
            color: #f5f5f5;
        }

        /* Text */
        h1, h2, h3, h4, h5, h6,
        p, label, span, div {
            color: inherit;
        }

        /* Hero */
        .hero {
            background: #111111 !important;
            border: 1px solid #292929;
            color: #f5f5f5 !important;
        }

        .hero h1,
        .hero .brand,
        .hero p {
            color: #f5f5f5 !important;
        }

        .hero p,
        .tagline,
        .small-muted,
        .metric-label {
            color: #a3a3a3 !important;
        }

        .hero h1 {
            color: #ffffff !important;
        }

        .hero .brand {
            color: #ffffff !important;
        }

        /* Cards */
        .metric-card,
        .history-card,
        .chat-answer {
            background: #111111 !important;
            border: 1px solid #292929 !important;
            color: #f5f5f5 !important;
        }

        /* Streamlit native metric cards */
        [data-testid="stMetric"] {
            background: #111111 !important;
            border: 1px solid #292929 !important;
            border-radius: 14px !important;
            padding: 1rem !important;
        }

        [data-testid="stMetricLabel"] {
            color: #a3a3a3 !important;
        }

        [data-testid="stMetricValue"] {
            color: #ffffff !important;
        }

        [data-testid="stMetricDelta"] {
            color: #a3a3a3 !important;
        }

        .chat-question {
            background: #181818;
            border: 1px solid #292929;
            color: #f5f5f5;
        }

        /* Inputs */
        input,
        textarea,
        [data-baseweb="select"] > div,
        [data-testid="stFileUploader"] {
            background-color: #111111 !important;
            color: #f5f5f5 !important;
            border-color: #333333 !important;
        }

        input::placeholder,
        textarea::placeholder {
            color: #737373 !important;
        }

        /* Select dropdown */
        [data-baseweb="popover"],
        [role="listbox"] {
            background: #111111 !important;
            color: #f5f5f5 !important;
        }

        /* Tabs */
        button[data-baseweb="tab"] {
            color: #a3a3a3 !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff !important;
        }

        /* Expanders */
        [data-testid="stExpander"] {
            background: #111111;
            border: 1px solid #292929;
        }

        /* Code / pre */
        code, pre {
            background: #0d0d0d !important;
            color: #e5e5e5 !important;
        }

        .footer {
            color: #737373;
        }

        .brand {
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 0.1rem;
        }

        .tagline {
            color: #6b7280;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        .hero {
            padding: 1.5rem 1.8rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #ffffff, #eef2ff);
            border: 1px solid #e5e7eb;
            margin-bottom: 1.2rem;
        }

        .hero h1 {
            margin: 0;
            font-size: 2.2rem;
        }

        .hero p {
            color: #6b7280;
            margin-top: 0.5rem;
        }

        .metric-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 1rem;
            min-height: 105px;
        }

        .metric-label {
            color: #6b7280;
            font-size: 0.85rem;
        }

        .metric-value {
            font-size: 1.55rem;
            font-weight: 750;
            margin-top: 0.25rem;
        }

        .chat-question {
            background: #eef2ff;
            padding: 0.8rem 1rem;
            border-radius: 12px;
            margin-top: 1rem;
        }

        .chat-answer {
            background: white;
            border: 1px solid #e5e7eb;
            padding: 1rem;
            border-radius: 12px;
            margin-top: 0.4rem;
        }

        .history-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 1rem;
            margin-bottom: 0.8rem;
        }

        .small-muted {
            color: #6b7280;
            font-size: 0.85rem;
        }

        div[data-testid="stFileUploader"] {
            background: white;
            border-radius: 14px;
        }

        .footer {
            text-align: center;
            color: #9ca3af;
            padding: 2rem 0 1rem 0;
            font-size: 0.8rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Session state
# -----------------------------
defaults = {
    "token": None,
    "email": None,
    "page": "Dashboard",
    "selected_document": None,
    "selected_document_name": None,
    "last_summary": None,
    "last_qa": None,
    "history": [],
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -----------------------------
# Helpers
# -----------------------------
def api_headers():
    if not st.session_state.token:
        return {}
    return {
        "Authorization": f"Bearer {st.session_state.token}"
    }


def safe_json(response):
    try:
        return response.json()
    except ValueError:
        return {}


def api_error(response, fallback="Something went wrong."):
    data = safe_json(response)
    return data.get("detail") or data.get("error") or f"{fallback} (HTTP {response.status_code})"


def get_history():
    if not st.session_state.token:
        return []

    try:
        response = requests.get(
            f"{API_URL}/history",
            headers=api_headers(),
            timeout=60,
        )

        if response.status_code == 200:
            return response.json()

        st.error(api_error(response, "Could not load history."))
        return []

    except requests.RequestException as exc:
        st.error(f"Could not connect to the backend: {exc}")
        return []


def logout():
    st.session_state.token = None
    st.session_state.email = None
    st.session_state.selected_document = None
    st.session_state.selected_document_name = None
    st.session_state.last_summary = None
    st.session_state.last_qa = None
    st.session_state.history = []
    st.rerun()


# ============================================================
# Authentication
# ============================================================
if not st.session_state.token:
    left, right = st.columns([1.15, 1])

    with left:
        st.markdown(
            """
            <div class="hero">
                <div class="brand">✨ SummarAI</div>
                <h1>Understand documents faster.</h1>
                <p>
                    Upload a PDF, generate an AI summary, and ask questions
                    about the document using RAG.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### What you can do")
        c1, c2 = st.columns(2)
        with c1:
            st.info("📄 **PDF Summarization**\n\nTurn long documents into structured summaries.")
            st.info("💬 **Document Q&A**\n\nAsk questions and get answers grounded in your PDF.")
        with c2:
            st.info("📝 **Text Summarization**\n\nPaste text directly and summarize it.")
            st.info("🗂️ **History**\n\nKeep track of your uploaded documents and answers.")

    with right:
        login_tab, signup_tab = st.tabs(["🔐 Login", "✨ Create account"])

        with login_tab:
            st.subheader("Welcome back")

            login_email = st.text_input(
                "Email",
                key="login_email",
                placeholder="you@example.com",
            )
            login_password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )

            if st.button("Login", type="primary", use_container_width=True):
                if not login_email.strip() or not login_password:
                    st.warning("Please enter your email and password.")
                else:
                    try:
                        response = requests.post(
                            f"{API_URL}/login",
                            data={
                                "username": login_email.strip(),
                                "password": login_password,
                            },
                            timeout=60,
                        )

                        if response.status_code == 200:
                            data = safe_json(response)
                            st.session_state.token = data.get("access_token")
                            st.session_state.email = login_email.strip()
                            st.session_state.page = "Dashboard"

                            if st.session_state.token:
                                st.success("Login successful!")
                                st.rerun()
                            else:
                                st.error("Login succeeded but no access token was returned.")
                        else:
                            st.error(api_error(response, "Login failed."))

                    except requests.RequestException as exc:
                        st.error(f"Could not connect to the backend: {exc}")

        with signup_tab:
            st.subheader("Create your account")

            signup_email = st.text_input(
                "Email",
                key="signup_email",
                placeholder="you@example.com",
            )
            signup_password = st.text_input(
                "Password",
                type="password",
                key="signup_password",
            )
            signup_confirm = st.text_input(
                "Confirm password",
                type="password",
                key="signup_confirm",
            )

            if st.button("Create account", type="primary", use_container_width=True):
                if not signup_email.strip() or not signup_password:
                    st.warning("Please fill in all fields.")
                elif signup_password != signup_confirm:
                    st.warning("Passwords do not match.")
                else:
                    try:
                        response = requests.post(
                            f"{API_URL}/signup",
                            json={
                                "email": signup_email.strip(),
                                "password": signup_password,
                            },
                            timeout=60,
                        )

                        if response.status_code == 200:
                            st.success("Account created. You can now log in.")
                        else:
                            st.error(api_error(response, "Signup failed."))

                    except requests.RequestException as exc:
                        st.error(f"Could not connect to the backend: {exc}")

    st.markdown(
        '<div class="footer">SummarAI • FastAPI + PostgreSQL + Chroma + Mistral</div>',
        unsafe_allow_html=True,
    )
    st.stop()


# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.markdown("## ✨ SummarAI")
    st.caption("AI document intelligence")

    st.divider()

    pages = {
        "🏠 Dashboard": "Dashboard",
        "📄 Summarize PDF": "Summarize PDF",
        "💬 Ask Document": "Ask Document",
        "📝 Summarize Text": "Summarize Text",
        "🗂️ History": "History",
    }

    for label, page_name in pages.items():
        if st.button(
            label,
            key=f"nav_{page_name}",
            use_container_width=True,
        ):
            st.session_state.page = page_name
            st.rerun()

    st.divider()

    st.caption("Signed in as")
    st.write(st.session_state.email)

    if st.button("Logout", use_container_width=True):
        logout()


# ============================================================
# Dashboard
# ============================================================
if st.session_state.page == "Dashboard":
    st.markdown(
        """
        <div class="hero">
            <div class="brand">Good to see you 👋</div>
            <p>
                Your AI workspace for summarizing documents and getting
                answers from your own content.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    history = get_history()
    st.session_state.history = history

    document_count = len(history)
    question_count = sum(len(item.get("questions_answers", [])) for item in history)
    summary_count = sum(len(item.get("summaries", [])) for item in history)

    m1, m2, m3 = st.columns(3)

    with m1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Documents</div>
                <div class="metric-value">{document_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Summaries</div>
                <div class="metric-value">{summary_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Questions answered</div>
                <div class="metric-value">{question_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 🚀 Start working")

    a, b, c = st.columns(3)

    with a:
        st.markdown("#### 📄 PDF")
        st.write("Upload a document and create an AI-generated summary.")
        if st.button("Summarize a PDF", use_container_width=True):
            st.session_state.page = "Summarize PDF"
            st.rerun()

    with b:
        st.markdown("#### 💬 RAG Q&A")
        st.write("Ask questions using the uploaded document as context.")
        if st.button("Ask a document", use_container_width=True):
            st.session_state.page = "Ask Document"
            st.rerun()

    with c:
        st.markdown("#### 📝 Text")
        st.write("Paste text directly and generate a concise summary.")
        if st.button("Summarize text", use_container_width=True):
            st.session_state.page = "Summarize Text"
            st.rerun()

    st.markdown("### Recent documents")

    if not history:
        st.info("No documents yet. Upload your first PDF to get started.")
    else:
        for item in history[:5]:
            with st.container():
                st.markdown(
                    f"""
                    <div class="history-card">
                        <strong>📄 {item.get("filename", "Untitled")}</strong><br>
                        <span class="small-muted">
                            {item.get("page_count", 0)} pages •
                            {item.get("chunk_count", 0)} chunks
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ============================================================
# PDF upload + summary
# ============================================================
elif st.session_state.page == "Summarize PDF":
    st.title("📄 Summarize PDF")
    st.caption("Upload a PDF. SummarAI will process it, store its chunks in Chroma, and generate a structured summary.")

    uploaded_file = st.file_uploader(
        "Choose a PDF",
        type=["pdf"],
        help="Upload a PDF document to summarize.",
    )

    if uploaded_file is not None:
        st.success(f"Selected: **{uploaded_file.name}**")

        if st.button("Upload & Process PDF", type="primary", use_container_width=True):
            try:
                with st.spinner("Uploading and indexing your PDF..."):
                    response = requests.post(
                        f"{API_URL}/upload/pdf",
                        files={
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                "application/pdf",
                            )
                        },
                        headers=api_headers(),
                        timeout=180,
                    )

                if response.status_code == 200:
                    data = safe_json(response)
                    st.session_state.selected_document = str(data.get("document_id"))
                    st.session_state.selected_document_name = data.get(
                        "filename",
                        uploaded_file.name,
                    )

                    st.success("PDF processed successfully.")

                    x, y, z = st.columns(3)
                    with x:
                        st.metric("Pages", data.get("page_count", 0))
                    with y:
                        st.metric("Chunks", data.get("chunk_count", 0))
                    with z:
                        st.metric("Characters", data.get("text_length", 0))

                    st.info(
                        "Your document is indexed. Click **Generate Summary** below."
                    )
                else:
                    st.error(api_error(response, "PDF upload failed."))

            except requests.RequestException as exc:
                st.error(f"Could not connect to the backend: {exc}")

    if st.session_state.selected_document:
        st.divider()

        st.subheader("Generate summary")
        st.write(
            f"Document: **{st.session_state.selected_document_name or st.session_state.selected_document}**"
        )

        if st.button("✨ Generate Summary", type="primary", use_container_width=True):
            try:
                with st.spinner("Reading the document and generating the summary..."):
                    response = requests.post(
                        f"{API_URL}/summarize/pdf",
                        json={
                            "document_id": st.session_state.selected_document
                        },
                        headers=api_headers(),
                        timeout=300,
                    )

                if response.status_code == 200:
                    data = safe_json(response)
                    st.session_state.last_summary = data

                    st.success("Summary generated successfully.")

                    st.markdown("### 📋 Summary")
                    st.markdown(data.get("summary", "No summary returned."))

                    x, y, z = st.columns(3)
                    with x:
                        st.metric("Pages", data.get("page_count", 0))
                    with y:
                        st.metric("Chunks", data.get("chunk_count", 0))
                    with z:
                        st.metric("Sources", data.get("sources", 0))

                else:
                    st.error(api_error(response, "Summary generation failed."))

            except requests.RequestException as exc:
                st.error(f"Could not connect to the backend: {exc}")

    if st.session_state.last_summary:
        st.divider()
        st.subheader("Latest summary")
        st.markdown(
            st.session_state.last_summary.get(
                "summary",
                "No summary available.",
            )
        )


# ============================================================
# Ask document
# ============================================================
elif st.session_state.page == "Ask Document":
    st.title("💬 Ask Your Document")
    st.caption("Ask questions about an indexed PDF. Answers are generated using the most relevant document chunks.")

    history = get_history()

    if not history:
        st.info("Upload a PDF first from **Summarize PDF**.")
    else:
        document_options = {
            f'{item.get("filename", "Untitled")} (ID: {item.get("document_id")})':
            str(item.get("document_id"))
            for item in history
        }

        selected_label = st.selectbox(
            "Select a document",
            list(document_options.keys()),
        )
        selected_id = document_options[selected_label]

        question = st.text_area(
            "Your question",
            placeholder="Example: What are the main conclusions of this document?",
            height=120,
        )

        if st.button("Ask", type="primary", use_container_width=True):
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                try:
                    with st.spinner("Searching the document and generating an answer..."):
                        response = requests.post(
                            f"{API_URL}/ask",
                            json={
                                "document_id": selected_id,
                                "question": question.strip(),
                            },
                            headers=api_headers(),
                            timeout=180,
                        )

                    if response.status_code == 200:
                        data = safe_json(response)
                        st.session_state.last_qa = data

                        st.markdown(
                            f"""
                            <div class="chat-question">
                                <strong>You</strong><br>
                                {question}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.markdown("### 🤖 Answer")
                        st.markdown(
                            f"""
                            <div class="chat-answer">
                                {data.get("answer", "No answer returned.")}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.caption(
                            f"Retrieved sources: {data.get('sources', 0)} • "
                            f"Input tokens: {data.get('input_tokens', 0)} • "
                            f"Output tokens: {data.get('output_tokens', 0)}"
                        )

                    else:
                        st.error(api_error(response, "Question failed."))

                except requests.RequestException as exc:
                    st.error(f"Could not connect to the backend: {exc}")


# ============================================================
# Text summarization
# ============================================================
elif st.session_state.page == "Summarize Text":
    st.title("📝 Summarize Text")
    st.caption("Paste any text and let SummarAI create a concise summary with key points.")

    text_input = st.text_area(
        "Paste your text",
        height=350,
        placeholder="Paste an article, notes, meeting transcript, documentation, or any other text here...",
    )

    if st.button("✨ Summarize Text", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("Please enter some text first.")
        else:
            try:
                with st.spinner("Generating your summary..."):
                    response = requests.post(
                        f"{API_URL}/summarize/text",
                        json={"text": text_input},
                        headers=api_headers(),
                        timeout=180,
                    )

                if response.status_code == 200:
                    data = safe_json(response)

                    st.success("Summary generated!")
                    st.markdown("### 📋 Summary")
                    st.markdown(data.get("summary", "No summary returned."))

                    x, y = st.columns(2)
                    with x:
                        st.metric("Input tokens", data.get("input_tokens", 0))
                    with y:
                        st.metric("Output tokens", data.get("output_tokens", 0))

                else:
                    st.error(api_error(response, "Text summarization failed."))

            except requests.RequestException as exc:
                st.error(f"Could not connect to the backend: {exc}")


# ============================================================
# History
# ============================================================
elif st.session_state.page == "History":
    st.title("🗂️ History")
    st.caption("Your uploaded documents, generated summaries, and previous questions.")

    history = get_history()
    st.session_state.history = history

    if not history:
        st.info("No document history yet.")
    else:
        for item in history:
            document_id = item.get("document_id")
            filename = item.get("filename", "Untitled")
            page_count = item.get("page_count", 0)
            chunk_count = item.get("chunk_count", 0)

            with st.expander(
                f"📄 {filename}  •  {page_count} pages  •  {chunk_count} chunks"
            ):
                summaries = item.get("summaries", [])
                questions = item.get("questions_answers", [])

                if summaries:
                    st.markdown("### 📋 Summaries")
                    for summary in summaries:
                        st.markdown(summary.get("summary", "No summary available."))
                        st.caption(
                            f"Created: {summary.get('created_at', '')} • "
                            f"Input tokens: {summary.get('input_tokens', 0)} • "
                            f"Output tokens: {summary.get('output_tokens', 0)}"
                        )
                        st.divider()

                if questions:
                    st.markdown("### 💬 Questions & Answers")
                    for qa in questions:
                        st.markdown(
                            f"**Q:** {qa.get('question', '')}"
                        )
                        st.markdown(
                            f"**A:** {qa.get('answer', '')}"
                        )
                        st.divider()

                if not summaries and not questions:
                    st.caption("No summary or questions have been recorded yet.")

                if st.button(
                    "🗑️ Delete document",
                    key=f"delete_{document_id}",
                    type="secondary",
                ):
                    try:
                        response = requests.delete(
                            f"{API_URL}/documents/{document_id}",
                            headers=api_headers(),
                            timeout=120,
                        )

                        if response.status_code == 200:
                            st.success("Document and related history deleted.")
                            st.rerun()
                        else:
                            st.error(api_error(response, "Delete failed."))

                    except requests.RequestException as exc:
                        st.error(f"Could not connect to the backend: {exc}")


# ============================================================
# Footer
# ============================================================
st.markdown(
    '<div class="footer">SummarAI • AI-powered document intelligence</div>',
    unsafe_allow_html=True,
)

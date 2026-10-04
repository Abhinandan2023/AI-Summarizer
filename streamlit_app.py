import streamlit as st
import requests
import os




# ============================================================
# Configuration
# ============================================================

API_URL = "http://127.0.0.1:8000"


# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(
    page_title="SummarAI",
    page_icon="📄",
    layout="wide"
)


# ============================================================
# Header
# ============================================================

st.title("📄 SummarAI")
st.write("AI-powered document summarization and Q&A")


# ============================================================
# PDF Upload
# ============================================================

uploaded_file = st.file_uploader(
    "Upload a PDF",
    type=["pdf"]
)


# ============================================================
# Detect New PDF
# ============================================================

if uploaded_file is not None:

    if (
        "uploaded_file_id" not in st.session_state
        or
        st.session_state.uploaded_file_id
        != uploaded_file.file_id
    ):

        # Store current uploaded file ID
        st.session_state.uploaded_file_id = (
            uploaded_file.file_id
        )

        # Remove previously active document
        st.session_state.pop(
            "document_id",
            None
        )


# ============================================================
# Process PDF
# ============================================================

if uploaded_file is not None:

    if st.button("Process PDF"):

        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "application/pdf"
            )
        }

        with st.spinner("Processing PDF..."):

            try:

                response = requests.post(
                    f"{API_URL}/upload/pdf",
                    files=files
                )

            except requests.exceptions.RequestException as e:

                st.error(
                    "Could not connect to the FastAPI backend."
                )

                st.code(str(e))

                st.stop()


        if response.status_code == 200:

            data = response.json()

            # Store newly created document ID
            st.session_state.document_id = (
                data["document_id"]
            )

            st.success(
                "PDF processed successfully!"
            )

            st.write(
                f"**File:** {data['filename']}"
            )

            st.write(
                f"**Pages:** {data['page_count']}"
            )

            st.write(
                f"**Chunks:** {data['chunk_count']}"
            )

        else:

            st.error(
                f"Failed to process PDF. "
                f"Status: {response.status_code}"
            )

            st.code(
                response.text
            )


# ============================================================
# Active Document
# ============================================================

if "document_id" in st.session_state:

    st.divider()

    st.subheader("📄 Active Document")

    st.write(
        f"Document ID: "
        f"`{st.session_state.document_id}`"
    )


    # ========================================================
    # PDF Summary
    # ========================================================

    st.subheader("📝 Document Summary")

    if st.button("Generate Summary"):

        with st.spinner(
            "Generating summary..."
        ):

            try:

                response = requests.post(
                    f"{API_URL}/summarize/pdf",
                    json={
                        "document_id": str(
                            st.session_state.document_id
                        )
                    }
                )

            except requests.exceptions.RequestException as e:

                st.error(
                    "Could not connect to the FastAPI backend."
                )

                st.code(str(e))

                st.stop()


        if response.status_code == 200:

            data = response.json()

            st.success(
                "Summary generated!"
            )

            st.markdown(
                data["summary"]
            )

        else:

            st.error(
                f"Failed to generate summary. "
                f"Status: {response.status_code}"
            )

            st.code(
                response.text
            )


    # ========================================================
    # PDF Q&A
    # ========================================================

    st.divider()

    st.subheader("💬 Ask Questions")

    question = st.text_input(
        "Ask anything about the uploaded PDF"
    )

    if st.button("Ask Question"):

        if not question.strip():

            st.warning(
                "Please enter a question."
            )

        else:

            with st.spinner(
                "Finding the answer..."
            ):

                try:

                    response = requests.post(
                        f"{API_URL}/ask",
                        json={
                            "document_id": str(
                                st.session_state.document_id
                            ),
                            "question": question
                        }
                    )

                except requests.exceptions.RequestException as e:

                    st.error(
                        "Could not connect to the FastAPI backend."
                    )

                    st.code(str(e))

                    st.stop()


            if response.status_code == 200:

                data = response.json()

                st.markdown(
                    "### Answer"
                )

                st.write(
                    data["answer"]
                )

                st.caption(
                    f"Sources used: "
                    f"{data.get('sources', 'N/A')}"
                )

            else:

                st.error(
                    f"Failed to get an answer. "
                    f"Status: {response.status_code}"
                )

                st.code(
                    response.text
                )


# ============================================================
# History
# ============================================================

st.divider()

st.subheader("📚 History")


# ------------------------------------------------------------
# Load History
# ------------------------------------------------------------

if st.button("View History"):

    with st.spinner(
        "Loading history..."
    ):

        try:

            response = requests.get(
                f"{API_URL}/history"
            )

        except requests.exceptions.RequestException as e:

            st.error(
                "Could not connect to the FastAPI backend."
            )

            st.code(str(e))

            st.stop()


    if response.status_code == 200:

        # Store latest history in session state
        st.session_state.history = response.json()

    else:

        st.error(
            f"Failed to load history. "
            f"Status: {response.status_code}"
        )

        st.code(
            response.text
        )


# ------------------------------------------------------------
# Display History
# ------------------------------------------------------------

if "history" in st.session_state:

    history = st.session_state.history


    # --------------------------------------------------------
    # No History
    # --------------------------------------------------------

    if not history:

        st.info(
            "No document history found."
        )


    # --------------------------------------------------------
    # Documents
    # --------------------------------------------------------

    else:

        for document in history:

            document_id = document["document_id"]


            # =================================================
            # Document Header
            # =================================================

            col1, col2 = st.columns(
                [6, 1]
            )


            # -------------------------------------------------
            # Document Information
            # -------------------------------------------------

            with col1:

                st.markdown(
                    f"### 📄 {document['filename']}"
                )

                st.caption(
                    f"Document ID: {document_id} | "
                    f"Pages: {document['page_count']} | "
                    f"Chunks: {document['chunk_count']}"
                )


            # -------------------------------------------------
            # Delete Button
            # -------------------------------------------------

            with col2:

                delete_clicked = st.button(
                    "🗑 Delete",
                    key=f"delete_{document_id}"
                )


            # =================================================
            # Delete Document
            # =================================================

            if delete_clicked:

                with st.spinner(
                    "Deleting document..."
                ):

                    try:

                        delete_response = requests.delete(
                            f"{API_URL}/documents/"
                            f"{document_id}"
                        )

                    except requests.exceptions.RequestException as e:

                        st.error(
                            "Could not connect to the FastAPI backend."
                        )

                        st.code(str(e))

                        st.stop()


                # ------------------------------------------------
                # Delete Successful
                # ------------------------------------------------

                if delete_response.status_code == 200:

                    # Clear active document if the deleted
                    # document is currently active
                    if (
                        "document_id"
                        in st.session_state
                        and
                        st.session_state.document_id
                        == document_id
                    ):

                        st.session_state.pop(
                            "document_id",
                            None
                        )

                        st.session_state.pop(
                            "uploaded_file_id",
                            None
                        )


                    # ------------------------------------------------
                    # IMPORTANT:
                    # Remove deleted document from local history
                    # before rerun.
                    # ------------------------------------------------

                    st.session_state.history = [
                        item
                        for item
                        in st.session_state.history
                        if item["document_id"]
                        != document_id
                    ]


                    st.success(
                        f"{document['filename']} "
                        "deleted successfully."
                    )


                    # ------------------------------------------------
                    # Rerun Streamlit
                    # ------------------------------------------------

                    st.rerun()


                # ------------------------------------------------
                # Delete Failed
                # ------------------------------------------------

                else:

                    st.error(
                        f"Failed to delete document. "
                        f"Status: "
                        f"{delete_response.status_code}"
                    )

                    st.code(
                        delete_response.text
                    )


            # =================================================
            # Document Details
            # =================================================

            with st.expander(
                "View document details"
            ):


                # =============================================
                # Summaries
                # =============================================

                st.markdown(
                    "### 📝 Summaries"
                )

                if document["summaries"]:

                    for summary in document[
                        "summaries"
                    ]:

                        st.markdown(
                            summary["summary"]
                        )

                        st.caption(
                            f"Input tokens: "
                            f"{summary.get('input_tokens', 'N/A')} | "
                            f"Output tokens: "
                            f"{summary.get('output_tokens', 'N/A')}"
                        )

                        st.divider()

                else:

                    st.info(
                        "No summary generated."
                    )


                # =============================================
                # Questions & Answers
                # =============================================

                st.markdown(
                    "### 💬 Questions & Answers"
                )

                if document[
                    "questions_answers"
                ]:

                    for qa in document[
                        "questions_answers"
                    ]:

                        st.markdown(
                            f"**Q:** "
                            f"{qa['question']}"
                        )

                        st.write(
                            f"**A:** "
                            f"{qa['answer']}"
                        )

                        st.caption(
                            f"Input tokens: "
                            f"{qa.get('input_tokens', 'N/A')} | "
                            f"Output tokens: "
                            f"{qa.get('output_tokens', 'N/A')}"
                        )

                        st.divider()

                else:

                    st.info(
                        "No questions asked."
                    )
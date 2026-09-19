import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Marginalia",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# SESSION STATE
# =========================================================

if "pipeline" not in st.session_state:
    st.session_state.pipeline = None

if "file_name" not in st.session_state:
    st.session_state.file_name = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "num_pages" not in st.session_state:
    st.session_state.num_pages = None

if "num_chunks" not in st.session_state:
    st.session_state.num_chunks = None


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    /* -------------------------------------------------
       Overall page
    ------------------------------------------------- */

    .stApp {
        background-color: #fbfaf5;
    }

    [data-testid="stAppViewContainer"] {
        background-color: #fbfaf5;
    }

    [data-testid="stHeader"] {
        background-color: #fbfaf5;
    }


    /* -------------------------------------------------
       Sidebar
    ------------------------------------------------- */

    [data-testid="stSidebar"] {
        background-color: #f3efe1;
        border-right: 1px solid #ddd6c4;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 25px;
        padding-left: 20px;
        padding-right: 20px;
    }

    .sidebar-title {
        font-family: Georgia, serif;
        font-size: 24px;
        font-weight: 700;
        color: #181818;
        margin-bottom: 8px;
    }

    .sidebar-subtitle {
        color: #77736a;
        font-size: 15px;
        line-height: 1.5;
        margin-bottom: 28px;
    }

    .setting-label {
        font-size: 15px;
        font-weight: 500;
        color: #252525;
        margin-top: 15px;
        margin-bottom: 2px;
    }

    .setting-value {
        color: #8e3235;
        font-size: 15px;
        text-align: center;
        margin-bottom: -5px;
    }

    .model-title {
        font-family: Georgia, serif;
        font-size: 23px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 10px;
    }

    .model-info {
        color: #77736a;
        font-size: 14px;
        line-height: 1.7;
        margin-top: 18px;
    }


    /* -------------------------------------------------
       Main content
    ------------------------------------------------- */

    .main-container {
        max-width: 1050px;
        margin: auto;
        padding-top: 55px;
    }

    .brand {
        font-family: monospace;
        color: #b27a2d;
        font-size: 17px;
        letter-spacing: 2px;
        margin-bottom: 20px;
    }

    .main-title {
        font-family: Georgia, serif;
        font-size: 52px;
        font-weight: 700;
        line-height: 1.05;
        color: #242424;
        margin-bottom: 22px;
    }

    .main-description {
        font-size: 18px;
        color: #484848;
        line-height: 1.65;
        max-width: 850px;
        margin-bottom: 35px;
    }

    .section-title {
        font-family: Georgia, serif;
        font-size: 18px;
        color: #222;
        margin-bottom: 10px;
    }


    /* -------------------------------------------------
       Upload area
    ------------------------------------------------- */

    [data-testid="stFileUploader"] {
        background-color: #f3efe1;
        border-radius: 12px;
        border: 1px solid #eee8d8;
        padding: 15px;
    }


    /* -------------------------------------------------
       Buttons
    ------------------------------------------------- */

    .stButton > button {
        border-radius: 8px;
        min-height: 42px;
        font-weight: 500;
    }

    .stButton > button[kind="primary"] {
        background-color: #8e3235;
        border-color: #8e3235;
    }


    /* -------------------------------------------------
       Question box
    ------------------------------------------------- */

    .question-title {
        font-family: Georgia, serif;
        font-size: 25px;
        font-weight: 700;
        color: #242424;
        margin-top: 35px;
        margin-bottom: 12px;
    }

    .answer-box {
        background-color: #f4f0e5;
        border: 1px solid #ddd6c4;
        border-radius: 10px;
        padding: 22px;
        margin-top: 15px;
        line-height: 1.7;
    }

    .source-box {
        background-color: #f8f6ef;
        border: 1px solid #ddd6c4;
        border-radius: 8px;
        padding: 15px;
    }


    /* -------------------------------------------------
       Status
    ------------------------------------------------- */

    .ready-text {
        color: #56704c;
        font-size: 15px;
        margin-top: 10px;
    }

    .paper-info {
        color: #77736a;
        font-size: 14px;
        margin-top: 5px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-title">Reading room settings</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sidebar-subtitle">'
        'Tune how the paper is split and searched.'
        '</div>',
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # Chunk Size
    # -----------------------------------------------------

    st.markdown(
        '<div class="setting-label">Chunk size</div>',
        unsafe_allow_html=True
    )

    chunk_size = st.slider(
        "Chunk size",
        min_value=200,
        max_value=2000,
        value=int(os.getenv("CHUNK_SIZE", 1000)),
        step=100,
        label_visibility="collapsed"
    )

    st.markdown(
        f'<div class="setting-value">{chunk_size}</div>',
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # Chunk Overlap
    # -----------------------------------------------------

    st.markdown(
        '<div class="setting-label">Chunk overlap</div>',
        unsafe_allow_html=True
    )

    chunk_overlap = st.slider(
        "Chunk overlap",
        min_value=0,
        max_value=500,
        value=int(os.getenv("CHUNK_OVERLAP", 200)),
        step=50,
        label_visibility="collapsed"
    )

    st.markdown(
        f'<div class="setting-value">{chunk_overlap}</div>',
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # Top K
    # -----------------------------------------------------

    st.markdown(
        '<div class="setting-label">Passages retrieved per question</div>',
        unsafe_allow_html=True
    )

    top_k = st.slider(
        "Passages retrieved per question",
        min_value=1,
        max_value=10,
        value=int(os.getenv("TOP_K", 5)),
        step=1,
        label_visibility="collapsed"
    )

    st.markdown(
        f'<div class="setting-value">{top_k}</div>',
        unsafe_allow_html=True
    )


    st.markdown("---")


    # -----------------------------------------------------
    # Model
    # -----------------------------------------------------

    st.markdown(
        '<div class="model-title">Model</div>',
        unsafe_allow_html=True
    )

    selected_model = st.radio(
        "Model",
        ["Groq", "Gemini", "OpenRouter"],
        index=0,
        label_visibility="collapsed"
    )


    # -----------------------------------------------------
    # Model information
    # -----------------------------------------------------

    st.markdown(
        """
        <div class="model-info">
        Embeddings — all-MiniLM-L6-v2 (local)<br>
        Index — FAISS, cosine similarity<br>
        Model — openai/gpt-oss-20b
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# MAIN CONTENT
# =========================================================

st.markdown(
    '<div class="main-container">',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="brand">marginalia</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="main-title">Ask the paper in the margin</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="main-description">
    Upload a research paper and ask it what you would ask a colleague
    who actually read it — the objective, the method, the data, what it
    found, and where it falls short. Every answer is grounded in the
    paper's own text and can be traced back to its source page.
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# PDF UPLOAD
# =========================================================

st.markdown(
    '<div class="section-title">Upload a research paper (PDF)</div>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"],
    label_visibility="collapsed"
)


# =========================================================
# PROCESS PDF
# =========================================================

if uploaded_file is not None:

    st.markdown(
        f"""
        <div class="paper-info">
        📄 Selected: <b>{uploaded_file.name}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    process_button = st.button(
        "📖 Read this paper",
        type="primary",
        use_container_width=False
    )

    if process_button:

        with st.spinner(
            "Reading the paper and building the knowledge base..."
        ):

            tmp_path = None

            try:

                # Import only when required
                from src.pipeline import RAGPipeline

                # -------------------------------------------------
                # Create temporary PDF
                # -------------------------------------------------

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".pdf"
                ) as tmp:

                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name


                # -------------------------------------------------
                # Create pipeline
                # -------------------------------------------------

                pipeline = RAGPipeline(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    top_k=top_k,
                    embedding_model=os.getenv(
                        "EMBEDDING_MODEL",
                        "all-MiniLM-L6-v2"
                    )
                )


                # -------------------------------------------------
                # Ingest PDF
                # -------------------------------------------------

                pipeline.ingest_pdf(
                    tmp_path,
                    source_name=uploaded_file.name
                )


                # -------------------------------------------------
                # Save pipeline
                # -------------------------------------------------

                st.session_state.pipeline = pipeline
                st.session_state.file_name = uploaded_file.name
                st.session_state.chat_history = []

                st.session_state.num_pages = getattr(
                    pipeline,
                    "num_pages",
                    "N/A"
                )

                st.session_state.num_chunks = getattr(
                    pipeline,
                    "num_chunks",
                    "N/A"
                )


                st.success(
                    "Paper loaded successfully."
                )

                st.rerun()


            except Exception as e:

                st.error(
                    "Could not process the PDF."
                )

                st.exception(e)


            finally:

                # -------------------------------------------------
                # Delete temporary file
                # -------------------------------------------------

                if tmp_path is not None:

                    try:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                    except Exception:
                        pass


# =========================================================
# AFTER PAPER IS PROCESSED
# =========================================================

if st.session_state.pipeline is not None:

    pipeline = st.session_state.pipeline

    st.markdown("---")

    # -----------------------------------------------------
    # Paper information
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Pages",
            st.session_state.num_pages
        )

    with col2:

        st.metric(
            "Text chunks",
            st.session_state.num_chunks
        )

    with col3:

        st.metric(
            "Chunk size",
            chunk_size
        )

    st.markdown(
        f"""
        <div class="ready-text">
        ✓ Ready to answer questions about <b>
        {st.session_state.file_name}
        </b>
        </div>
        """,
        unsafe_allow_html=True
    )


    # =====================================================
    # ASK QUESTION
    # =====================================================

    st.markdown(
        '<div class="question-title">Ask the paper</div>',
        unsafe_allow_html=True
    )

    question = st.text_input(
        "Question",
        placeholder=(
            "Example: What is the main objective of this paper?"
        ),
        label_visibility="collapsed"
    )

    ask_button = st.button(
        "Ask",
        type="primary"
    )


    # =====================================================
    # GENERATE ANSWER
    # =====================================================

    if ask_button:

        if not question.strip():

            st.warning(
                "Please enter a question."
            )

        else:

            with st.spinner(
                "Searching the paper and generating the answer..."
            ):

                try:

                    result = pipeline.answer(
                        question
                    )

                    st.session_state.chat_history.append(
                        {
                            "question": question,
                            "result": result
                        }
                    )

                except Exception as e:

                    st.error(
                        "Could not generate the answer."
                    )

                    st.exception(e)


    # =====================================================
    # DISPLAY ANSWERS
    # =====================================================

    if st.session_state.chat_history:

        st.markdown("---")

        for chat in reversed(
            st.session_state.chat_history
        ):

            question_text = chat["question"]
            result = chat["result"]


            # -------------------------------------------------
            # Question
            # -------------------------------------------------

            st.markdown(
                f"### ❓ {question_text}"
            )


            # -------------------------------------------------
            # Answer
            # -------------------------------------------------

            st.markdown(
                '<div class="answer-box">',
                unsafe_allow_html=True
            )

            st.markdown(
                result.answer
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


            # -------------------------------------------------
            # Sources
            # -------------------------------------------------

            if hasattr(result, "sources"):

                st.markdown(
                    "#### 📚 Sources"
                )

                for source in result.sources:

                    try:

                        i, chunk, score = source

                        with st.expander(
                            f"Source {i} — Page {chunk.page_number}"
                        ):

                            st.write(
                                f"**Document:** {chunk.source}"
                            )

                            st.write(
                                f"**Page:** {chunk.page_number}"
                            )

                            st.write(
                                f"**Similarity:** {score:.2f}"
                            )

                            st.write(
                                "**Relevant text:**"
                            )

                            st.write(
                                chunk.text
                            )

                    except Exception:

                        # Fallback if source structure is different
                        with st.expander("Source"):

                            st.write(source)


# =========================================================
# INITIAL STATE
# =========================================================

else:

    st.markdown(
        """
        <div style="
            margin-top:20px;
            padding:45px;
            text-align:center;
            border:1px dashed #d7d0bf;
            border-radius:10px;
            background-color:#fffefa;
            color:#77736a;
            font-size:16px;
        ">
            Upload a PDF above, then click
            <b>Read this paper</b> to begin.
        </div>
        """,
        unsafe_allow_html=True
    )


st.markdown(
    "</div>",
    unsafe_allow_html=True
)
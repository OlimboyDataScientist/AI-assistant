import os
import streamlit as st
import pandas as pd
from datetime import datetime
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.settings import Settings
from llama_index.llms.together import TogetherLLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.readers.file import (
    DocxReader,
    PandasCSVReader,
    PyMuPDFReader
)
from dotenv import load_dotenv

# Load API key from .env or directly
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# Setup folders
UPLOAD_FOLDER = "uploaded_docs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Setup LLM
llm = TogetherLLM(
    api_key=TOGETHER_API_KEY,
    model="mistralai/Mistral-7B-Instruct-v0.1"
)
# Service Context (optional: add chunking configs)
Settings.llm = llm
Settings.node_parser = SentenceSplitter(chunk_size=512)

# UI setup
st.set_page_config(page_title="📄 Smart Document QA", layout="wide")
st.title("🔍 Ask Questions from Your Documents")

# File uploader
uploaded_files = st.file_uploader("Upload PDFs, DOCX, TXT, or CSV files", type=["pdf", "docx", "txt", "csv"], accept_multiple_files=True)
for file in uploaded_files:
    with open(os.path.join(UPLOAD_FOLDER, file.name), "wb") as f:
        f.write(file.read())

# Load documents
readers = {
    ".pdf": PyMuPDFReader(),
    ".docx": DocxReader(),
    ".csv": PandasCSVReader()
}

def load_uploaded_docs(folder):
    docs = []
    for fname in os.listdir(folder):
        ext = os.path.splitext(fname)[-1].lower()
        reader = readers.get(ext)
        if reader:
            path = os.path.join(folder, fname)
            try:
                loaded = reader.load_data(path)
                for d in loaded:
                    d.metadata = {"source": fname}
                docs.extend(loaded)
            except Exception as e:
                st.warning(f"❌ Could not read {fname}: {e}")
    return docs

# Load & index
documents = load_uploaded_docs(UPLOAD_FOLDER)
if documents:
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine(similarity_top_k=3)
    st.session_state.query_engine = query_engine
else:
    st.warning("Upload some files to get started.")

# User query
query = st.text_input("Ask a question:")
if "history" not in st.session_state:
    st.session_state.history = []

if query and "query_engine" in st.session_state:
    response = st.session_state.query_engine.query(query)
    answer = str(response)
    sources = [n.metadata.get("source", "") for n in response.source_nodes]
    sources_display = ", ".join(set(sources)) if sources else "N/A"

    # Store to history
    qna = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "question": query,
        "answer": answer,
        "source": sources_display
    }
    st.session_state.history.append(qna)

    # Display answer
    st.subheader("💡 Answer")
    st.markdown(f"**Answer:** {answer}")
    st.markdown(f"📄 **Sources:** {sources_display}")

# History in sidebar
st.sidebar.title("🕓 Q&A History")
if st.session_state.history:
    for item in reversed(st.session_state.history):
        st.sidebar.markdown(f"**Q:** {item['question']}")
        st.sidebar.markdown(f"**A:** {item['answer'][:100]}...")
        st.sidebar.markdown(f"**📄 From:** {item['source']}")
        st.sidebar.markdown("---")

    # Option to export
    if st.sidebar.button("💾 Export History"):
        df = pd.DataFrame(st.session_state.history)
        df.to_csv("history.csv", index=False)
        st.sidebar.success("History saved to history.csv!")

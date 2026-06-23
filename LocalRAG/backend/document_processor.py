import os
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader
)

class DocumentProcessor:
    """
    Loads documents and splits them into overlapping chunks using LangChain.
    """
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def load_document(self, file_path: str) -> List[Document]:
        """Loads a document and returns a list of LangChain Document objects."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        _, ext = os.path.splitext(file_path.lower())

        if ext in [".txt", ".md"]:
            loader = TextLoader(file_path, encoding="utf-8")
        elif ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif ext == ".docx":
            loader = Docx2txtLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        return loader.load()

    def process(self, file_path: str) -> List[Document]:
        """Loads a document, splits it into chunks, and returns them with metadata."""
        raw_documents = self.load_document(file_path)
        chunks = self.splitter.split_documents(raw_documents)

        file_name = os.path.basename(file_path)
        total_chunks = len(chunks)

        for i, chunk in enumerate(chunks):
            # Clean/standardize metadata
            chunk.metadata = {
                "file_name": file_name,
                "chunk_index": i,
                "total_chunks": total_chunks
            }

        return chunks

def process_document(
    file_path: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Document]:
    """Helper function matching the API entry point."""
    processor = DocumentProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return processor.process(file_path)
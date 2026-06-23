import os

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader
)


class DocumentProcessor:

    def __init__(
        self,
        chunk_size=500,
        chunk_overlap=50
    ):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                " ",
                ""
            ]
        )


    def load_document(self, file_path: str):

        ext = os.path.splitext(
            file_path
        )[1].lower()


        if ext in [".txt", ".md"]:
            loader = TextLoader(
                file_path,
                encoding="utf-8"
            )

        elif ext == ".pdf":
            loader = PyPDFLoader(
                file_path
            )

        elif ext == ".docx":
            loader = Docx2txtLoader(
                file_path
            )

        else:
            raise ValueError(
                f"Unsupported file type: {ext}"
            )


        documents = loader.load()

        return documents



    def process(
        self,
        file_path: str
    ):

        documents = self.load_document(
            file_path
        )


        chunks = self.splitter.split_documents(
            documents
        )


        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["file_name"] = (
                os.path.basename(file_path)
            )

        return chunks
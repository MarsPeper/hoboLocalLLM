import os
import re
from typing import List, Dict, Any

class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, separators: List[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> List[str]:
        # Clean carriage returns
        text = re.sub(r'\r\n', '\n', text)
        return self._recursive_split(text, self.separators)

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]
        
        if not separators:
            # Fallback to character splitting with overlap if no separators left
            chunks = []
            start = 0
            step = max(1, self.chunk_size - self.chunk_overlap)
            while start < len(text):
                chunks.append(text[start:start + self.chunk_size])
                start += step
            return chunks
        
        separator = separators[0]
        next_separators = separators[1:]
        
        # Split by the separator
        if separator == "":
            splits = list(text)
        else:
            splits = text.split(separator)
            
        chunks = []
        current_doc = []
        current_len = 0
        
        for i, split in enumerate(splits):
            part = split
            # Re-attach separator to the split if it's not the last one
            if i < len(splits) - 1 and separator != "":
                part += separator
                
            part_len = len(part)
            
            if current_len + part_len <= self.chunk_size:
                current_doc.append(part)
                current_len += part_len
            else:
                # Flush the current chunk
                if current_doc:
                    chunks.append("".join(current_doc))
                
                # If this individual part is larger than chunk_size, split it recursively
                if part_len > self.chunk_size:
                    sub_chunks = self._recursive_split(part, next_separators)
                    chunks.extend(sub_chunks)
                    current_doc = []
                    current_len = 0
                else:
                    # Start a new chunk, pulling in overlap from the end of the previous chunk
                    overlap_doc = []
                    overlap_len = 0
                    for prev_part in reversed(current_doc):
                        if overlap_len + len(prev_part) <= self.chunk_overlap:
                            overlap_doc.insert(0, prev_part)
                            overlap_len += len(prev_part)
                        else:
                            break
                    
                    current_doc = overlap_doc + [part]
                    current_len = sum(len(p) for p in current_doc)
                    
        if current_doc:
            chunks.append("".join(current_doc))
            
        # Strip whitespace from chunks and filter out empty ones
        return [c.strip() for c in chunks if c.strip()]


def extract_text_from_file(file_path: str) -> str:
    """Extracts plain text from txt, md, pdf, and docx files."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    _, ext = os.path.splitext(file_path.lower())
    
    if ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
            
    elif ext == ".pdf":
        import pypdf
        reader = pypdf.PdfReader(file_path)
        text = []
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text.append(content)
        return "\n".join(text)
        
    elif ext == ".docx":
        import docx
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
        
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def process_document(file_path: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[Dict[str, Any]]:
    """Loads a document, extracts text, chunks it, and returns chunks with metadata."""
    text = extract_text_from_file(file_path)
    file_name = os.path.basename(file_path)
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    text_chunks = splitter.split_text(text)
    
    chunks = []
    for idx, content in enumerate(text_chunks):
        chunks.append({
            "content": content,
            "metadata": {
                "file_name": file_name,
                "chunk_index": idx,
                "total_chunks": len(text_chunks)
            }
        })
    return chunks

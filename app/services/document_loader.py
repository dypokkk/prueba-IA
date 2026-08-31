import re
from pathlib import Path
from typing import List, Dict, Any

class DocumentLoader:
    def __init__(self, data_dir: Path, chunk_size: int = 1500, chunk_overlap: int = 250):
        self.data_dir = data_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_markdown_documents(self) -> List[Dict[str, Any]]:
        """
        Loads all markdown files in the data directory and extracts structured chunks.
        """
        documents = []
        md_files = sorted(self.data_dir.glob("*.md"))

        for file_path in md_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            chunks = self._chunk_markdown(content, file_path.name)
            documents.extend(chunks)

        return documents

    def _chunk_markdown(self, text: str, filename: str) -> List[Dict[str, Any]]:
        """
        Splits markdown text into overlapping chunks, tracking section headers.
        """
        chunks = []
        # Split into main sections based on headers (# and ##)
        sections = re.split(r'\n(?=#{1,3}\s+)', text)
        chunk_idx = 0

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Extract section title
            first_line = section.split('\n')[0]
            section_title = first_line.strip('# ').strip()

            # If section is small enough, keep as single chunk
            if len(section) <= self.chunk_size:
                chunks.append({
                    "chunk_id": f"{filename}#chunk_{chunk_idx}",
                    "filename": filename,
                    "section": section_title,
                    "text": section
                })
                chunk_idx += 1
            else:
                # Sliding window chunking with overlap
                start = 0
                while start < len(section):
                    end = start + self.chunk_size
                    chunk_text = section[start:end]

                    # Snap to last space or newline if not at end of text
                    if end < len(section):
                        last_space = max(chunk_text.rfind(' '), chunk_text.rfind('\n'))
                        if last_space > self.chunk_size // 2:
                            chunk_text = chunk_text[:last_space]
                            end = start + last_space

                    # Prepend section context if not the first chunk in section
                    formatted_text = chunk_text.strip()
                    if not formatted_text.startswith(f"## {section_title}") and not formatted_text.startswith(f"# {section_title}"):
                        formatted_text = f"[{section_title}]\n{formatted_text}"

                    chunks.append({
                        "chunk_id": f"{filename}#chunk_{chunk_idx}",
                        "filename": filename,
                        "section": section_title,
                        "text": formatted_text
                    })
                    chunk_idx += 1

                    # Advance window with overlap
                    start = end - self.chunk_overlap
                    if start >= len(section) or (end >= len(section)):
                        break

        return chunks

from pydantic import BaseModel
from common.rag_db import pinecone_index, PineconeIdx1536_Namespaces
from bs4 import BeautifulSoup

clean_text = lambda raw_text: BeautifulSoup(raw_text, "lxml").text

RELEVANT_FIELDS = [
    "text",
    "product_id",
    "file_id",
    "advisor_id",
    "product_name",
    "page_number",
]


def get_documents(vector: list, top_k: int = 10, filters: dict = {}):
    _results = pinecone_index.query(
        namespace=PineconeIdx1536_Namespaces.doc_rag,
        vector=vector,
        include_metadata=True,
        filter=filters,
        top_k=top_k,
    )
    res = _results["matches"]
    results = []
    for match in res:
        match_meta = match.get("metadata", {})
        _meta = {k: match_meta.get(k, "") for k in RELEVANT_FIELDS}
        results.append(_meta)
    return results


class CitationNode(BaseModel):
    id: int
    text: str
    product_id: str
    file_id: str
    advisor_id: str
    product_name: str
    page_number: int


class RAGContext:
    def __init__(self, chunks: list, with_references: bool = False):
        self.chunks = chunks
        self.with_references = with_references
        self.ranked_chunks = []
        self.seen_map = set()
        self.chunk_map = {}

        self.messages = []

    def build_context(self):
        rank = 1
        for chunk in self.chunks:
            unique_key = f"{chunk.get('product_id')}_{chunk.get('page_number')}"

            if unique_key in self.seen_map:
                continue
            self.seen_map.add(unique_key)
            self.ranked_chunks.append(
                CitationNode(
                    id=rank,
                    text=clean_text(chunk.get("text")),
                    product_id=chunk.get("product_id"),
                    file_id=chunk.get("file_id"),
                    advisor_id=chunk.get("advisor_id"),
                    product_name=chunk.get("product_name"),
                    page_number=int(chunk.get("page_number", "1")),
                )
            )
            rank += 1

        for chunk in self.ranked_chunks:
            self.chunk_map[chunk.id] = chunk.dict()

        for chunk in self.ranked_chunks:
            prefix = (
                f"<Text Document Index: {chunk.id}>\n" if self.with_references else ""
            )
            suffix = (
                f"\n</Text Document Index: {chunk.id}>" if self.with_references else ""
            )
            chunk_msg = f"{prefix}{chunk.text}{suffix}"
            print("########## Chunk Message ##########",chunk_msg)
            self.messages.append({"type": "text", "text": chunk_msg})

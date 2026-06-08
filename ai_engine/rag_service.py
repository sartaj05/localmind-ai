import os
import chromadb
from pypdf import PdfReader
from django.conf import settings
from sentence_transformers import SentenceTransformer

from .models import KnowledgeDocument


CHROMA_PATH = "chroma_db"

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name="localmind_knowledge")


def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks


def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text() or ""
        text += page_text + "\n"

    return text


def extract_text_from_txt(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        return file.read()


def extract_text_from_document(file_path):
    lower_path = file_path.lower()

    if lower_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)

    if lower_path.endswith(".txt"):
        return extract_text_from_txt(file_path)

    return ""


def clear_collection():
    existing = collection.get()

    if existing and existing.get("ids"):
        collection.delete(ids=existing["ids"])


def build_knowledge_base():
    clear_collection()

    documents = KnowledgeDocument.objects.all()
    chunk_count = 0

    for document in documents:
        file_path = document.file.path

        if not os.path.exists(file_path):
            continue

        text = extract_text_from_document(file_path)

        if not text.strip():
            continue

        chunks = chunk_text(text)

        for index, chunk in enumerate(chunks):
            chunk_id = f"doc_{document.id}_chunk_{index}"

            embedding = embedding_model.encode(chunk).tolist()

            collection.add(
                ids=[chunk_id],
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[
                    {
                        "document_id": document.id,
                        "source": document.title,
                        "file_name": os.path.basename(file_path),
                    }
                ],
            )

            chunk_count += 1

    return chunk_count


def search_knowledge(query, top_k=3):
    query_embedding = embedding_model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    context_parts = []

    for index, document in enumerate(documents):
        metadata = metadatas[index]
        source = metadata.get("source", "unknown")
        context_parts.append(f"Source: {source}\nContent: {document}")

    return "\n\n".join(context_parts)
import os

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

from .models import KnowledgeDocument


CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "localmind_knowledge"

embedding_model = None

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)


def get_embedding_model():
    """
    Lazy-load embedding model only when RAG is actually used.
    This avoids loading HuggingFace model during makemigrations/migrate.
    """
    global embedding_model

    if embedding_model is None:
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    return embedding_model


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


def clear_user_collection(user):
    existing = collection.get(
        where={"user_id": user.id}
    )

    if existing and existing.get("ids"):
        collection.delete(ids=existing["ids"])


def build_knowledge_base(user):
    clear_user_collection(user)

    documents = KnowledgeDocument.objects.filter(user=user)
    chunk_count = 0

    model = get_embedding_model()

    for document in documents:
        file_path = document.file.path

        if not os.path.exists(file_path):
            continue

        text = extract_text_from_document(file_path)

        if not text.strip():
            continue

        chunks = chunk_text(text)

        for index, chunk in enumerate(chunks):
            chunk_id = f"user_{user.id}_doc_{document.id}_chunk_{index}"

            embedding = model.encode(chunk).tolist()

            collection.add(
                ids=[chunk_id],
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[
                    {
                        "user_id": user.id,
                        "document_id": document.id,
                        "source": document.title,
                        "file_name": os.path.basename(file_path),
                    }
                ],
            )

            chunk_count += 1

    return chunk_count


def search_knowledge(query, user, top_k=3):
    model = get_embedding_model()

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"user_id": user.id},
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    context_parts = []

    for index, document in enumerate(documents):
        metadata = metadatas[index]
        source = metadata.get("source", "unknown")

        context_parts.append(
            f"Source: {source}\nContent: {document}"
        )

    return "\n\n".join(context_parts)

def get_user_collection_stats(user):
    existing = collection.get(
        where={"user_id": user.id}
    )

    ids = existing.get("ids", []) if existing else []

    return {
        "total_chunks": len(ids),
        "is_indexed": len(ids) > 0,
    }
def search_knowledge_with_sources(query, user, top_k=3):
    model = get_embedding_model()

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"user_id": user.id},
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    context_parts = []
    sources = []

    for index, document in enumerate(documents):
        metadata = metadatas[index]

        source = metadata.get("source", "unknown")
        document_id = metadata.get("document_id")
        file_name = metadata.get("file_name", "unknown")

        context_parts.append(
            f"Source: {source}\nContent: {document}"
        )

        sources.append(
            {
                "document_id": document_id,
                "source": source,
                "file_name": file_name,
                "chunk_preview": document[:200],
            }
        )

    return {
        "context": "\n\n".join(context_parts),
        "sources": sources,
    }
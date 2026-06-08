import os
import chromadb
from sentence_transformers import SentenceTransformer


CHROMA_PATH = "chroma_db"
KNOWLEDGE_PATH = "knowledge_base"

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


def build_knowledge_base():
    if not os.path.exists(KNOWLEDGE_PATH):
        os.makedirs(KNOWLEDGE_PATH)

    existing = collection.get()

    if existing and existing.get("ids"):
        collection.delete(ids=existing["ids"])

    doc_id = 1

    for filename in os.listdir(KNOWLEDGE_PATH):
        if not filename.endswith(".txt"):
            continue

        file_path = os.path.join(KNOWLEDGE_PATH, filename)

        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()

        chunks = chunk_text(text)

        for chunk in chunks:
            embedding = embedding_model.encode(chunk).tolist()

            collection.add(
                ids=[str(doc_id)],
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[{"source": filename}],
            )

            doc_id += 1

    return doc_id - 1


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
        source = metadatas[index].get("source", "unknown")
        context_parts.append(f"Source: {source}\nContent: {document}")

    return "\n\n".join(context_parts)
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from mistralai import Mistral
from dotenv import load_dotenv
import os
import time

load_dotenv()

mistral = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

cliente = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

collections = [c.name for c in cliente.get_collections().collections]
if "Estudos" not in collections:
    cliente.create_collection(
        collection_name="Estudos",
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )

def chunk_text(texto: str, tamanho: int = 500) -> list[str]:
    palavras = texto.split()
    chunks = []
    for i in range(0, len(palavras), tamanho):
        chunks.append(" ".join(palavras[i:i+tamanho]))
    return chunks

def gerar_embedding(texto: str) -> list[float]:
    result = mistral.embeddings.create(
        model="mistral-embed",
        inputs=[texto]
    )
    return result.data[0].embedding

with open("train.txt", "r", encoding="utf-8") as f:
    texto = f.read()

chunks = chunk_text(texto)
print(f"{len(chunks)} chunks gerados.")

points = []

for i, chunk in enumerate(chunks):
    try:
        embedding = gerar_embedding(chunk)
        points.append(PointStruct(
            id=i,
            vector=embedding,
            payload={"texto": chunk}
        ))
        time.sleep(0.5)

        if i % 100 == 0:
            print(f"{i}/{len(chunks)} indexados...")
            cliente.upsert(collection_name="Estudos", points=points)
            points = []

    except Exception as e:
        print(f"Erro no chunk {i}: {e}")
        time.sleep(10)
        continue

if points:
    cliente.upsert(collection_name="Estudos", points=points)

print("Indexação concluída!")
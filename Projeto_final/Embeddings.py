from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from mistralai import Mistral
from dotenv import load_dotenv
import os
import time

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializa o cliente Mistral para geração de embeddings
mistral = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

# Inicializa o cliente Qdrant para armazenar e indexar os vetores
cliente = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

# Verifica se a coleção "Estudos" já existe; cria caso não exista.
# Vetores de 1024 dimensões com distância cosseno (padrão para similaridade semântica).
collections = [c.name for c in cliente.get_collections().collections]
if "Estudos" not in collections:
    cliente.create_collection(
        collection_name="Estudos",
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )


def chunk_text(texto: str, tamanho: int = 500) -> list[str]:
    """Divide o texto em blocos de até `tamanho` palavras.
    Necessário porque modelos de embedding têm limite de tokens por entrada.
    """
    palavras = texto.split()
    chunks = []
    for i in range(0, len(palavras), tamanho):
        # Junta as palavras de cada janela em uma string
        chunks.append(" ".join(palavras[i:i + tamanho]))
    return chunks


def gerar_embedding(texto: str) -> list[float]:
    """Envia o texto para a API Mistral e retorna o vetor de embedding gerado.
    O modelo 'mistral-embed' produz vetores de 1024 dimensões.
    """
    result = mistral.embeddings.create(
        model="mistral-embed",
        inputs=[texto]
    )
    return result.data[0].embedding


# Lê o arquivo de textos (artigos científicos) que será indexado
with open("train.txt", "r", encoding="utf-8") as f:
    texto = f.read()

# Divide o texto completo em chunks de 500 palavras
chunks = chunk_text(texto)
print(f"{len(chunks)} chunks gerados.")

# Lista temporária para acumular pontos antes de fazer upsert em lote
points = []

for i, chunk in enumerate(chunks):
    try:
        # Gera o embedding do chunk atual
        embedding = gerar_embedding(chunk)

        # Cria o ponto Qdrant com ID sequencial, vetor e texto como payload
        points.append(PointStruct(
            id=i,
            vector=embedding,
            payload={"texto": chunk}  # Texto original armazenado para recuperação
        ))

        # Respeita o rate limit da API Mistral com pausa de 0.5s entre chamadas
        time.sleep(0.5)

        # A cada 100 chunks, envia o lote ao Qdrant e reinicia a lista
        if i % 100 == 0:
            print(f"{i}/{len(chunks)} indexados...")
            cliente.upsert(collection_name="Estudos", points=points)
            points = []  # Limpa o lote após o envio

    except Exception as e:
        print(f"Erro no chunk {i}: {e}")
        # Em caso de erro (ex: timeout), aguarda 10s antes de continuar
        time.sleep(10)
        continue

# Envia o lote final caso ainda haja pontos não enviados
if points:
    cliente.upsert(collection_name="Estudos", points=points)

print("Indexação concluída!")

# services/embedding_service.py
import os
import faiss
import pickle
from openai import OpenAI
from dotenv import load_dotenv
from typing import List
from sentence_transformers import SentenceTransformer
import logging

load_dotenv()

model = None


def _carregar_modelo():
    """Carrega o modelo de embeddings apenas quando necessário."""
    global model
    if model is None:
        try:
            # Força uso de CPU para evitar dependências de CUDA que podem faltar
            model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        except Exception as e:  # pragma: no cover - falha depende do ambiente
            logging.error(f"Erro ao carregar modelo de embeddings: {e}")
            model = None
    return model

INDEX_PATH = "embeddings/faiss_index/index.faiss"
DOCS_PATH = "embeddings/faiss_index/docs.pkl"
KNOWLEDGE_FOLDER = "conhecimento"

def carregar_documentos() -> List[str]:
    docs = []
    for nome_arquivo in os.listdir(KNOWLEDGE_FOLDER):
        caminho = os.path.join(KNOWLEDGE_FOLDER, nome_arquivo)
        with open(caminho, "r", encoding="utf-8") as f:
            docs.append(f.read())
    return docs

def criar_index():
    modelo = _carregar_modelo()
    if modelo is None:
        return

    docs = carregar_documentos()
    embeddings = modelo.encode(docs)
    
    index = faiss.IndexFlatL2(embeddings[0].shape[0])
    index.add(embeddings)

    with open(DOCS_PATH, "wb") as f:
        pickle.dump(docs, f)
    faiss.write_index(index, INDEX_PATH)

def buscar_contexto(pergunta: str, top_k=3):
    modelo = _carregar_modelo()
    if modelo is None:
        return ""

    if not os.path.exists(INDEX_PATH) or not os.path.exists(DOCS_PATH):
        logging.warning("Índice de embeddings não encontrado.")
        return ""

    index = faiss.read_index(INDEX_PATH)
    with open(DOCS_PATH, "rb") as f:
        docs = pickle.load(f)

    query_embedding = modelo.encode([pergunta])
    distancias, indices = index.search(query_embedding, top_k)
    resultados = [docs[i] for i in indices[0]]
    return "\n---\n".join(resultados)

# services/embedding_service.py
import os
import faiss
import pickle
from openai import OpenAI
from dotenv import load_dotenv
from typing import List
from sentence_transformers import SentenceTransformer

load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')  # substituto leve se não usar OpenAI

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
    docs = carregar_documentos()
    embeddings = model.encode(docs)
    
    index = faiss.IndexFlatL2(embeddings[0].shape[0])
    index.add(embeddings)

    with open(DOCS_PATH, "wb") as f:
        pickle.dump(docs, f)
    faiss.write_index(index, INDEX_PATH)

def buscar_contexto(pergunta: str, top_k=3):
    index = faiss.read_index(INDEX_PATH)
    with open(DOCS_PATH, "rb") as f:
        docs = pickle.load(f)

    query_embedding = model.encode([pergunta])
    distancias, indices = index.search(query_embedding, top_k)

    resultados = [docs[i] for i in indices[0]]
    return "\n---\n".join(resultados)
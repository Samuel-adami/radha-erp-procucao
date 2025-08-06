from whoosh import index
from whoosh.fields import Schema, TEXT
from whoosh.qparser import MultifieldParser
import os

INDEX_DIR = "whoosh_index"


def _get_or_create_index():
    if not os.path.exists(INDEX_DIR):
        os.makedirs(INDEX_DIR)
        schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True))
        return index.create_in(INDEX_DIR, schema)
    return index.open_dir(INDEX_DIR)


def indexar_documento(titulo: str, conteudo: str) -> None:
    ix = _get_or_create_index()
    writer = ix.writer()
    writer.add_document(title=titulo, content=conteudo)
    writer.commit()


def buscar_documentos(termo: str, limite: int = 10):
    ix = _get_or_create_index()
    with ix.searcher() as searcher:
        parser = MultifieldParser(["title", "content"], schema=ix.schema)
        query = parser.parse(termo)
        resultados = searcher.search(query, limit=limite)
        return [{"titulo": r["title"], "conteudo": r["content"], "score": r.score} for r in resultados]

import os
import json
import re
import subprocess
import logging
import textwrap
import argparse
from dotenv import load_dotenv

# Conexões Externas
import boto3
from sqlalchemy import create_engine, inspect

# LangChain - Core do RAG
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import StrOutputParser, Document

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Padrões de exclusão para escopos de código ao indexar documentos
EXCLUDE_PATTERNS = [
    "**/node_modules/**", "**/__pycache__/**", "**/dist/**", "**/build/**",
    "**/venv/**", "**/.git/**", "**/tests/**", "**/*test*/**",
    "**/migrations/**", "**/docs/**", "**/scripts/**", "**/examples/**",
    "**/marketing-digital-ia/frontend/**", "**/producao/frontend/**",
    "**/frontend-erp/public/**", "**/frontend-erp/src/assets/**",
    "**/marketing-digital-ia/.github/"
]

class AgenteERP_RAG_Focado:
    """
    Um agente orquestrador que utiliza RAG para analisar um escopo focado de um
    ERP, o schema do DB e a estrutura do S3, e opcionalmente executa o plano gerado.
    """
    def __init__(self, escopos_de_codigo: list[str], solicitacao_usuario: str = "") -> None:
        """
        Inicializa o agente com busca inteligente baseada em palavras-chave da solicitação.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("Inicializando o agente com escopo baseado na solicitação...")
        self.llm = ChatOpenAI(
            model_name="gpt-4o", temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.escopos_de_codigo = escopos_de_codigo
        self.vector_store = self._setup_vector_store(solicitacao_usuario)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 25})
        self.prompt_template = self._get_prompt_template()
        self.rag_chain = (
            {"contexto": self.retriever, "solicitacao_usuario": RunnablePassthrough()}
            | self.prompt_template
            | self.llm
            | StrOutputParser()
        )


    def _get_schema_do_banco(self) -> str | None:
        db_url = os.getenv("DATABASE_URL")
        if not db_url: return None
        try:
            self.logger.info("Conectando ao banco de dados para extrair schema...")
            engine = create_engine(db_url)
            with engine.connect() as conn:
                inspector = inspect(conn)
            schema_info = ""
            for schema_name in inspector.get_schema_names():
                if not (schema_name.startswith('pg_') or schema_name == 'information_schema'):
                    for table_name in inspector.get_table_names(schema=schema_name):
                        schema_info += f"--- Tabela: {schema_name}.{table_name} ---\n"
                        for column in inspector.get_columns(table_name, schema=schema_name):
                            schema_info += f"  - {column['name']} ({column['type']})\n"
                        schema_info += "\n"
            return schema_info
        except Exception as e:
            self.logger.error("Erro ao extrair schema do banco: %s", e)
            return None

    def _get_estrutura_s3(self) -> str | None:
        bucket_name = os.getenv("OBJECT_STORAGE_BUCKET")
        endpoint_url = os.getenv("OBJECT_STORAGE_ENDPOINT")
        if not all([bucket_name, endpoint_url, os.getenv("OBJECT_STORAGE_ACCESS_KEY"), os.getenv("OBJECT_STORAGE_SECRET_KEY")]):
            return None
        try:
            self.logger.info("Conectando ao Object Storage para listar objetos...")
            s3_client = boto3.client(
                's3', endpoint_url=endpoint_url,
                aws_access_key_id=os.getenv('OBJECT_STORAGE_ACCESS_KEY'),
                aws_secret_access_key=os.getenv('OBJECT_STORAGE_SECRET_KEY')
            )
            s3_structure = [f"--- Bucket S3: {bucket_name} ---"]
            continuation_token = None
            while True:
                params = {'Bucket': bucket_name}
                if continuation_token:
                    params['ContinuationToken'] = continuation_token
                resp = s3_client.list_objects_v2(**params)
                for obj in resp.get('Contents', []):
                    s3_structure.append(f"- {obj['Key']}")
                if not resp.get('IsTruncated'):
                    break
                continuation_token = resp.get('NextContinuationToken')
            return "\n".join(s3_structure) + "\n"
        except Exception as e:
            self.logger.error("Erro ao listar objetos do S3: %s", e)
            return None

    def _load_code_documents(self, solicitacao_usuario: str) -> list[Document]:
        """
        Carrega arquivos relevantes com base em palavras-chave da solicitação (via ripgrep),
        ao invés de carregar diretórios inteiros.
        """
        from langchain_community.document_loaders import TextLoader

        # Busca arquivos relevantes em cada diretório de escopo definido
        arquivos_set: set[str] = set()
        for path in self.escopos_de_codigo:
            encontrados = self.buscar_arquivos_por_palavra_chave(solicitacao_usuario, root_path=path)
            arquivos_set.update(encontrados)
        arquivos = list(arquivos_set)
        docs: list[Document] = []

        if not arquivos:
            self.logger.warning("Nenhum arquivo relevante encontrado com base na solicitação. Usando fallback padrão.")
            return []

        for arq in arquivos:
            try:
                loader = TextLoader(arq)
                docs.extend(loader.load())
            except Exception as e:
                self.logger.warning("Erro ao carregar arquivo %s: %s", arq, e)

        unique = {doc.metadata['source']: doc for doc in docs}
        self.logger.info("Total de %d arquivos relevantes encontrados.", len(unique))
        return list(unique.values())

    def buscar_arquivos_por_palavra_chave(self, solicitacao: str, root_path: str) -> list[str]:
        """
        Usa ripgrep para buscar arquivos com base em palavras-chave extraídas da solicitação natural do usuário.
        """
        import subprocess
        import re

        palavras = re.findall(r'\b\w+\b', solicitacao.lower())
        chaves = [p for p in palavras if len(p) > 4 and p not in {
            "corrija", "falha", "erro", "importacao", "corrigir", "problema",
            "codigo", "funcao", "metodo", "arquivo", "projeto", "sistema"
        }]

        if not chaves:
            print("⚠️ Nenhuma palavra-chave forte detectada. Tentando com termos genéricos.")
            chaves = palavras  # tenta tudo

        encontrados = set()
        for chave in chaves:
            try:
                resultado = subprocess.run(
                    ["rg", "-l", "-i", chave, root_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    check=False
                )
                for linha in resultado.stdout.strip().split("\n"):
                    if linha.strip() and os.path.isfile(linha.strip()):
                        encontrados.add(linha.strip())
            except FileNotFoundError:
                print("❌ Ripgrep (rg) não instalado. Instale com: sudo apt install ripgrep")
                break

        return list(encontrados)

    def _load_external_documents(self, docs: list[Document]) -> list[Document]:
        """Anexa documentos externos de schema do banco e estrutura do S3."""
        extras: list[Document] = []
        if schema_text := self._get_schema_do_banco():
            extras.append(Document(page_content=schema_text, metadata={"source": "database_schema"}))
        if s3_text := self._get_estrutura_s3():
            extras.append(Document(page_content=s3_text, metadata={"source": "s3_structure"}))
        return docs + extras

    def _split_and_index_documents(self, docs: list[Document]) -> Chroma:
        """Divide documento em chunks e cria o vector store."""
        if not docs:
            self.logger.warning("Nenhum documento para indexar.")
            return Chroma(embedding_function=self.embeddings)

        splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
        splits = splitter.split_documents(docs)
        self.logger.info("Total de %d chunks gerados para indexar.", len(splits))
        store = Chroma(embedding_function=self.embeddings)
        for i in range(0, len(splits), 400):
            batch = splits[i : i + 400]
            store.add_documents(documents=batch)
            self.logger.debug("Lote %d/%d indexado.", i // 400 + 1, (len(splits) - 1) // 400 + 1)
        self.logger.info("Vector Store criado com sucesso.")
        return store
            
    def _setup_vector_store(self, solicitacao_usuario: str) -> Chroma:
        """Orquestra a criação do vector store com base em busca inteligente por palavras-chave."""
        self.logger.info("Buscando arquivos relevantes com base na solicitação...")
        code_docs = self._load_code_documents(solicitacao_usuario)
        all_docs = self._load_external_documents(code_docs)
        return self._split_and_index_documents(all_docs)


    def _get_prompt_template(self) -> PromptTemplate:
        template = textwrap.dedent("""
        Você é um Engenheiro de Software Sênior especialista em arquitetura de sistemas ERP,
        atuando como um agente de IA para auxiliar no desenvolvimento do 'radha-erp-producao'.
        Sua tarefa é analisar uma solicitação e, com base nos contextos fornecidos, gerar uma resposta JSON
        que contenha DUAS CHAVES: "plano_execucao_json" e "plano_execucao_texto".

        **Regras Estritas e Inegociáveis:**
        1.  **Ultra Especificidade:** Sua análise e plano de ação DEVEM referenciar os nomes completos dos arquivos e módulos encontrados no contexto (ex: 'frontend-erp/src/modules/comercial/components/Projeto3D.vue', 'comercial-backend/services/gabster.py'). NÃO use nomes genéricos como 'backend' ou 'frontend' no campo 'component'. Use o nome do diretório principal do módulo (ex: 'comercial-backend', 'frontend-erp').
        2.  **Nível de Código:** Ao descrever uma ação, se o contexto fornecer nomes de funções, classes ou métodos dentro de um arquivo, você DEVE mencioná-los para aumentar a precisão.
        3.  **Foco na Lógica:** Sua análise deve ir além de simplesmente repetir a solicitação. Investigue a lógica potencial com base nos trechos de código fornecidos e proponha ações concretas de depuração ou implementação.
        4.  **Formato de Saída:** Sua resposta DEVE ser um único objeto JSON válido contendo as duas chaves solicitadas ("plano_execucao_json" e "plano_execucao_texto"), e nada mais. Não inclua texto explicativo como "```json" no início.

        **Contexto do Sistema (Trechos Relevantes de Código, Banco de Dados e S3):**
        ```
        {contexto}
        ```

        **Solicitação do Desenvolvedor:**
        ```
        {solicitacao_usuario}
        ```

        **Sua Resposta (Formato JSON com as duas chaves obrigatórias):**
        """)
        return PromptTemplate(
            template=template,
            input_variables=["contexto", "solicitacao_usuario"],
        )

    def gerar_plano(self, solicitacao_usuario: str) -> dict:
        """
        Gera o plano de execução JSON a partir da solicitação do usuário,
        usando RAG e parsing robusto de JSON.
        """
        self.logger.info("Gerando plano de ação com RAG...")
        try:
            response_str = self.rag_chain.invoke(solicitacao_usuario)
            decoder = json.JSONDecoder()
            obj, _ = decoder.raw_decode(response_str)
            self.logger.info("Plano de ação gerado com sucesso!")
            return obj
        except json.JSONDecodeError as e:
            self.logger.error("Resposta da IA não pôde ser decodificada: %s", e)
            self.logger.debug("Resposta bruta da IA: %s", response_str)
            return {"erro": "A resposta da IA não pôde ser decodificada para JSON.", "resposta_bruta": response_str}
        except Exception as e:
            self.logger.exception("Erro inesperado ao gerar plano")
            return {"erro": str(e)}

def main():
    """Função principal: interage com o usuário para seleção de módulo e ciclo de solicitações."""
    parser = argparse.ArgumentParser(description="Agente ERP RAG focalizado")
    parser.add_argument(
        "--path-erp",
        default=os.getenv("PATH_DO_ERP", ""), 
        help="Caminho raiz do projeto ERP"
    )
    args = parser.parse_args()

    root = args.path_erp
    if not os.path.isdir(root):
        logging.error("Caminho principal do ERP não encontrado em '%s'", root)
        return

    ignored = {".git", ".vscode", "venv", "scripts", "docs"}
    try:
        modules = [
            d for d in os.listdir(root)
            if os.path.isdir(os.path.join(root, d)) and d not in ignored and not d.startswith(".")
        ]
    except FileNotFoundError:
        modules = []

    if not modules:
        logging.error("Nenhum módulo de projeto encontrado no diretório principal.")
        return

    print("Selecione o módulo para análise:")
    for i, mod in enumerate(modules, 1):
        print(f"  [{i}] {mod}")

    choice = 0
    while not (1 <= choice <= len(modules)):
        try:
            choice = int(input(f"Digite o número da sua escolha (1-{len(modules)}): "))
        except ValueError:
            print("Entrada inválida.")

    selected = modules[choice - 1]
    focus = [os.path.join(root, selected)]
    print("Escopo de análise:", selected)

    agent = None
    print("Agente pronto. Digite sua solicitação ou 'sair' para terminar.")

    while True:
        req = input("> ")
        if req.lower() in {"sair", "exit", "quit"}:
            print("Encerrando.")
            break
        if not req.strip():
            continue

        agent = AgenteERP_RAG_Focado(escopos_de_codigo=focus, solicitacao_usuario=req)
        plan = agent.gerar_plano(req)


        plan = agent.gerar_plano(req)
        if plan and "erro" not in plan:
            print(json.dumps(plan, indent=2, ensure_ascii=False))

            resposta_exec = input("\n> Deseja tentar executar este plano automaticamente com o Codex CLI? (s/n): ").lower()
            if resposta_exec in ['s', 'sim']:
                plano_texto = plan.get("plano_execucao_texto", "")
                executar_plano_com_codex(plano_texto)

        
def executar_plano_com_codex(plano_texto: str, markdown_path="plano_de_acao.md", auto_commit=True):
    """
    Executa o plano com Codex CLI, atualiza markdown, salva logs com timestamp e cria commit automático.
    """
    import time
    import subprocess
    import os
    import re
    import threading
    import itertools
    import sys
    from tqdm import tqdm
    from datetime import datetime

    if not plano_texto.strip():
        print("⚠️ Plano está vazio. Nada a executar.")
        return

    prompt_codex = f"""
Contexto: agente gerou plano para o projeto Radha ERP.
Tarefa: interprete e execute o plano abaixo, criando ou modificando arquivos conforme necessário.

Plano:
{plano_texto}
""".strip()

    print("\n🚀 Enviando plano ao Codex CLI (tempo estimado: até 5 minutos)...\n")

    try:
        # Garante criação do markdown
        if not os.path.exists(markdown_path):
            with open(markdown_path, "w", encoding="utf-8") as f_md:
                f_md.write(f"""---
data: {time.strftime('%Y-%m-%d')}
autor: {os.getenv("USER", "agente")}
modulo: indefinido
tags: [plano, acao, radha-erp]
---

# Plano de Ação: Execução automática com Codex CLI

## Contexto
Gerado automaticamente pelo agente.

## Objetivo
Executar automaticamente as instruções planejadas.

## Passos para Execução
""")
                # Divide o texto do plano em passos numerados ou com '- '
                passos = re.split(r'\n(?:\d+\.\s+|- )', plano_texto.strip())
                for passo in passos:
                    if passo.strip():
                        f_md.write(f"- [ ] {passo.strip()}\n")
                f_md.write("\n## Critérios de Sucesso\n- [ ] Todos os passos foram executados\n")

        # Define caminho de log com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("logs", exist_ok=True)
        caminho_resposta = os.path.join("logs", f"resposta_codex_{timestamp}.txt")
        output_lines = []

        def marcar_passos_no_markdown(linha_codex):
            if not os.path.exists(markdown_path):
                return
            with open(markdown_path, "r", encoding="utf-8") as f_md:
                conteudo = f_md.read()
            alterado = False
            padrao_passos = re.findall(r"- \[ \] (.+)", conteudo)
            for passo in padrao_passos:
                palavras = passo.strip().split()[:3]
                if all(p.lower() in linha_codex.lower() for p in palavras):
                    conteudo = re.sub(
                        rf"- \[ \] {re.escape(passo)}",
                        f"- [x] {passo}",
                        conteudo
                    )
                    alterado = True
                    break
            if alterado:
                with open(markdown_path, "w", encoding="utf-8") as f_md:
                    f_md.write(conteudo)

        # Inicia Codex CLI
        proc = subprocess.Popen(
            ["codex", "--full-auto"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        proc.stdin.write(prompt_codex)
        proc.stdin.close()

        def ler_stdout():
            for linha in proc.stdout:
                tqdm.write(linha.strip())
                output_lines.append(linha)
                marcar_passos_no_markdown(linha)

        def ler_stderr():
            for err in proc.stderr:
                tqdm.write(f"❌ {err.strip()}")
                output_lines.append(err)

        t_stdout = threading.Thread(target=ler_stdout)
        t_stderr = threading.Thread(target=ler_stderr)
        t_stdout.start()
        t_stderr.start()

        start_time = time.time()
        barra = tqdm(total=300, desc="Codex CLI (s)", bar_format="{l_bar}{bar}| {remaining}")
        try:
            while proc.poll() is None:
                time.sleep(1)
                barra.update(1)
                if time.time() - start_time > 300:
                    proc.terminate()
                    tqdm.write("\n⏰ Tempo limite excedido. Codex encerrado.")
                    break
        except KeyboardInterrupt:
            proc.terminate()
            tqdm.write("\n🛑 Execução interrompida manualmente.")
        finally:
            barra.close()

        t_stdout.join()
        t_stderr.join()

        with open(caminho_resposta, "w", encoding="utf-8") as f_out:
            for linha in output_lines:
                f_out.write(linha)

        print(f"\n✅ Codex CLI finalizado.")
        print(f"📝 Log salvo em: {caminho_resposta}")
        print(f"📄 Markdown atualizado: {markdown_path}")

        # Verifica modificações antes do commit
        if auto_commit:
            try:
                status = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
                if status:
                    subprocess.check_call(["git", "add", "."], stdout=subprocess.DEVNULL)
                    subprocess.check_call(["git", "commit", "-m", "🤖 Execução automática via Codex CLI - plano aplicado"], stdout=subprocess.DEVNULL)
                    print("✅ Alterações versionadas com sucesso (commit automático criado).")
                else:
                    print("ℹ️ Nenhuma alteração detectada no projeto. Nada a versionar.")
            except subprocess.CalledProcessError:
                print("⚠️ Commit automático falhou. Verifique se está em um repositório Git.")
            except Exception as e:
                print(f"⚠️ Erro ao tentar realizar commit: {e}")

    except FileNotFoundError:
        print("❌ Codex CLI não encontrado. Verifique se está no PATH.")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()

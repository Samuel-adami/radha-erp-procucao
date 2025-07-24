import os
import json
import re
import subprocess
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

class AgenteERP_RAG_Focado:
    """
    Um agente orquestrador que utiliza RAG para analisar um escopo focado de um
    ERP, o schema do DB e a estrutura do S3, e opcionalmente executa o plano gerado.
    """
    def __init__(self, escopos_de_codigo: list[str]):
        print("\nInicializando o agente com o escopo focado...")
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        
        self.escopos_de_codigo = escopos_de_codigo
        self.vector_store = self._setup_vector_store()
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
            print("Conectando ao banco de dados para extrair schema...")
            engine = create_engine(db_url)
            inspector = inspect(engine)
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
            print(f"Erro ao extrair schema do banco: {e}")
            return None

    def _get_estrutura_s3(self) -> str | None:
        bucket_name = os.getenv("OBJECT_STORAGE_BUCKET")
        endpoint_url = os.getenv("OBJECT_STORAGE_ENDPOINT")
        if not all([bucket_name, endpoint_url, os.getenv("OBJECT_STORAGE_ACCESS_KEY"), os.getenv("OBJECT_STORAGE_SECRET_KEY")]):
            return None
        try:
            print("Conectando ao Object Storage para listar objetos...")
            s3_client = boto3.client('s3', endpoint_url=endpoint_url, aws_access_key_id=os.getenv('OBJECT_STORAGE_ACCESS_KEY'), aws_secret_access_key=os.getenv('OBJECT_STORAGE_SECRET_KEY'))
            response = s3_client.list_objects_v2(Bucket=bucket_name)
            s3_structure = f"--- Bucket S3: {bucket_name} ---\n"
            s3_structure += "".join(f"- {obj['Key']}\n" for obj in response.get('Contents', []))
            return s3_structure
        except Exception as e:
            print(f"Erro ao listar objetos do S3: {e}")
            return None

    def _setup_vector_store(self) -> Chroma:
        print("Criando novo Vector Store para a sessão atual...")
        print("Carregando arquivos de código do escopo selecionado...")
        all_docs = []
        for path in self.escopos_de_codigo:
            if not os.path.isdir(path):
                print(f"Aviso: O caminho do escopo '{path}' não existe. Ignorando.")
                continue
            print(f"  - Lendo diretório: {path}")
            exclude_patterns = ["**/node_modules/**", "**/__pycache__/**", "**/dist/**", "**/build/**", "**/venv/**", "**/.git/**", "**/tests/**", "**/*test*/**"]
            loader = DirectoryLoader(path, glob="**/*", loader_cls=TextLoader, show_progress=True, use_multithreading=True, silent_errors=True, recursive=True, exclude=exclude_patterns)
            all_docs.extend(loader.load())
        
        unique_docs = list({doc.metadata['source']: doc for doc in all_docs}.values())
        print(f"Total de {len(unique_docs)} arquivos de código únicos carregados.")
        docs_externos = []
        if schema_banco_texto := self._get_schema_do_banco():
            docs_externos.append(Document(page_content=schema_banco_texto, metadata={"source": "database_schema"}))
        if estrutura_s3_texto := self._get_estrutura_s3():
            docs_externos.append(Document(page_content=estrutura_s3_texto, metadata={"source": "s3_structure"}))
        todos_os_docs = unique_docs + docs_externos
        if not todos_os_docs:
            print("Nenhum documento encontrado para indexar.")
            return Chroma(embedding_function=self.embeddings)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
        splits = text_splitter.split_documents(todos_os_docs)
        print(f"Total de {len(splits)} chunks de documentos para indexar.")
        print("Criando embeddings em memória e em lotes...")
        vector_store = Chroma(embedding_function=self.embeddings)
        batch_size = 400 
        for i in range(0, len(splits), batch_size):
            batch = splits[i:i + batch_size]
            vector_store.add_documents(documents=batch)
            print(f"  - Lote {i // batch_size + 1} de {(len(splits) - 1) // batch_size + 1} processado.")
        print("Vector Store da sessão criado com sucesso!")
        return vector_store

    def _get_prompt_template(self) -> PromptTemplate:
        template = """
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
        """
        return PromptTemplate(
            template=template,
            input_variables=["contexto", "solicitacao_usuario"],
        )

    def gerar_plano(self, solicitacao_usuario: str):
        print("\nGerando plano de ação com RAG...")
        try:
            response_str = self.rag_chain.invoke(solicitacao_usuario)
            match = re.search(r'\{.*\}|\[.*\]', response_str, re.DOTALL)
            if not match:
                raise json.JSONDecodeError("Nenhum JSON válido encontrado na resposta da IA.", response_str, 0)
            clean_json_str = match.group(0)
            plano_json = json.loads(clean_json_str)
            print("Plano de ação gerado com sucesso!")
            return plano_json
        except json.JSONDecodeError as e:
            print(f"Erro: A resposta da IA não é um JSON válido ou não foi encontrado. {e}")
            print("Resposta recebida:", response_str)
            return {"erro": "A resposta da IA não pôde ser decodificada para JSON.", "resposta_bruta": response_str}
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
            return {"erro": str(e)}

# --- PONTO DE ENTRADA FINAL COM INTEGRAÇÃO CODEX CLI ---
if __name__ == "__main__":
    PATH_DO_ERP = "/home/samuel/radha-erp-producao"

    if not os.path.isdir(PATH_DO_ERP):
        print(f"ATENÇÃO: O caminho principal do ERP não foi encontrado em '{PATH_DO_ERP}'")
    else:
        try:
            pastas_a_ignorar = {'.git', '.vscode', 'venv', 'scripts', 'docs'}
            todos_os_modulos = [d for d in os.listdir(PATH_DO_ERP) if os.path.isdir(os.path.join(PATH_DO_ERP, d)) and d not in pastas_a_ignorar and not d.startswith('.')]
        except FileNotFoundError:
            todos_os_modulos = []

        if not todos_os_modulos:
            print("Nenhum módulo de projeto encontrado no diretório principal.")
        else:
            print("\n✅ Agente inicializado. Para focar a análise, selecione o módulo principal para esta sessão:")
            for i, modulo in enumerate(todos_os_modulos, 1):
                print(f"  [{i}] {modulo}")
            
            escolha = -1
            while escolha < 1 or escolha > len(todos_os_modulos):
                try:
                    escolha = int(input(f"\nDigite o número da sua escolha (1-{len(todos_os_modulos)}): "))
                except ValueError:
                    print("Por favor, digite um número válido.")

            modulo_selecionado = todos_os_modulos[escolha - 1]
            nome_do_modulo_chave = modulo_selecionado.replace('-backend', '').replace('_backend', '')
            caminho_modulos_frontend_pai = os.path.join(PATH_DO_ERP, "frontend-erp", "src", "modules")
            caminho_frontend_modulo_final = None
            if os.path.isdir(caminho_modulos_frontend_pai):
                for pasta_frontend in os.listdir(caminho_modulos_frontend_pai):
                    if pasta_frontend.lower() == nome_do_modulo_chave.lower():
                        caminho_frontend_modulo_final = os.path.join(caminho_modulos_frontend_pai, pasta_frontend)
                        break
            
            escopo_final = [os.path.join(PATH_DO_ERP, modulo_selecionado)]
            escopo_display = [modulo_selecionado]
            if caminho_frontend_modulo_final:
                escopo_final.append(caminho_frontend_modulo_final)
                escopo_display.append(os.path.relpath(caminho_frontend_modulo_final, PATH_DO_ERP))
            else:
                print(f"Aviso: Submódulo de frontend correspondente a '{nome_do_modulo_chave}' não encontrado. Analisando apenas o backend.")
            
            print(f"\nIniciando indexação para o escopo: {', '.join(escopo_display)}...")
            agente = AgenteERP_RAG_Focado(escopos_de_codigo=escopo_final)
            
            print("\n" + "="*60)
            print("✅ Agente pronto. Digite sua solicitação ou 'sair' para terminar.")
            print("="*60)

            while True:
                solicitacao = input("> ")
                if solicitacao.lower() in ['sair', 'exit', 'quit']:
                    print("Encerrando o agente. Até logo!")
                    break
                if not solicitacao:
                    continue

                plano_completo = agente.gerar_plano(solicitacao)

                if plano_completo and "erro" not in plano_completo:
                    print("\n" + "="*28 + " PLANO DE AÇÃO (JSON) " + "="*29)
                    print(json.dumps(plano_completo.get("plano_execucao_json", {}), indent=2, ensure_ascii=False))
                    print("="*80)

                    plano_texto = plano_completo.get("plano_execucao_texto", "")
                    
                    if plano_texto:
                        resposta_md = input("\n> Deseja salvar o plano em texto (.md)? (s/n): ").lower()
                        if resposta_md in ['s', 'sim']:
                            from datetime import datetime
                            diretorio_scripts = os.path.dirname(os.path.realpath(__file__))
                            os.makedirs(diretorio_scripts, exist_ok=True)
                            caminho_arquivo_plano = os.path.join(diretorio_scripts, "plano_de_acao.md")
                            data_hoje = datetime.now().strftime("%Y-%m-%d")
                            frontmatter = f"""---\ndata: {data_hoje}\nautor: {os.getenv('USER') or os.getenv('USERNAME') or 'desconhecido'}\nmodulo: {modulo_selecionado if 'modulo_selecionado' in locals() else 'N/A'}\ntags: [plano, acao, radha-erp]\n---\n"""
                            markdown = f"{frontmatter}\n# Plano de Ação: {solicitacao}\n\n## Contexto\nDescreva o cenário, arquivos e funções envolvidos.\n\n## Objetivo\nExplique o que deve ser alcançado.\n\n## Passos para Execução\n" 
                            # Tenta converter passos do plano_texto em checklist
                            for idx, linha in enumerate(plano_texto.splitlines(), 1):
                                if linha.strip() and not linha.strip().startswith('#'):
                                    markdown += f"- [ ] {linha.strip()}\n"
                            markdown += "\n## Critérios de Sucesso\n- [ ] Validar se todos os passos foram concluídos com sucesso\n\n## Observações\n- Adapte conforme necessário para seu fluxo.\n"
                            with open(caminho_arquivo_plano, "w", encoding="utf-8") as f:
                                f.write(markdown)
                            print(f"\n✅ Plano em texto salvo em '{caminho_arquivo_plano}'")
                            try:
                                subprocess.run(["code", caminho_arquivo_plano], check=True)
                            except (subprocess.CalledProcessError, FileNotFoundError):
                                pass

                        # VVVVVV NOVA LÓGICA DE EXECUÇÃO COM CODEX CLI VVVVVV
                        resposta_exec = input("\n> Deseja tentar executar este plano automaticamente com o Codex CLI? (s/n): ").lower()
                        if resposta_exec in ['s', 'sim']:
                            prompt_codex = f"""
Contexto: agente gerado plano para o projeto Radha ERP.
Tarefa: interprete e execute o plano abaixo, criando ou modificando arquivos conforme necessário.

Plano:
{plano_texto}
"""
                            print("\n🚀 Enviando plano ao Codex CLI (isso pode levar um tempo)...")
                            import time
                            try:
                                proc = subprocess.Popen(
                                    ["codex", "--full-auto", prompt_codex.strip()],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True
                                )
                                diretorio_scripts = os.path.dirname(os.path.realpath(__file__))
                                caminho_resposta = os.path.join(diretorio_scripts, "resposta_codex.txt")
                                with open(caminho_resposta, "w", encoding="utf-8") as f:
                                    inicio = time.time()
                                    while True:
                                        if proc.poll() is not None:
                                            break
                                        linha = proc.stdout.readline()
                                        if linha == '' and proc.poll() is not None:
                                            break
                                        if linha:
                                            print(linha, end='')
                                            f.write(linha)
                                            f.flush()
                                        if time.time() - inicio > 300:
                                            proc.terminate()
                                            print("\n⏰ Tempo limite excedido: o Codex CLI demorou mais de 5 minutos para responder. O processo foi interrompido.")
                                            break
                                    # Também leia o restante do stderr
                                    for err in proc.stderr:
                                        print(err, end='')
                                print(f"\n✅ Resposta do Codex salva em '{caminho_resposta}'")
                            except FileNotFoundError:
                                print("\n❌ Erro: O comando 'codex' não foi encontrado. Verifique se o Codex CLI está instalado e no seu PATH.")
                            except Exception as e:
                                print(f"\n❌ Erro durante a execução do Codex CLI: {e}")
                        # ^^^^^^ NOVA LÓGICA DE EXECUÇÃO COM CODEX CLI ^^^^^^
                else:
                    print("\n--- ERRO AO GERAR PLANO ---")
                    print(json.dumps(plano_completo, indent=2, ensure_ascii=False))

                print("\nPróxima solicitação ou 'sair' para terminar.")
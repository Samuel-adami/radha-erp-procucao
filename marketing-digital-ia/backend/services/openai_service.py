import os
import asyncio
import logging
import time
from dotenv import load_dotenv
import openai

# Detecta se a nova interface assíncrona da biblioteca OpenAI está
# disponível. Em ambientes com versões mais antigas do pacote, a
# importação abaixo falhará e usaremos a API síncrona como fallback.
try:  # pragma: no cover - compatibilidade dinâmica
    from openai import AsyncOpenAI, OpenAIError
    _use_async_client = True
except Exception:  # Versões < 1.0 não possuem AsyncOpenAI
    from openai.error import OpenAIError  # type: ignore
    AsyncOpenAI = None
    _use_async_client = False
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
import requests
import re

# 🔄 Variáveis de ambiente
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

# 🔧 Cliente OpenAI
if _use_async_client and API_KEY:
    client = AsyncOpenAI(api_key=API_KEY, base_url=API_BASE)
else:
    # Fallback para versões antigas da biblioteca
    if API_KEY:
        openai.api_key = API_KEY  # type: ignore
        try:
            openai.api_base = API_BASE  # type: ignore
        except Exception:
            pass
    client = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Remove referências de arquivos (ex.: [4:0+identidade.md]) das respostas
def remover_referencias(texto: str) -> str:
    return re.sub(r"\[\d+:\d+\+[^\]]+\]", "", texto).strip()

# 🎯 Geração de resposta via Assistant com arquivos
async def gerar_resposta(mensagem: str, id_assistant: str) -> str:
    if client is None:
        if not API_KEY:
            logging.warning("OPENAI_API_KEY não configurada.")
        else:
            logging.warning("Biblioteca OpenAI não suporta recursos assíncronos.")
        return "Serviço de IA indisponível no momento."

    try:
        thread = await client.beta.threads.create()
        await client.beta.threads.messages.create(thread_id=thread.id, role="user", content=mensagem)
        run = await client.beta.threads.runs.create(thread_id=thread.id, assistant_id=id_assistant)

        inicio = time.time()
        while True:
            status = await client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if status.status == "completed":
                break
            if status.status in ("failed", "cancelled", "expired"):
                logging.error(f"Execução falhou com status: {status.status}")
                return "Não foi possível obter uma resposta no momento."
            if time.time() - inicio > 60:
                logging.error("Timeout ao aguardar resposta do Assistant.")
                return "Tempo esgotado. Tente novamente mais tarde."
            await asyncio.sleep(1)

        messages = await client.beta.threads.messages.list(thread_id=thread.id)
        respostas = [
            remover_referencias(msg.content[0].text.value)
            for msg in messages.data if msg.role == "assistant"
        ]
        respostas = [r for r in map(str.strip, respostas) if r]
        return "\n\n".join(respostas) if respostas else "O assistente não retornou uma resposta."

    except OpenAIError as e:
        logging.error(f"Erro OpenAI: {e}")
        return "Instabilidade técnica ao acessar o assistente. Tente novamente mais tarde."
    except Exception as e:
        logging.exception(f"Erro inesperado: {e}")
        return "Erro inesperado ao processar a mensagem."

# 🖼️ Geração de imagem DALL·E 3
async def gerar_imagem(prompt: str) -> str:
    if not API_KEY:
        logging.warning("OPENAI_API_KEY não configurada. Impossível gerar imagem.")
        return ""

    try:
        if _use_async_client and client is not None:
            resposta = await client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            return resposta.data[0].url
        else:
            def _sync_call():
                resp = openai.Image.create(prompt=prompt, n=1, size="1024x1024")  # type: ignore
                return resp["data"][0]["url"]

            return await asyncio.to_thread(_sync_call)
    except OpenAIError as e:
        logging.error(f"Erro ao gerar imagem com DALL·E: {e}")
        return ""
    except Exception as e:
        logging.exception(f"Falha inesperada ao gerar imagem: {e}")
        return ""

# 📝 Sobrepor texto na imagem
def gerar_imagem_com_texto(imagem_url: str, texto: str) -> str:
    try:
        response = requests.get(imagem_url)
        imagem = Image.open(BytesIO(response.content)).convert("RGBA")
        largura, altura = imagem.size

        # Camada transparente
        txt_layer = Image.new("RGBA", imagem.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        # Fonte
        try:
            fonte = ImageFont.truetype("DejaVuSans-Bold.ttf", size=40)
        except:
            fonte = ImageFont.load_default()

        text_width, text_height = draw.textsize(texto, font=fonte)
        x = (largura - text_width) / 2
        y = altura - text_height - 40

        # Sombra e texto
        draw.text((x + 2, y + 2), texto, font=fonte, fill="black")
        draw.text((x, y), texto, font=fonte, fill="white")

        imagem_final = Image.alpha_composite(imagem, txt_layer)

        buffer = BytesIO()
        imagem_final.save(buffer, format="PNG")
        imagem_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{imagem_base64}"

    except Exception as e:
        logging.error(f"Erro ao sobrepor texto na imagem: {e}")
        return ""

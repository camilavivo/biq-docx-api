# Garante permissões seguras ao iniciar
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
try:
    open(os.path.join(DOWNLOAD_DIR, ".test"), "w").close()
except Exception as e:
    print(f"⚠️ Aviso: não foi possível gravar em {DOWNLOAD_DIR} - {e}")

# -*- coding: utf-8 -*-
"""
API BIQ ADVFarma — Preenche o Boletim de Incidência da Qualidade (Anexo 01 POP-NO-GQ-157)
"""

import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Response, Request
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles

from biq_filler import preencher_biq_from_payload


# =========================================
# CONFIGURAÇÕES GERAIS
# =========================================
API_KEY = os.getenv("BIQ_API_KEY")  # chave opcional de segurança
# Caminhos seguros dentro do container Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.getenv("BIQ_TEMPLATE_PATH", os.path.join(BASE_DIR, "MODELO_BIQ.docx"))
DOWNLOAD_DIR = os.getenv("BIQ_DOWNLOAD_DIR", os.path.join(BASE_DIR, "downloads"))
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# garante que a pasta de downloads existe
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="ADV BIQ Filler API",
    version="2.0.1",
    description=(
        "API para geração automática do Boletim de Incidência da Qualidade (BIQ) "
        "em conformidade com o Anexo 01 do POP-NO-GQ-157 e padrões de BPF."
    ),
)

# rota estática para download dos arquivos gerados
app.mount("/downloads", StaticFiles(directory=DOWNLOAD_DIR), name="downloads")


# =========================================
# MODELO DE ENTRADA – Pydantic
# =========================================
class BIQPayload(BaseModel):
    dados_incidentes: dict
    justificativa_texto: str
    descricao_incidente: str
    acoes: list
    equipe: list
    follow_up_texto: str
    numero_biq: str


# =========================================
# FUNÇÃO DE AUTENTICAÇÃO (API KEY)
# =========================================
def _check_api_key(x_api_key: Optional[str]):
    """Valida a API Key se configurada."""
    if not API_KEY:
        return  # sem API_KEY = API aberta
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida.")


# =========================================
# HEALTHCHECK
# =========================================
@app.get("/health")
def health():
    """Rota de verificação de status da API."""
    exists = os.path.exists(TEMPLATE_PATH)
    return {
        "status": "ok",
        "msg": "API BIQ online",
        "versao": "2.0.1",
        "template_encontrado": exists,
        "template_path": TEMPLATE_PATH,
    }


# =========================================
# ROTA 1 – GERA E RETORNA O DOCX DIRETO
# =========================================
@app.post(
    "/fill",
    response_class=Response,
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {}
            }
        }
    },
)
def fill(payload: BIQPayload, x_api_key: Optional[str] = Header(default=None)):
    """
    Gera o arquivo BIQ e retorna o binário diretamente (para download direto).
    """
    _check_api_key(x_api_key)

    if not os.path.exists(TEMPLATE_PATH):
        raise HTTPException(status_code=500, detail=f"Template não encontrado: {TEMPLATE_PATH}")

    docx_bytes = preencher_biq_from_payload(TEMPLATE_PATH, payload.model_dump())

    headers = {"Content-Disposition": 'attachment; filename="FORMULARIO_BIQ_PRENCHIDO.docx"'}
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )


# =========================================
# ROTA 2 – RETORNA ARQUIVO EM BASE64
# =========================================
@app.post("/fill_b64")
def fill_b64(payload: BIQPayload, x_api_key: Optional[str] = Header(default=None)):
    """
    Gera o BIQ e retorna o arquivo codificado em Base64 (útil para integrações).
    """
    import base64

    _check_api_key(x_api_key)

    if not os.path.exists(TEMPLATE_PATH):
        raise HTTPException(status_code=500, detail=f"Template não encontrado: {TEMPLATE_PATH}")

    docx_bytes = preencher_biq_from_payload(TEMPLATE_PATH, payload.model_dump())
    b64 = base64.b64encode(docx_bytes).decode("utf-8")

    return {
        "filename": "FORMULARIO_BIQ_PRENCHIDO.docx",
        "filedata": b64,
        "status": "success",
    }


# =========================================
# ROTA 3 – GERA O DOCX E SALVA NO SERVIDOR (RETORNA URL)
# =========================================
@app.post("/fill_url")
def fill_url(request: Request, payload: BIQPayload, x_api_key: Optional[str] = Header(default=None)):
    """
    Gera o BIQ, salva no servidor e retorna a URL pública para download.
    """
    _check_api_key(x_api_key)

    if not os.path.exists(TEMPLATE_PATH):
        raise HTTPException(status_code=500, detail=f"Template não encontrado: {TEMPLATE_PATH}")

    # Geração do arquivo
    docx_bytes = preencher_biq_from_payload(TEMPLATE_PATH, payload.model_dump())

    # Nome único
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    unique = uuid.uuid4().hex[:8]
    filename = f"FORMULARIO_BIQ_PRENCHIDO_{stamp}_{unique}.docx"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    # Garante que a pasta existe (Render pode limpá-la ao hibernar)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Grava o arquivo no disco
    with open(filepath, "wb") as f:
        f.write(docx_bytes)

    # Monta URL pública
    base_url = str(request.base_url).rstrip("/")
    file_url = f"{base_url}/downloads/{filename}"

    return {
        "filename": filename,
        "fileUrl": file_url,
        "status": "success",
        "mensagem": "Arquivo BIQ gerado com sucesso e disponível para download.",
    }

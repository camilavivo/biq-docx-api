# -*- coding: utf-8 -*-
"""
API BIQ ADVFarma — Geração Automática do Boletim de Incidência da Qualidade (BIQ)
Versão: 2.1.0
"""

import os
import uuid
import base64
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Response, Request
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles
from starlette.responses import JSONResponse

from biq_filler import preencher_biq_from_payload


# =========================================
# CONFIGURAÇÕES GERAIS
# =========================================
API_KEY = os.getenv("BIQ_API_KEY")  # opcional
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.getenv("BIQ_TEMPLATE_PATH", os.path.join(BASE_DIR, "MODELO_BIQ.docx"))
DOWNLOAD_DIR = os.getenv("BIQ_DOWNLOAD_DIR", os.path.join(BASE_DIR, "downloads"))

# Garantir diretório de downloads
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Log inicial — ajuda no Render
print(f"🧩 TEMPLATE_PATH definido como: {TEMPLATE_PATH}")
print(f"📁 DOWNLOAD_DIR definido como: {DOWNLOAD_DIR}")

if os.path.exists(TEMPLATE_PATH):
    print(f"✅ Modelo BIQ encontrado em: {TEMPLATE_PATH}")
else:
    print(f"⚠️ Modelo BIQ NÃO encontrado em: {TEMPLATE_PATH}")


# =========================================
# FASTAPI CONFIG
# =========================================
app = FastAPI(
    title="ADV BIQ Filler API",
    version="2.1.0",
    description="API para geração automática do Boletim de Incidência da Qualidade (BIQ) conforme POP-NO-GQ-157."
)

# Expor rota de downloads
app.mount("/downloads", StaticFiles(directory=DOWNLOAD_DIR), name="downloads")


# =========================================
# MODELO DE ENTRADA
# =========================================
class BIQPayload(BaseModel):
    dados_incidentes: Optional[dict] = {}
    justificativa_texto: str
    descricao_incidente: str
    acoes: list
    equipe: list
    follow_up_texto: str
    numero_biq: str


# =========================================
# AUTENTICAÇÃO OPCIONAL
# =========================================
def _check_api_key(x_api_key: Optional[str]):
    """Valida a API Key, se configurada."""
    if not API_KEY:
        return
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida.")


# =========================================
# HEALTHCHECK
# =========================================
@app.get("/health")
def health():
    """Rota de verificação da API."""
    exists = os.path.exists(TEMPLATE_PATH)
    return {
        "status": "ok",
        "msg": "API BIQ online",
        "versao": "2.1.0",
        "template_encontrado": exists,
        "template_path": TEMPLATE_PATH
    }


# =========================================
# /fill — GERA DOCX DIRETO (download)
# =========================================
@app.post("/fill")
def fill(payload: BIQPayload, x_api_key: Optional[str] = Header(default=None)):
    _check_api_key(x_api_key)
    try:
        if not os.path.exists(TEMPLATE_PATH):
            raise FileNotFoundError(f"Template não encontrado: {TEMPLATE_PATH}")

        docx_bytes = preencher_biq_from_payload(TEMPLATE_PATH, payload.model_dump())
        headers = {"Content-Disposition": 'attachment; filename="FORMULARIO_BIQ_PRENCHIDO.docx"'}

        print("✅ BIQ gerado e enviado como resposta direta.")
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers=headers
        )

    except Exception as e:
        print(f"❌ Erro em /fill: {e}")
        return JSONResponse(status_code=500, content={"erro": str(e)})


# =========================================
# /fill_b64 — GERA BASE64
# =========================================
@app.post("/fill_b64")
def fill_b64(payload: BIQPayload, x_api_key: Optional[str] = Header(default=None)):
    _check_api_key(x_api_key)
    try:
        if not os.path.exists(TEMPLATE_PATH):
            raise FileNotFoundError(f"Template não encontrado: {TEMPLATE_PATH}")

        docx_bytes = preencher_biq_from_payload(TEMPLATE_PATH, payload.model_dump())
        b64 = base64.b64encode(docx_bytes).decode("utf-8")

        print("✅ BIQ gerado e retornado em Base64.")
        return {"filename": "FORMULARIO_BIQ_PRENCHIDO.docx", "filedata": b64, "status": "success"}

    except Exception as e:
        print(f"❌ Erro em /fill_b64: {e}")
        return JSONResponse(status_code=500, content={"erro": str(e)})


# =========================================
# /fill_url — GERA DOCX E SALVA NO SERVIDOR
# =========================================
@app.post("/fill_url")
def fill_url(request: Request, payload: BIQPayload, x_api_key: Optional[str] = Header(default=None)):
    _check_api_key(x_api_key)
    try:
        if not os.path.exists(TEMPLATE_PATH):
            raise FileNotFoundError(f"Template não encontrado: {TEMPLATE_PATH}")

        # Gera DOCX
        docx_bytes = preencher_biq_from_payload(TEMPLATE_PATH, payload.model_dump())

        # Nome e caminho seguros
        stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        unique = uuid.uuid4().hex[:8]
        filename = f"FORMULARIO_BIQ_PRENCHIDO_{stamp}_{unique}.docx"
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        # Salva no diretório
        with open(filepath, "wb") as f:
            f.write(docx_bytes)

        base_url = str(request.base_url).rstrip("/")
        file_url = f"{base_url}/downloads/{filename}"

        print(f"✅ Arquivo salvo e disponível em: {file_url}")

        return {
            "filename": filename,
            "fileUrl": file_url,
            "status": "success",
            "mensagem": "Arquivo BIQ gerado com sucesso e disponível para download."
        }

    except Exception as e:
        print(f"❌ Erro em /fill_url: {e}")
        return JSONResponse(status_code=500, content={"erro": str(e)})

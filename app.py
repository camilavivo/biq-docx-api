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

# ========== CONFIGURAÇÕES ==========
API_KEY = os.getenv("BIQ_API_KEY")
TEMPLATE_PATH = os.getenv("BIQ_TEMPLATE_PATH", "/app/templates/MODELO_BIQ.docx")
DOWNLOAD_DIR = os.getenv("BIQ_DOWNLOAD_DIR", "/app/downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="ADV BIQ Filler API",
    version="2.0.0",
    description="API para geração automática do Boletim de Incidência da Qualidade (BIQ) conforme POP-NO-GQ-157.",
)

app.mount("/downloads", StaticFiles(directory=DOWNLOAD_DIR), name="downloads")

# ========== MODELO DE ENTRADA ==========
class BIQPayload(BaseModel):
    dados_incidentes: dict
    justificativa_texto: str
    descricao_incidente: str
    acoes: list
    equipe: list
    follow_up_texto: str
    numero_biq: str

# ========== AUTENTICAÇÃO ==========
def _check_api_key(x_api_key: Optional[str]):
    if not API_KEY:
        return  # sem chave configurada, não exige
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida.")

# ========== HEALTHCHECK ==========
@app.get("/health")
def health():
    return {"status": "ok", "msg": "API BIQ online", "versao": "2.0.0"}

# ========== ROTA 1 – RETORNA DOCX DIRETO ==========
@app.post(
    "/fill",
    response_class=Response,
    responses={200: {"content": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document": {}}}},
)
def fill(payload: BIQPayload, x_api_key: Optional[str] = Header(default=None)):
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

# ========== ROTA 2 – RETORNA BASE64 ==========
@app.post("/fill_b64")
def fill_b64(payload: BIQPayload, x_api_key: Optional[str] = Header(default=None)):
    import base64
    _check_api_key(x_api_key)
    if not os.path.exists(TEMPLATE_PATH):
        raise HTTPException(status_code=500, detail=f"Template não encontrado: {TEMPLATE_PATH}")
    docx_bytes = preencher_biq_from_payload(TEMPLATE_PATH, payload.model_dump())
    b64 = base64.b64encode(docx_bytes).decode("utf-8")
    return {"filename": "FORMULARIO_BIQ_PRENCHIDO.docx", "filedata": b64}

# ========== ROTA 3 – RETORNA URL ==========
@app.post("/fill_url")
def fill_url(request: Request, payload: BIQPayload, x_api_key: Optional[str] = Header(default=None)):
    """
    Salva o DOCX no servidor e retorna a URL pública para download.
    """
    _check_api_key(x_api_key)
    if not os.path.exists(TEMPLATE_PATH):
        raise HTTPException(status_code=500, detail=f"Template não encontrado: {TEMPLATE_PATH}")

    docx_bytes = preencher_biq_from_payload(TEMPLATE_PATH, payload.model_dump())

    # nome único do arquivo
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    unique = uuid.uuid4().hex[:8]
    filename = f"FORMULARIO_BIQ_PRENCHIDO_{stamp}_{unique}.docx"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(docx_bytes)

    base_url = str(request.base_url).rstrip("/")
    file_url = f"{base_url}/downloads/{filename}"

    return {"filename": filename, "fileUrl": file_url, "status": "success"}

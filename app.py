# -*- coding: utf-8 -*-
"""
API BIQ ADVFarma — Geração Automática de Boletim de Incidência da Qualidade (Anexo 01 POP-NO-GQ-157)
Versão: 2.1.0
"""

import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Response, Request
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from biq_filler import preencher_biq_from_payload


# ============================================================
# CONFIGURAÇÕES GERAIS E AMBIENTE
# ============================================================

API_KEY = os.getenv("BIQ_API_KEY") or None

# Diretório base do app (Render: /opt/render/project/src)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminhos seguros e absolutos
TEMPLATE_PATH = os.getenv("BIQ_TEMPLATE_PATH", os.path.join(BASE_DIR, "MODELO_BIQ.docx"))
DOWNLOAD_DIR = os.getenv("BIQ_DOWNLOAD_DIR", os.path.join(BASE_DIR, "downloads"))

# Cria pastas e testa permissão de escrita
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
try:
    test_file = os.path.join(DOWNLOAD_DIR, ".permtest")
    with open(test_file, "w") as f:
        f.write("ok")
    os.remove(test_file)
    print(f"✅ Pasta de downloads OK: {DOWNLOAD_DIR}")
except Exception as e:
    print(f"⚠️ Aviso: não foi possível gravar em {DOWNLOAD_DIR} ({e})")


# ============================================================
# INICIALIZAÇÃO DO APP FASTAPI
# ============================================================

app = FastAPI(
    title="ADV BIQ Filler API",
    version="2.1.0",
    description="API oficial da ADV Farma para gerar automaticamente o Boletim de Incidência da Qualidade (BIQ) em formato DOCX.",
)

# Permite chamadas externas seguras (ex.: do GPT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monta rota estática para downloads públicos
app.mount("/downloads", StaticFiles(directory=DOWNLOAD_DIR), name="downloads")


# ============================================================
# MODELO DE DADOS (ENTRADA)
# ============================================================

class BIQPayload(BaseModel):
    dados_incidentes: dict
    justificativa_texto: str
    descricao_incidente: str
    acoes: list
    equipe: list
    follow_up_texto: str
    numero_biq: str


# ============================================================
# AUTENTICAÇÃO OPCIONAL
# ============================================================

def _check_api_key(x_api_key: Optional[str]):
    """Valida a API Key, se configurada via variável de ambiente."""
    if not API_KEY:
        return  # API sem restrição
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida ou ausente.")


# ============================================================
# HEALTHCHECK
# ============================================================

@app.get("/health")
def health():
    """Verifica status geral e existência do template."""
    exists = os.path.exists(TEMPLATE_PATH)
    return {
        "status": "ok",
        "msg": "API BIQ online e funcional",
        "versao": "2.1.0",
        "template_encontrado": exists,
        "template_path": TEMPLATE_PATH,
        "download_dir": DOWNLOAD_DIR,
    }


# ============================================================
# ROTA 1 — RETORNA DOCX DIRETO (binário)
# ============================================================

@app.post(
    "/fill",
    response_class=Response,
    responses={200: {"content": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document": {}}}},
)
def fill(payload: BIQPayload, x_api_key: Optional[str] = Header(default=None)):
    """Gera o arquivo BIQ e retorna o DOCX direto (download binário)."""
    _check_api_key(x_api_key)

    if not os.path.exists(TEMPLATE_PATH):
        raise HTTPException(status_code=500, detail=f"Template não encontrado: {TEMPLATE_PATH}")

    try:
        docx_bytes = preencher_biq_from_payload(TEMPLATE_PATH, payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao preencher o documento: {e}")

    headers = {"Content-Disposition": 'attachment; filename="FORMULARIO_BIQ_PRENCHIDO.docx"'}
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )


# ============================================================
# ROTA 2 — RETORNA EM BASE64
# ============================================================

@app.post("/fill_b64")
def fill_b64(payload: BIQPayload, x_api_key: Optional[str] = Header(default=None)):
    """Gera o arquivo BIQ e retorna em formato Base64."""
    import base64

    _check_api_key(x_api_key)

    if not os.path.exists(TEMPLATE_PATH):
        raise HTTPException(status_code=500, detail=f"Template não encontrado: {TEMPLATE_PATH}")

    try:
        docx_bytes = preencher_biq_from_payload(TEMPLATE_PATH, payload.model_dump())
        b64 = base64.b64encode(docx_bytes).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar base64: {e}")

    return {"filename": "FORMULARIO_BIQ_PRENCHIDO.docx", "filedata": b64, "status": "success"}


# ============================================================
# ROTA 3 — RETORNA URL PÚBLICA DO DOCX
# ============================================================

@app.post("/fill_url")
def fill_url(request: Request, payload: BIQPayload, x_api_key: Optional[str] = Header(default=None)):
    """Gera o BIQ, salva em /downloads e retorna a URL pública."""
    _check_api_key(x_api_key)

    if not os.path.exists(TEMPLATE_PATH):
        raise HTTPException(status_code=500, detail=f"Template não encontrado: {TEMPLATE_PATH}")

    try:
        docx_bytes = preencher_biq_from_payload(TEMPLATE_PATH, payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar documento: {e}")

    # Nome único e caminho final
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    unique = uuid.uuid4().hex[:8]
    filename = f"FORMULARIO_BIQ_PRENCHIDO_{stamp}_{unique}.docx"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    try:
        with open(filepath, "wb") as f:
            f.write(docx_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {e}")

    file_url = f"{str(request.base_url).rstrip('/')}/downloads/{filename}"
    print(f"📄 BIQ gerado com sucesso: {file_url}")

    return {
        "filename": filename,
        "fileUrl": file_url,
        "status": "success",
        "mensagem": "Arquivo BIQ gerado com sucesso e disponível para download público.",
    }


# ============================================================
# ROTA 4 — COMPATIBILIDADE COM GPT ACTION (/gerar-biq-docx)
# ============================================================

@app.post("/gerar-biq-docx")
def gerar_biq_docx_action(request: Request, payload: BIQPayload, x_api_key: Optional[str] = Header(default=None)):
    """
    Compatível com a Action do GPT (gerarBiqDocx).
    Redireciona internamente para /fill_url.
    """
    print("🔄 Recebida requisição via /gerar-biq-docx (Action do GPT).")
    return fill_url(request, payload, x_api_key)


# ============================================================
# STARTUP MESSAGE (para logs no Render)
# ============================================================

@app.on_event("startup")
def startup_event():
    print("🚀 API BIQ ADV Farma inicializada com sucesso.")
    print(f"📂 Template: {TEMPLATE_PATH}")
    print(f"📁 Downloads: {DOWNLOAD_DIR}")


# ============================================================
# EXECUÇÃO LOCAL (opcional)
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)

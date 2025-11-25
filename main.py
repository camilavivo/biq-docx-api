from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import uuid
import os
from docx import Document
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Pasta onde os DOCX serão salvos
OUTPUT_DIR = "generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Rota estática para acessar os arquivos gerados
app.mount("/files", StaticFiles(directory=OUTPUT_DIR), name="files")


class BIQPayload(BaseModel):
    biq_texto: str


@app.get("/")
def read_root():
    return {"status": "ok", "msg": "API BIQ DOCX rodando"}


@app.post("/gerar-biq-docx")
def gerar_biq_docx(payload: BIQPayload):
    """
    Recebe o texto completo do BIQ e gera um arquivo DOCX simples com esse conteúdo.
    Depois devolve a URL do arquivo.
    """
    # Nome do arquivo
    filename = f"BIQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.docx"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # Cria o DOCX
    doc = Document()
    doc.add_paragraph(payload.biq_texto)
    doc.save(filepath)

    # Caminho relativo para download
    file_url = f"/files/{filename}"

    return {"file_url": file_url}

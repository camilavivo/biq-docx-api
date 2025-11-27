from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime
import os
import uuid
from fastapi.staticfiles import StaticFiles

# ==================== CONFIGURAÇÃO BÁSICA ====================

app = FastAPI(title="API BIQ ADV Farma")

OUTPUT_DIR = "generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

app.mount("/files", StaticFiles(directory=OUTPUT_DIR), name="files")

MODELO_PATH = "MODELO_BIQ.docx"  # seu modelo oficial

# ==================== ESTRUTURA DO JSON ====================

class BIQData(BaseModel):
    dados_incidentes: Dict[str, str]
    justificativa_texto: str
    descricao_incidente: str
    acoes: List[List[str]]
    equipe: List[List[str]]
    follow_up_texto: str
    numero_biq: str

# ==================== ROTA PRINCIPAL ====================

@app.get("/")
def home():
    return {
        "status": "ok",
        "msg": "API BIQ DOCX pronta para preencher modelo oficial",
        "versao": "2.0"
    }

@app.post("/gerar-biq-docx")
def gerar_biq_docx(biq: BIQData):
    """
    Recebe um JSON estruturado com os dados do BIQ,
    preenche o MODELO_BIQ.docx e devolve o link para download.
    """

    doc = Document(MODELO_PATH)

    # ======== PREENCHER TABELAS ========

    for table in doc.tables:
        header = table.rows[0].cells[0].text.strip()

        # 1️⃣ Dados da incidência
        if "Campo" in header:
            for row in table.rows[1:]:
                campo = row.cells[0].text.strip()
                if campo in biq.dados_incidentes:
                    row.cells[1].text = biq.dados_incidentes[campo]

        # 2️⃣ Justificativa / Reincidência
        elif "Justificativa" in header:
            for row in table.rows[1:]:
                if "Justificativa" in row.cells[0].text:
                    row.cells[1].text = biq.justificativa_texto
                elif "Reincidência" in row.cells[0].text:
                    row.cells[1].text = "Não reincidente"

        # 3️⃣ Descrição da incidência
        elif "Descrição" in header:
            for row in table.rows:
                if "Descrição" in row.cells[0].text:
                    row.cells[1].text = biq.descricao_incidente

        # 4️⃣ Ações corretivas e preventivas
        elif "N° Ação" in header:
            while len(table.rows) > 1:
                table._element.remove(table.rows[1]._element)
            for acao in biq.acoes:
                row = table.add_row().cells
                for i, valor in enumerate(acao):
                    row[i].text = valor

        # 5️⃣ Tabela de anexos (fixa)
        elif "Número do Anexo" in header:
            while len(table.rows) > 1:
                table._element.remove(table.rows[1]._element)
            row = table.add_row().cells
            row[0].text = "Não Aplicável"
            row[1].text = "Não Aplicável"
            row[2].text = "Não Aplicável"

        # 6️⃣ Envolvimento da equipe
        elif "Nome" in header and "Cargo" in table.rows[0].cells[1].text:
            while len(table.rows) > 1:
                table._element.remove(table.rows[1]._element)
            for membro in biq.equipe:
                row = table.add_row().cells
                row[0].text = membro[0]
                row[1].text = membro[1]
                row[2].text = "___________________________"

        # 7️⃣ Follow-up
        elif "Follow" in header:
            for row in table.rows:
                if "Follow" in row.cells[0].text:
                    row.cells[1].text = biq.follo

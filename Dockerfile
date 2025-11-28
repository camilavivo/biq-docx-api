# ================================
# ADV Farma – API BIQ DOCX (versão estável)
# ================================
FROM python:3.11-slim

LABEL maintainer="ADV Farma <sistemas@advfarma.com.br>"
LABEL description="API para geração automática de Boletim de Incidência da Qualidade (BIQ) conforme POP-NO-GQ-157."

WORKDIR /opt/render/project/src

# Copia tudo
COPY . .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Cria pastas com permissões seguras
RUN mkdir -p /opt/render/project/src/downloads && \
    chmod -R 777 /opt/render/project/src/downloads

# Expõe a porta padrão
EXPOSE 10000

# Comando de inicialização (Render usa $PORT automaticamente)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]

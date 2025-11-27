# ================================
# ADV Farma – API BIQ DOCX
# ================================
FROM python:3.11-slim

LABEL maintainer="ADV Farma <sistemas@advfarma.com.br>"
LABEL description="API para geração automática de Boletim de Incidência da Qualidade (BIQ) conforme POP-NO-GQ-157."

# Define diretório de trabalho
WORKDIR /app

# Copia arquivos da aplicação
COPY . /app

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Cria pastas necessárias
RUN mkdir -p /app/downloads /app/templates

# Expõe a porta padrão do Render
EXPOSE 10000

# Comando de inicialização
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]

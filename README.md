# 🧩 ADV FARMA – API BIQ DOCX

API oficial para geração automática do **Boletim de Incidência da Qualidade (BIQ)**  
conforme **Anexo 01 do POP-NO-GQ-157** e **RDC 658/2022 (BPF)**.

Desenvolvida para uso interno na ADV Farma, integrando-se ao **GPT Especialista em Garantia da Qualidade**,  
para criação e preenchimento automáticos de formulários BIQ em formato **.DOCX**.

---

## 🧠 Visão Geral

Esta API recebe os dados estruturados do BIQ (via JSON),  
preenche o modelo oficial do formulário (`MODELO_BIQ.docx`) e devolve:

- O arquivo BIQ preenchido (`.docx`)  
- Em **URL pública** (`/fill_url`)  
- Ou em **Base64** (`/fill_b64`)  

Compatível com integrações:
- GPT ADVFarma  
- QLD / CAPA internos  
- Sistemas de controle de documentos  
- Power Automate / E-mail / SGQ eletrônico

---

## ⚙️ Estrutura do Projeto


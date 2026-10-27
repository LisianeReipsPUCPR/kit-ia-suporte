"""Ouvidoria SIMULADA do kit (Aula 5). Registra manifestações e devolve protocolo.

Dados fictícios, só para o laboratório. Num tribunal, seria a API do sistema da ouvidoria.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

ARQ = Path(os.environ.get("KIT_CONFIG", "/config")) / "manifestacoes.json"
TIPOS = {"reclamação", "reclamacao", "denúncia", "denuncia", "elogio", "sugestão", "sugestao", "solicitação", "solicitacao"}
app = FastAPI(title="Ouvidoria simulada")


class Manifestacao(BaseModel):
    tipo: str
    texto: str
    canal: str = "chat"


def carregar() -> list:
    try:
        return json.loads(ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


@app.post("/manifestacoes", status_code=201)
async def registrar(request: Request):
    """Aceita JSON {"tipo","texto","canal"} ou os mesmos campos na URL (?tipo=...&texto=...)."""
    try:
        dados = await request.json()
    except ValueError:
        dados = dict(request.query_params)
    try:
        m = Manifestacao(**dados)
    except Exception:
        raise HTTPException(422, "Envie tipo e texto da manifestação.")
    if m.tipo.strip().lower() not in TIPOS:
        raise HTTPException(422, "Tipo deve ser reclamação, denúncia, elogio, sugestão ou solicitação.")
    if not m.texto.strip():
        raise HTTPException(422, "O texto da manifestação está vazio.")
    lista = carregar()
    agora = datetime.now()
    protocolo = f"OUV-{agora.year}-{len(lista) + 1:06d}"
    item = {"protocolo": protocolo, "tipo": m.tipo, "texto_original": m.texto, "canal": m.canal,
            "registrada_em": agora.strftime("%d/%m/%Y %H:%M"),
            "prazo_resposta": (agora + timedelta(days=30)).strftime("%d/%m/%Y"), "prazo_dias": 30}
    lista.append(item)
    ARQ.write_text(json.dumps(lista, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"protocolo": protocolo, "prazo_dias": 30, "prazo_resposta": item["prazo_resposta"]}


@app.get("/manifestacoes")
def listar():
    return carregar()

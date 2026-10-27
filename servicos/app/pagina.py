"""Página do kit (http://localhost:8080): painel de controle do laboratório.

Mostra se tudo está ligado, guarda a chave do Dify, abre o chat on-line de teste
e tem botões para testar a ouvidoria e a API do tribunal, sem comandos.
"""
import json
import os
import re
from pathlib import Path

import httpx
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse

CONFIG = Path(os.environ.get("KIT_CONFIG", "/config"))
URL = {
    "chatwoot": os.environ.get("URL_CHATWOOT", "http://chatwoot:3000"),
    "dify": os.environ.get("URL_DIFY", "http://dify"),
    "conector": os.environ.get("URL_CONECTOR", "http://conector:8000"),
    "ouvidoria": os.environ.get("URL_OUVIDORIA", "http://ouvidoria:8100"),
    "tribunal": os.environ.get("URL_TRIBUNAL", "http://tribunal:8200"),
}
app = FastAPI(title="Página do kit")
STATIC = Path(__file__).parent / "static"


def ler(nome: str) -> dict:
    try:
        return json.loads((CONFIG / nome).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


@app.get("/", response_class=HTMLResponse)
def inicio():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    cw = ler("chatwoot.json")
    return html.replace("{{WEBSITE_TOKEN}}", cw.get("website_token", "")) \
               .replace("{{LOGIN}}", cw.get("login", "equipe@suporte-lab.com.br")) \
               .replace("{{SENHA}}", cw.get("senha", "Suporte@2026")) \
               .replace("{{PUB_DIFY}}", os.environ.get("PUB_DIFY", "http://localhost:8081")) \
               .replace("{{PUB_CHATWOOT}}", os.environ.get("PUB_CHATWOOT", "http://localhost:3000"))


@app.get("/api/status")
async def status():
    async def ok(url: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=4) as h:
                r = await h.get(url)
                return r.status_code < 500
        except httpx.HTTPError:
            return False
    return {
        "chatwoot": await ok(URL["chatwoot"] + "/api"),
        "dify": await ok(URL["dify"] + "/console/api/setup"),
        "conector": await ok(URL["conector"] + "/saude"),
        "ouvidoria": await ok(URL["ouvidoria"] + "/manifestacoes"),
        "tribunal": await ok(URL["tribunal"] + "/registros"),
        "chatwoot_configurado": bool(ler("chatwoot.json").get("website_token")),
        "dify_configurado": bool(ler("dify.json").get("dify_key")),
    }


@app.post("/api/chave")
def salvar_chave(chave: str = Form(...)):
    chave = chave.strip()
    if not re.fullmatch(r"app-[A-Za-z0-9]{10,}", chave):
        return JSONResponse({"ok": False, "msg": "A chave do Dify começa com app- seguida de letras e números. Copie de novo em Publicar › Acesso à API."}, 400)
    (CONFIG / "dify.json").write_text(json.dumps({"dify_key": chave}), encoding="utf-8")
    return {"ok": True, "msg": "Chave salva. O bot do chat on-line já usa o Dify."}


@app.post("/api/teste/ouvidoria")
async def teste_ouvidoria(tipo: str = Form(...), texto: str = Form(...)):
    async with httpx.AsyncClient(timeout=10) as h:
        r = await h.post(URL["ouvidoria"] + "/manifestacoes", json={"tipo": tipo, "texto": texto, "canal": "chat"})
    return {"status": r.status_code, "resposta": r.json()}


@app.post("/api/teste/tribunal")
async def teste_tribunal(numero: str = Form(...), token: str = Form(""), vezes: int = Form(1)):
    cab = {"Authorization": f"Bearer {token}"} if token else {}
    resultados = []
    async with httpx.AsyncClient(timeout=10) as h:
        for _ in range(max(1, min(vezes, 15))):
            r = await h.get(f"{URL['tribunal']}/processos/{numero}", headers=cab)
            resultados.append({"status": r.status_code, "resposta": r.json()})
    return resultados

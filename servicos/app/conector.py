"""Conector do kit: liga o Chatwoot (chat on-line) ao Dify (o "cérebro" do bot).

Fluxo: o Chatwoot avisa que chegou mensagem -> o conector pergunta ao Dify ->
devolve a resposta no chat. Se o Dify pedir [ATENDENTE] (ou falhar), a conversa
passa para um atendente humano. O conector não conhece o modelo de IA: trocar de
Gemini para ChatGPT, Claude ou Ollama é feito só no Dify.
"""
import json
import logging
import os
from pathlib import Path

import httpx
from fastapi import FastAPI, Request

CONFIG = Path(os.environ.get("KIT_CONFIG", "/config"))
CHATWOOT_URL = os.environ.get("CHATWOOT_URL", "http://chatwoot:3000")
DIFY_URL = os.environ.get("DIFY_URL", "http://dify/v1")
MARCADOR = "[ATENDENTE]"
FALHA = "Tive um problema técnico. Vou transferir você para um atendente."
SEM_CHAVE = ("O assistente ainda não foi ligado ao Dify. "
             "Vou transferir você para um atendente.")

logging.basicConfig(level=logging.INFO, format="%(asctime)s conector %(message)s")
log = logging.getLogger()
app = FastAPI(title="Conector do kit")
conversas: dict[int, str] = {}  # conversa no Chatwoot -> conversation_id no Dify


def ler(nome: str) -> dict:
    """Lê um arquivo de configuração do kit (vazio se ainda não existe)."""
    try:
        return json.loads((CONFIG / nome).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


@app.get("/saude")
def saude():
    return {"ok": True, "chatwoot": bool(ler("chatwoot.json")), "dify": bool(ler("dify.json").get("dify_key"))}


@app.post("/webhook")
async def webhook(request: Request):
    ev = await request.json()
    # 1. Só mensagens novas do usuário, em conversas que ainda estão com o bot
    if ev.get("event") != "message_created" or ev.get("message_type") != "incoming":
        return {"ok": True}
    conversa = ev.get("conversation") or {}
    if conversa.get("status") != "pending":  # já está com um atendente humano
        return {"ok": True}
    texto = (ev.get("content") or "").strip()
    if not texto:
        return {"ok": True}

    cw, dify = ler("chatwoot.json"), ler("dify.json")
    conta_id = (ev.get("account") or {}).get("id") or cw.get("account_id")
    conversa_id = conversa["id"]

    async with httpx.AsyncClient(timeout=60) as http:
        # 2. Pergunta ao Dify: ele decide escopo, base de conhecimento e modelo
        if not dify.get("dify_key"):
            resposta, transferir = SEM_CHAVE, True
        else:
            try:
                r = await http.post(
                    f"{DIFY_URL}/chat-messages",
                    headers={"Authorization": f"Bearer {dify['dify_key']}"},
                    json={"inputs": {}, "query": texto, "response_mode": "blocking",
                          "conversation_id": conversas.get(conversa_id, ""),
                          "user": f"chatwoot-{conversa_id}"},
                )
                r.raise_for_status()
                dados = r.json()
                conversas[conversa_id] = dados.get("conversation_id", "")
                resposta = dados.get("answer", "")
                transferir = MARCADOR in resposta
                resposta = resposta.replace(MARCADOR, "").strip()
            except (httpx.HTTPError, ValueError) as e:
                log.warning("Dify falhou: %s", e)
                resposta, transferir = FALHA, True

        # 3. Devolve a resposta no chat
        base = f"{CHATWOOT_URL}/api/v1/accounts/{conta_id}/conversations/{conversa_id}"
        cab = {"api_access_token": cw.get("bot_token", "")}
        if resposta:
            await http.post(f"{base}/messages", headers=cab,
                            json={"content": resposta, "message_type": "outgoing"})
        # 4. Transferência: a conversa sai do bot e entra na fila humana
        if transferir:
            await http.post(f"{base}/toggle_status", headers=cab, json={"status": "open"})
        log.info("conversa %s respondida%s", conversa_id, " e transferida" if transferir else "")
    return {"ok": True}

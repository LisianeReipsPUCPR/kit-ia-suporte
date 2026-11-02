"""Conector do kit: liga o Chatwoot (chat on-line) ao Dify (o "cérebro" do bot).

Fluxo: o Chatwoot avisa que chegou mensagem -> o conector pergunta ao Dify ->
devolve a resposta no chat. Se o Dify pedir [ATENDENTE] (ou falhar), a conversa
passa para um atendente humano. O conector não conhece o modelo de IA: trocar de
Gemini para ChatGPT, Claude ou Ollama é feito só no Dify.
"""
import asyncio
import json
import logging
import os
import re
import time
from pathlib import Path

import httpx
from fastapi import BackgroundTasks, FastAPI, Request

CONFIG = Path(os.environ.get("KIT_CONFIG", "/config"))
CHATWOOT_URL = os.environ.get("CHATWOOT_URL", "http://chatwoot:3000")
DIFY_URL = os.environ.get("DIFY_URL", "http://dify/v1")
MARCADOR = "[ATENDENTE]"
TENTATIVAS = 3  # o modelo às vezes recusa por excesso de demanda (erro temporário)
ESPERA_CURTA = 20  # limite por minuto: vale aguardar até estes segundos e repetir
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


def anotar(**campos):
    """Guarda como o robô está indo em /config/robo.json: é o que o painel mostra."""
    (CONFIG / "robo.json").write_text(json.dumps(ler("robo.json") | campos), encoding="utf-8")


def segundos_de_espera(corpo: str) -> int | None:
    """Lê quanto falta para o limite renovar: Gemini (retryDelay: 50010s) ou Groq (try again in 7m12.5s)."""
    if m := re.search(r"retryDelay\W+(\d+)", corpo):
        return int(m.group(1))
    if m := re.search(r"try again in\s+(?:(\d+)h)?(?:(\d+)m(?!s))?(?:([\d.]+)s)?", corpo):
        h, minutos, s = (float(x or 0) for x in m.groups())
        return int(h * 3600 + minutos * 60 + s) + 1
    return None


def diagnosticar(status: int, corpo: str) -> dict:
    """Traduz o erro do modelo de IA, que o Dify repassa dentro do corpo da resposta."""
    agora = time.time()
    if status == 401:
        return {"tipo": "chave_dify", "em": agora}
    if re.search(r"RESOURCE_EXHAUSTED|quotaValue|rate_limit_exceeded|rate limit", corpo, re.I):
        espera = segundos_de_espera(corpo)
        cota = re.search(r"quotaValue\W+(\d+)", corpo)
        return {"tipo": "limite", "em": agora,
                "volta_em": agora + espera if espera is not None else None,
                "cota": int(cota.group(1)) if cota else None}
    if re.search(r"UNAVAILABLE|capacity", corpo, re.I):
        return {"tipo": "sobrecarga", "em": agora}
    if re.search(r"API_KEY_INVALID|invalid_api_key|PERMISSION_DENIED|UNAUTHENTICATED|credential|not configured", corpo, re.I):
        return {"tipo": "conta", "em": agora}
    if re.search(r"NOT_FOUND|model_not_found|decommissioned", corpo, re.I):
        return {"tipo": "modelo", "em": agora}
    return {"tipo": "outro", "em": agora}


async def consultar(http: httpx.AsyncClient, chave: str, conversa_dify: str, texto: str, usuario: str) -> httpx.Response:
    """Pergunta ao Dify e anota o resultado. Só repete em sobrecarga ou em limite que renova logo."""
    for tentativa in range(TENTATIVAS):
        try:
            r = await http.post(
                f"{DIFY_URL}/chat-messages",
                headers={"Authorization": f"Bearer {chave}"},
                json={"inputs": {}, "query": texto, "response_mode": "blocking",
                      "conversation_id": conversa_dify, "user": usuario},
            )
        except httpx.TransportError:
            anotar(erro={"tipo": "dify", "em": time.time()})
            raise
        if r.is_success:
            agora = time.time()
            limites = {k: v for k, v in (ler("robo.json").get("limites") or {}).items()
                       if v.get("volta_em") is None or v["volta_em"] > agora}  # os vencidos já renovaram
            anotar(ok_em=agora, erro=None, limites=limites)
            return r
        erro = diagnosticar(r.status_code, r.text)
        if m := re.search(r"gemini|groq", r.text, re.I):
            erro["provedor"] = m.group(0).lower()
        espera = 3 if erro["tipo"] == "sobrecarga" else (erro.get("volta_em") or float("inf")) - time.time()
        if espera > ESPERA_CURTA or tentativa == TENTATIVAS - 1:
            break
        await asyncio.sleep(max(espera, 1))
    limites = ler("robo.json").get("limites") or {}
    if erro["tipo"] == "limite":  # vale por provedor: uma resposta boa de outro modelo não apaga
        limites[erro.get("provedor", "desconhecido")] = erro
    anotar(erro=erro, limites=limites)
    return r


@app.get("/saude")
def saude():
    return {"ok": True, "chatwoot": bool(ler("chatwoot.json")), "dify": bool(ler("dify.json").get("dify_key"))}


@app.post("/testar")
async def testar():
    """Botão do painel: pergunta real, que passa pelo classificador e pelo redator (gasta cota, por isso só sob demanda)."""
    chave = ler("dify.json").get("dify_key")
    if not chave:
        anotar(erro={"tipo": "chave_dify", "em": time.time()})
        return {"ok": False}
    async with httpx.AsyncClient(timeout=60) as http:
        try:
            r = await consultar(http, chave, "", "como emito uma certidão?", "painel-teste")
        except httpx.HTTPError:
            return {"ok": False}
    if r.is_success:
        anotar(limites={})  # passou por todos os modelos: nenhum limite segue valendo
    return {"ok": r.is_success}


@app.post("/webhook")
async def webhook(request: Request, tarefas: BackgroundTasks):
    ev = await request.json()
    # 1. Só mensagens novas do usuário, em conversas que ainda estão com o bot
    if ev.get("event") != "message_created" or ev.get("message_type") != "incoming":
        return {"ok": True}
    anotar(recebida_em=time.time())  # o Chatwoot conseguiu entregar a mensagem ao conector
    conversa = ev.get("conversation") or {}
    if conversa.get("status") != "pending":  # já está com um atendente humano
        return {"ok": True}
    texto = (ev.get("content") or "").strip()
    if not texto:
        return {"ok": True}

    # O Chatwoot espera só 5 s e, se estourar, tira a conversa do bot: responde já e atende em seguida
    tarefas.add_task(atender, ev, conversa, texto)
    return {"ok": True}


async def atender(ev: dict, conversa: dict, texto: str):
    cw, dify = ler("chatwoot.json"), ler("dify.json")
    conta_id = (ev.get("account") or {}).get("id") or cw.get("account_id")
    conversa_id = conversa["id"]

    async with httpx.AsyncClient(timeout=60) as http:
        # 2. Pergunta ao Dify: ele decide escopo, base de conhecimento e modelo
        if not dify.get("dify_key"):
            resposta, transferir = SEM_CHAVE, True
        else:
            try:
                r = await consultar(http, dify["dify_key"], conversas.get(conversa_id, ""),
                                    texto, f"chatwoot-{conversa_id}")
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

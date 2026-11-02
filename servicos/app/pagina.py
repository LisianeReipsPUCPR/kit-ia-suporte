"""Página do kit (http://localhost:8080): painel de controle do laboratório.

Mostra se tudo está ligado e se o robô está respondendo, guarda a chave do Dify,
abre o chat on-line de teste e tem botões para testar a ouvidoria e a API do
tribunal, sem comandos.
"""
import base64
import json
import os
import re
import time
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
SOBRECARGA_VALE = 600  # depois de 10 minutos, um erro de sobrecarga já não diz nada
PROVEDORES = {"groq": "Groq", "gemini": "Gemini"}  # sempre aparecem no painel, mesmo fora de uso
contas = {"em": 0.0, "provedores": {}, "bloqueio": {"verificado": False, "em": None}, "token": ""}  # última verificação de Dify e Chatwoot


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
        "kit_atualizado": ler("atualizacao.json").get("situacao", "ok") == "ok",
    }


async def provedores_de_ia() -> dict:
    """Pergunta ao Dify quais contas estão cadastradas e onde o robô publicado usa cada uma (não gasta cota)."""
    provedores = {id_: {"nome": nome, "conta": None, "usos": []} for id_, nome in PROVEDORES.items()}
    try:
        senha = (CONFIG / ".senha").read_text(encoding="utf-8").strip()
        async with httpx.AsyncClient(timeout=10) as h:
            r = await h.post(URL["dify"] + "/console/api/login",
                             json={"email": ler("chatwoot.json").get("login"), "remember_me": True,
                                   "password": base64.b64encode(senha.encode()).decode()})
            r.raise_for_status()
            cab = {"X-CSRF-Token": h.cookies.get("csrf_token") or h.cookies.get("__Host-csrf_token") or ""}
            r = await h.get(URL["dify"] + "/console/api/workspaces/current/model-providers", headers=cab)
            r.raise_for_status()
            for p in provedores.values():
                p["conta"] = False
            for p in r.json()["data"]:  # langgenius/groq/groq -> groq
                id_ = p["provider"].split("/")[1]
                provedores.setdefault(id_, {"nome": id_.capitalize(), "conta": False, "usos": []})
                provedores[id_]["conta"] = (p.get("custom_configuration") or {}).get("status") == "active"
            r = await h.get(f"{URL['dify']}/console/api/apps/{ler('dify.json').get('app_id')}/workflows/publish", headers=cab)
            r.raise_for_status()
        for n in r.json()["graph"]["nodes"]:
            if modelo := n["data"].get("model"):
                id_ = modelo["provider"].split("/")[1]
                provedores.setdefault(id_, {"nome": id_.capitalize(), "conta": False, "usos": []})
                provedores[id_]["usos"].append({"no": n["data"].get("title", ""), "modelo": modelo["name"]})
    except (OSError, ValueError, KeyError, TypeError, IndexError, httpx.HTTPError):
        pass  # sem o app_id (chave colada à mão) ou Dify ocupado: fica com o que já se sabe
    return provedores


async def token_chatwoot(h: httpx.AsyncClient, cw: dict) -> str:
    """Entra no Chatwoot só uma vez e guarda o token: o Chatwoot bloqueia logins repetidos (HTTP 429)."""
    if not contas["token"]:
        r = await h.post(URL["chatwoot"] + "/auth/sign_in", json={"email": cw.get("login"), "password": cw.get("senha")})
        r.raise_for_status()
        contas["token"] = r.json()["data"]["access_token"]
    return contas["token"]


async def ultimo_bloqueio() -> dict:
    """Quando o Chatwoot avisou pela última vez que não conseguiu chamar o robô, e se deu para verificar."""
    cw = ler("chatwoot.json")
    try:
        async with httpx.AsyncClient(timeout=10) as h:
            cab = {"api_access_token": await token_chatwoot(h, cw)}
            base = f"{URL['chatwoot']}/api/v1/accounts/{cw.get('account_id')}/conversations"
            r = await h.get(base, headers=cab, params={"status": "all", "sort_by": "last_activity_at_desc"})
            if r.status_code == 401:
                contas["token"] = ""  # token vencido: entra de novo na próxima verificação
            r.raise_for_status()
            lista = r.json()["data"]["payload"]
            if not lista:
                return {"verificado": True, "em": None}
            r = await h.get(f"{base}/{lista[0]['id']}/messages", headers=cab)
            r.raise_for_status()
        em = max((m["created_at"] for m in r.json()["payload"]
                  if m["message_type"] == 2 and re.search(r"erro com o robô|agent bot", m["content"] or "")), default=None)
        return {"verificado": True, "em": em}
    except (ValueError, KeyError, httpx.HTTPError):
        return {"verificado": False, "em": None}


def situacao_do_robo(robo: dict, provedores: dict, bloqueio: dict) -> dict:
    """Resume se o robô está respondendo e o que fazer, com o estado de cada provedor. {hora} vira a hora local no navegador."""
    agora = time.time()
    em_uso = {id_: p for id_, p in provedores.items() if p["usos"]}
    erro = robo.get("erro") or {}
    if erro.get("provedor") and em_uso and erro["provedor"] not in em_uso:
        erro = {}  # erro de um provedor que o robô não usa mais
    tipo = None if erro.get("tipo") == "limite" else erro.get("tipo")
    limites = dict(robo.get("limites") or {})
    if "desconhecido" in limites and len(em_uso) == 1:  # o erro não dizia o provedor, mas só há um em uso
        limites.setdefault(next(iter(em_uso)), limites.pop("desconhecido"))
    def ativo(limite: dict) -> bool:
        return limite.get("volta_em") is None or limite["volta_em"] > agora

    itens = []
    for id_, p in provedores.items():
        usado, ia = bool(p["usos"]), p["nome"]
        recusada = usado and tipo == "conta" and erro.get("provedor") in (id_, None)
        if recusada:
            conta = ("bad", "chave recusada")
        elif p["conta"]:
            conta = ("ok", "conectada")
        elif p["conta"] is None:
            conta = ("warn", "não verificada")
        else:
            conta = ("bad" if usado else "warn", "não conectada")
        limite = limites.get(id_)
        volta = None
        if limite and ativo(limite):
            situacao, volta = ("bad" if usado else "warn", "atingido"), limite.get("volta_em")
        elif limite:
            situacao = ("warn", "a confirmar")
        elif usado and robo.get("ok_em"):
            situacao = ("ok", "sem erro")
        else:
            situacao = ("warn", "sem dados") if usado else ("", "sem dados")
        uso = ", ".join(f"{u['no']} ({u['modelo']})" for u in p["usos"]) or "não usado no robô publicado"
        itens += [{"nome": f"Conta do {ia}", "cls": conta[0], "txt": conta[1]},
                  {"nome": f"Limite do {ia}", "cls": situacao[0], "txt": situacao[1], "volta_em": volta},
                  {"nome": f"Uso do {ia}", "cls": "", "txt": uso}]
    bloqueado = bool(bloqueio["em"] and bloqueio["em"] > (robo.get("recebida_em") or 0))
    if bloqueado:
        itens.append({"nome": "Chat chega ao robô", "cls": "bad", "txt": "bloqueado"})
    elif robo.get("recebida_em"):
        itens.append({"nome": "Chat chega ao robô", "cls": "ok", "txt": "sim"})
    elif not bloqueio["verificado"]:
        itens.append({"nome": "Chat chega ao robô", "cls": "warn", "txt": "não verificado"})
    else:
        itens.append({"nome": "Chat chega ao robô", "cls": "warn", "txt": "sem mensagens"})

    sem_conta = [p["nome"] for p in em_uso.values() if p["conta"] is False]
    if tipo == "conta":
        sem_conta = sem_conta or [provedores[erro["provedor"]]["nome"] if erro.get("provedor") in provedores else "modelo de IA"]
    no_limite = {id_: l for id_, l in limites.items() if ativo(l) and (id_ in em_uso or id_ == "desconhecido")}
    vencidos = [id_ for id_, l in limites.items() if not ativo(l) and id_ in em_uso]
    ia = " e ".join(provedores[id_]["nome"] if id_ in provedores else "modelo de IA" for id_ in no_limite)
    voltas = [l["volta_em"] for l in no_limite.values() if l.get("volta_em")]
    volta_em = max(voltas) if len(voltas) == len(no_limite) and voltas else None
    if sem_conta:
        nomes = " e ".join(sem_conta)
        cls, titulo = "bad", f"Robô parado: a conta do {nomes} não está conectada."
        acao = (f"No Dify: seu nome › Configurações › Provedor de modelo › {sem_conta[0]}, e cole a chave. Para usar outro "
                "provedor, troque o modelo nos nós de IA do app Bot STJ e publique.")
    elif bloqueado:
        cls, titulo = "bad", "Robô parado: o Chatwoot não está conseguindo chamar o robô."
        acao = ("As conversas estão indo direto para o atendente humano. Confira se o Chatwoot foi ligado com "
                "SAFE_FETCH_ALLOW_PRIVATE_NETWORK ou chame a professora.")
    elif no_limite:
        parcial = len(em_uso) > 1 and all(id_ in em_uso for id_ in no_limite) and len(no_limite) < len(em_uso)
        nos = ", ".join(u["no"] for id_ in no_limite for u in provedores.get(id_, {"usos": []})["usos"])
        cls, titulo = "bad", (f"Robô com falha parcial: o limite do {ia} foi atingido." if parcial
                              else f"Robô parado: o limite do {ia} foi atingido.")
        volta = "Deve voltar em {hora}" if volta_em else "Deve voltar quando o provedor renovar a cota"
        afetados = f"Nó afetado: {nos}. " if parcial and nos else ""
        acao = (afetados + volta + ". Até lá, as conversas que passam por esse modelo vão para o atendente humano. "
                "Para voltar antes, troque o modelo no Dify e publique.")
    elif tipo == "modelo":
        cls, titulo = "bad", "Robô parado: um modelo escolhido não existe mais no provedor."
        acao = "No Dify, abra o app Bot STJ, escolha outro modelo nos nós de IA e clique em Publicar."
    elif tipo == "chave_dify":
        cls, titulo = "bad", "Robô parado: a chave do Dify está faltando ou foi recusada."
        acao = "Gere uma nova chave e salve no item 3 abaixo."
    elif tipo == "dify":
        cls, titulo = "bad", "Robô parado: o conector não conseguiu falar com o Dify."
        acao = "Confira se o Dify está OK na lista acima."
    elif tipo == "outro":
        cls, titulo = "bad", "A última pergunta ao robô falhou."
        acao = "Veja o erro em Logs, no app Bot STJ do Dify."
    elif tipo == "sobrecarga" and agora - erro.get("em", 0) < SOBRECARGA_VALE:
        nome = provedores[erro["provedor"]]["nome"] if erro.get("provedor") in provedores else "provedor de IA"
        cls, titulo = "warn", f"Robô instável: o {nome} está sobrecarregado."
        acao = "Costuma passar em alguns minutos. Enquanto isso, algumas conversas podem ir para o atendente humano."
    elif vencidos:
        cls, titulo = "warn", "Um limite de IA já deve ter sido renovado."
        acao = "Clique em Testar agora para confirmar."
    elif robo.get("ok_em") and tipo is None:
        cls, titulo = "ok", "Robô funcionando."
        acao = "Última resposta da IA em {ok}."
    else:
        cls, titulo = "warn", "Ainda não sei se o robô está respondendo."
        acao = "Mande uma mensagem no chat ou clique em Testar agora."
    return {"cls": cls, "titulo": titulo, "acao": acao, "volta_em": volta_em, "ok_em": robo.get("ok_em"), "itens": itens}


@app.get("/api/robo")
async def robo():
    # O painel chama a cada 5 s, mas Dify e Chatwoot só são consultados a cada 30 s (exige login)
    if time.time() - contas["em"] > 30 or not contas["provedores"]:
        contas.update(em=time.time(), provedores=await provedores_de_ia(), bloqueio=await ultimo_bloqueio())
    return situacao_do_robo(ler("robo.json"), contas["provedores"], contas["bloqueio"])


@app.post("/api/robo/testar")
async def testar_robo():
    try:
        async with httpx.AsyncClient(timeout=100) as h:
            r = await h.post(URL["conector"] + "/testar")
        return r.json()
    except (ValueError, httpx.HTTPError):
        return {"ok": False}


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

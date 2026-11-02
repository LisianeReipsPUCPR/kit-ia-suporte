"""Configura o Dify sozinho (versão Codespaces do kit).

Na primeira vez: cria a conta de administrador, importa o Bot STJ, publica e gera
a chave da API, gravando-a em /config/dify.json para o conector.
Uma vez por versão, em todo ambiente: instala o plugin do Groq, cria a base de
conhecimento e atualiza o fluxo publicado, preservando o que o aluno personalizou.
Se algo falhar, o laboratório liga assim mesmo e o kit tenta de novo na próxima vez.
"""
import base64
import json
import os
import sys
import time
from pathlib import Path

import httpx

DIFY = os.environ.get("URL_DIFY", "http://dify")
EMAIL = os.environ["KIT_EMAIL"]
SENHA = os.environ["KIT_SENHA"]
BOT = Path(os.environ.get("KIT_BOT", "/bot/Bot_STJ.yml"))
CONFIG = Path(os.environ.get("KIT_CONFIG", "/config"))
BASE = Path(os.environ.get("KIT_BASE", "/base"))

VERSAO = "2"  # suba este número quando o fluxo mudar: a atualização roda de novo em cada ambiente
PLUGIN_GROQ = "langgenius/groq:0.0.20@ecc58cf59b06533eaf63a9ddb8231de99994a70246b650e1b8917ffd0098bd55"
GROQ = "langgenius/groq/groq"
GEMINI = "langgenius/gemini/google"
MODELO_GROQ = "openai/gpt-oss-20b"
MODELO_GEMINI = "gemini-3.5-flash-lite"
MODELOS_DESLIGADOS = {"gemini-2.5-flash", "llama-3.1-8b-instant"}
NOME_BASE = "Base STJ – Atendimento"
RESPOSTA_NUMERO = ("Esse número não parece válido. Confira os dígitos e informe o número completo do processo "
                   "no padrão CNJ, por exemplo: 0001234-52.2026.3.00.0000.")
INSTRUCAO = """Você é a Lia, assistente virtual do atendimento do Superior Tribunal de Justiça (STJ).
Responda SOMENTE com o que está escrito no CONTEXTO abaixo, usando linguagem simples e no máximo 5 passos.
Não acrescente passos, telas, botões, formulários, links, telefones nem exigências que não estejam escritos no CONTEXTO. Mantenha os avisos de "Atenção" e "Importante" que se aplicam à pergunta.
Termine com o endereço que aparece depois de "Fonte oficial" no artigo usado, copiado exatamente como está.
Somente se a pergunta for sobre o andamento de um processo, acrescente no final: "Se preferir, me informe o número do processo e eu consulto aqui."
Se o CONTEXTO não responder à pergunta, diga exatamente: "Não encontrei essa informação. Quer falar com um atendente?"
Nunca dê orientação jurídica, opinião ou previsão de decisões.

CONTEXTO:
{{#context#}}"""


def etapa(msg):
    print(f"[dify] {msg}", flush=True)


def esperar(h: httpx.Client):
    for _ in range(120):  # até 10 minutos
        try:
            r = h.get(f"{DIFY}/console/api/setup")
            if r.status_code == 200:
                return r.json().get("step")
        except httpx.HTTPError:
            pass
        time.sleep(5)
    raise SystemExit("Dify não respondeu em 10 minutos.")


def entrar(h: httpx.Client) -> dict:
    r = h.post(f"{DIFY}/console/api/login",
               json={"email": EMAIL, "password": base64.b64encode(SENHA.encode()).decode(), "remember_me": True})
    r.raise_for_status()
    if r.json().get("result") != "success":
        raise SystemExit(f"login recusado: {r.text}")
    return {"X-CSRF-Token": h.cookies.get("csrf_token") or h.cookies.get("__Host-csrf_token") or ""}


def importar_bot(h: httpx.Client, cab: dict) -> str:
    r = h.post(f"{DIFY}/console/api/apps/imports", headers=cab,
               json={"mode": "yaml-content", "yaml_content": BOT.read_text(encoding="utf-8")})
    imp = r.json()
    if r.status_code == 202:
        r = h.post(f"{DIFY}/console/api/apps/imports/{imp['id']}/confirm", headers=cab)
        imp = r.json()
    if r.status_code >= 400 or not imp.get("app_id"):
        raise SystemExit(f"importação do bot falhou: HTTP {r.status_code} {r.text[:300]}")
    app_id = imp["app_id"]
    etapa(f"Bot STJ importado ({app_id})")

    r = h.post(f"{DIFY}/console/api/apps/{app_id}/workflows/publish", headers=cab,
               json={"marked_name": "Versão do kit", "marked_comment": ""})
    etapa(f"publicado: HTTP {r.status_code}")

    r = h.post(f"{DIFY}/console/api/apps/{app_id}/api-keys", headers=cab)
    r.raise_for_status()
    chave = r.json()["token"]
    (CONFIG / "dify.json").write_text(json.dumps({"dify_key": chave, "app_id": app_id}), encoding="utf-8")
    etapa("chave da API gravada; o chat já usa o Dify")
    return app_id


def achar_bot(h: httpx.Client, cab: dict) -> str | None:
    """A chave colada à mão no painel não guarda o app_id: procura o app pelo nome."""
    r = h.get(f"{DIFY}/console/api/apps", headers=cab, params={"page": 1, "limit": 50})
    r.raise_for_status()
    return next((a["id"] for a in r.json()["data"] if a["name"] == "Bot STJ"), None)


def instalar_groq(h: httpx.Client, cab: dict):
    url = f"{DIFY}/console/api/workspaces/current/plugin"
    instalados = h.get(f"{url}/list", headers=cab, params={"page": 1, "page_size": 100}).json().get("plugins", [])
    if any(p.get("plugin_id") == "langgenius/groq" for p in instalados):
        return
    h.post(f"{url}/install/marketplace", headers=cab,
           json={"plugin_unique_identifiers": [PLUGIN_GROQ]}).raise_for_status()
    for _ in range(36):  # até 3 minutos
        time.sleep(5)
        instalados = h.get(f"{url}/list", headers=cab, params={"page": 1, "page_size": 100}).json().get("plugins", [])
        if any(p.get("plugin_id") == "langgenius/groq" for p in instalados):
            etapa("plugin do Groq instalado")
            return
    raise SystemExit("o plugin do Groq não terminou de instalar.")


def contas_ativas(h: httpx.Client, cab: dict) -> set:
    r = h.get(f"{DIFY}/console/api/workspaces/current/model-providers", headers=cab)
    r.raise_for_status()
    return {p["provider"] for p in r.json()["data"] if (p.get("custom_configuration") or {}).get("status") == "active"}


def escolher_modelo(atual: dict, ativas: set) -> dict:
    """Mantém a escolha do aluno que funciona. Modelo desligado ou sem conta vai para o Groq ou o Gemini."""
    if atual.get("provider") in ativas and atual.get("name") not in MODELOS_DESLIGADOS:
        return atual
    parametros = {k: v for k, v in (atual.get("completion_params") or {}).items() if k != "reasoning_effort"}
    if GROQ in ativas or GEMINI not in ativas:  # sem nenhuma conta, já fica pronto para a chave do Groq
        parametros["reasoning_effort"] = "low"
        return {**atual, "provider": GROQ, "name": MODELO_GROQ, "completion_params": parametros}
    return {**atual, "provider": GEMINI, "name": MODELO_GEMINI, "completion_params": parametros}


def criar_base(h: httpx.Client, cab: dict) -> str:
    """Cria a base com cada artigo inteiro em um trecho (o Dify corta .md em cada título ##)."""
    ids = []
    for f in sorted(BASE.glob("*.md")):
        r = h.post(f"{DIFY}/console/api/files/upload", headers=cab, params={"source": "datasets"},
                   files={"file": (f.name, f.read_bytes(), "text/markdown")})
        r.raise_for_status()
        ids.append(r.json()["id"])
    if not ids:
        raise SystemExit("a pasta base-de-conhecimento está vazia.")
    r = h.post(f"{DIFY}/console/api/datasets/init", headers=cab, json={
        "data_source": {"type": "upload_file", "info_list": {"data_source_type": "upload_file",
                                                             "file_info_list": {"file_ids": ids}}},
        "indexing_technique": "economy",
        "process_rule": {"mode": "custom", "rules": {
            "pre_processing_rules": [{"id": "remove_extra_spaces", "enabled": True},
                                     {"id": "remove_urls_emails", "enabled": False}],
            "segmentation": {"separator": "\n\n\n", "max_tokens": 1024, "chunk_overlap": 0}}},
        "doc_form": "text_model", "doc_language": "Portuguese",
        "retrieval_model": {"search_method": "keyword_search", "reranking_enable": False, "top_k": 2,
                            "score_threshold_enabled": False, "score_threshold": 0}})
    r.raise_for_status()
    dados = r.json()
    base_id = dados["dataset"]["id"]
    for _ in range(40):
        time.sleep(3)
        r = h.get(f"{DIFY}/console/api/datasets/{base_id}/batch/{dados['batch']}/indexing-status", headers=cab)
        if all(d["indexing_status"] in ("completed", "error") for d in r.json()["data"]):
            break
    for nome in (NOME_BASE, f"{NOME_BASE} (kit)"):  # o aluno pode já ter uma base com esse nome
        r = h.patch(f"{DIFY}/console/api/datasets/{base_id}", headers=cab,
                    json={"name": nome, "permission": "only_me", "indexing_technique": "economy"})
        if r.is_success:
            etapa(f"base de conhecimento criada: {nome}")
            break
    return base_id


def base_do_kit(h: httpx.Client, cab: dict) -> str:
    """Reaproveita a base que o kit já criou neste ambiente; senão, cria."""
    marca = CONFIG / ".dify_base"
    if marca.exists():
        base_id = marca.read_text(encoding="utf-8").strip()
        if h.get(f"{DIFY}/console/api/datasets/{base_id}", headers=cab).status_code == 200:
            return base_id
    base_id = criar_base(h, cab)
    marca.write_text(base_id, encoding="utf-8")
    return base_id


def atualizar_fluxo(g: dict, base_id: str, ativas: set):
    """Aplica as mudanças do kit no grafo do aluno, sem refazer o que ele personalizou."""
    nos = {n["id"]: n["data"] for n in g["nodes"]}
    for nome in ("classificador", "llm"):
        if nome in nos and nos[nome].get("model"):
            nos[nome]["model"] = escolher_modelo(nos[nome]["model"], ativas)
    if "base" in nos:
        nos["base"]["dataset_ids"] = [base_id]
        nos["base"].setdefault("multiple_retrieval_config", {})["top_k"] = 2
    if "llm" in nos:
        nos["llm"]["reasoning_format"] = "separated"
        texto = nos["llm"]["prompt_template"][0]
        if "Responda SOMENTE com base no CONTEXTO abaixo." in texto["text"]:  # instrução antiga, sem personalização
            texto["text"] = INSTRUCAO
    # Pergunta de processo sem número vai para a base; só número inválido pede correção
    if {"numero_ok", "base", "resp_pede_numero"} <= nos.keys():
        casos = nos["numero_ok"]["cases"]
        if not any(c.get("case_id") == "invalido" for c in casos):
            casos.append({"case_id": "invalido", "id": "invalido", "logical_operator": "and", "conditions": [
                {"id": "c-num-2", "variable_selector": ["valida_numero", "numero"],
                 "comparison_operator": "not empty", "value": "", "varType": "string"}]})
            nos["resp_pede_numero"].update(title="Resposta: número inválido", answer=RESPOSTA_NUMERO)
        for e in g["edges"]:
            if e["source"] == "numero_ok" and e["target"] == "resp_pede_numero" and e["sourceHandle"] == "false":
                e.update(id="numero_ok-invalido-resp_pede_numero", sourceHandle="invalido")
        if not any(e["source"] == "numero_ok" and e["target"] == "base" for e in g["edges"]):
            modelo = next(e for e in g["edges"] if e["target"] == "resp_pede_numero")
            g["edges"].append({**modelo, "id": "numero_ok-false-base", "sourceHandle": "false", "target": "base",
                               "data": {**modelo["data"], "targetType": "knowledge-retrieval"}})


def atualizar_bot(h: httpx.Client, cab: dict, app_id: str):
    instalar_groq(h, cab)
    base_id = base_do_kit(h, cab)
    r = h.get(f"{DIFY}/console/api/apps/{app_id}/workflows/draft", headers=cab)
    r.raise_for_status()
    rascunho = r.json()
    atualizar_fluxo(rascunho["graph"], base_id, contas_ativas(h, cab))
    h.post(f"{DIFY}/console/api/apps/{app_id}/workflows/draft", headers=cab,
           json={"graph": rascunho["graph"], "features": rascunho["features"],
                 "hash": rascunho["hash"]}).raise_for_status()
    h.post(f"{DIFY}/console/api/apps/{app_id}/workflows/publish", headers=cab,
           json={"marked_name": f"Kit versão {VERSAO}", "marked_comment": ""}).raise_for_status()
    etapa(f"Bot STJ atualizado para a versão {VERSAO} do kit")


def main():
    marca = CONFIG / ".dify_versao"
    configurado = (CONFIG / "dify.json").exists()
    if configurado and marca.exists() and marca.read_text(encoding="utf-8").strip() == VERSAO:
        etapa("já configurado")
        return
    with httpx.Client(timeout=60) as h:
        etapa("aguardando o Dify ligar...")
        if esperar(h) == "not_started":
            r = h.post(f"{DIFY}/console/api/setup",
                       json={"email": EMAIL, "name": "Equipe Suporte", "password": SENHA, "language": "pt-BR"})
            etapa(f"conta de administrador: HTTP {r.status_code}")
            r.raise_for_status()
        cab = entrar(h)
        if configurado:
            dados = json.loads((CONFIG / "dify.json").read_text(encoding="utf-8"))
            app_id = dados.get("app_id") or achar_bot(h, cab)
        else:
            app_id = importar_bot(h, cab)
        if not app_id:
            raise SystemExit("não encontrei o app Bot STJ.")
        atualizar_bot(h, cab, app_id)
        marca.write_text(VERSAO, encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        if e.code not in (None, 0):
            print(f"[dify] AVISO: {e.code}. Siga os passos manuais do painel.", flush=True)
        sys.exit(0)
    except Exception as e:  # nunca derruba a inicialização
        print(f"[dify] AVISO: configuração automática falhou ({e}). Siga os passos manuais do painel.", flush=True)

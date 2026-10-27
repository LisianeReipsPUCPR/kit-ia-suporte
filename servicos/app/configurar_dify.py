"""Configura o Dify sozinho na primeira vez (versão Codespaces do kit).

Cria a conta de administrador, importa o Bot STJ, publica e gera a chave da API,
gravando-a em /config/dify.json para o conector. Se algo falhar, o aluno faz
os mesmos passos à mão, como descrito no painel.
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


def main():
    if (CONFIG / "dify.json").exists():
        etapa("já configurado")
        return
    with httpx.Client(timeout=60) as h:
        etapa("aguardando o Dify ligar...")
        if esperar(h) == "not_started":
            r = h.post(f"{DIFY}/console/api/setup",
                       json={"email": EMAIL, "name": "Equipe Suporte", "password": SENHA, "language": "pt-BR"})
            etapa(f"conta de administrador: HTTP {r.status_code}")
            r.raise_for_status()
        r = h.post(f"{DIFY}/console/api/login",
                   json={"email": EMAIL, "password": base64.b64encode(SENHA.encode()).decode(), "remember_me": True})
        r.raise_for_status()
        if r.json().get("result") != "success":
            raise SystemExit(f"login recusado: {r.text}")
        csrf = h.cookies.get("csrf_token") or h.cookies.get("__Host-csrf_token") or ""
        cab = {"X-CSRF-Token": csrf}

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


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        if e.code not in (None, 0):
            print(f"[dify] AVISO: {e.code}. Siga os passos manuais do painel.", flush=True)
        sys.exit(0)
    except Exception as e:  # nunca derruba a inicialização
        print(f"[dify] AVISO: configuração automática falhou ({e}). Siga os passos manuais do painel.", flush=True)

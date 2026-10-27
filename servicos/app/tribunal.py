"""API do tribunal SIMULADA do kit (Aula 6): consulta de processo com autorização por token.

Mostra o que uma API real deve fazer ANTES de qualquer dado chegar à IA:
  processo público: qualquer pessoa vê (200)
  segredo de justiça: 401 sem login | 403 logado sem permissão | 200 só para a parte autorizada
  429 consultas demais (limite) | 422 número inválido | 404 não encontrado
Todos os processos, partes e tokens são fictícios.
"""
import re
import time
from collections import defaultdict, deque

from fastapi import FastAPI, Header, HTTPException, Request

app = FastAPI(title="API do tribunal simulada")

TOKENS = {"TOKEN_PARTE": "Maria (parte do processo 0007777-71.2026.3.00.0000)", "TOKEN_CIDADAO": "Cidadão sem processo"}
PROCESSOS = {
    "00012345220263000000": {"numero": "0001234-52.2026.3.00.0000", "classe": "Recurso Especial",
                             "orgao": "Terceira Turma", "sigilo": False,
                             "ultima_movimentacao": "Conclusos ao relator", "data": "10/10/2026"},
    "00043215020253000000": {"numero": "0004321-50.2025.3.00.0000", "classe": "Agravo em Recurso Especial",
                             "orgao": "Primeira Turma", "sigilo": False,
                             "ultima_movimentacao": "Publicado acórdão", "data": "02/10/2026"},
    "00077777120263000000": {"numero": "0007777-71.2026.3.00.0000", "classe": "Recurso Especial (segredo de justiça)",
                             "orgao": "Quarta Turma", "sigilo": True, "partes_autorizadas": ["TOKEN_PARTE"],
                             "ultima_movimentacao": "Juntada de petição", "data": "15/10/2026"},
}
LIMITE, JANELA = 10, 60  # no máximo 10 consultas por minuto
historico: dict[str, deque] = defaultdict(deque)
registros: list[dict] = []


def dv_ok(n: str) -> bool:
    base = n[:7] + n[9:20] + "00"
    return 98 - int(base) % 97 == int(n[7:9])


@app.get("/processos/{numero}")
def consultar(numero: str, request: Request, authorization: str = Header(default="")):
    token = authorization.removeprefix("Bearer ").strip()
    quem = token or (request.client.host if request.client else "?")
    agora = time.time()
    fila = historico[quem]
    while fila and agora - fila[0] > JANELA:
        fila.popleft()
    fila.append(agora)

    def registrar(status: int):
        registros.append({"quando": time.strftime("%d/%m %H:%M:%S"), "quem": quem, "numero": numero, "status": status})

    if len(fila) > LIMITE:
        registrar(429)
        raise HTTPException(429, "Muitas consultas seguidas. Aguarde 1 minuto.")
    if token and token not in TOKENS:
        registrar(401)
        raise HTTPException(401, "Login inválido. Entre de novo no portal.")
    n = re.sub(r"\D", "", numero)
    if len(n) != 20 or not dv_ok(n):
        registrar(422)
        raise HTTPException(422, "Número de processo inválido (padrão CNJ).")
    p = PROCESSOS.get(n)
    if not p:
        registrar(404)
        raise HTTPException(404, "Processo não encontrado.")
    if p["sigilo"] and not token:
        registrar(401)
        raise HTTPException(401, "Este processo tem acesso restrito. Faça login no portal para consultar.")
    if p["sigilo"] and token not in p.get("partes_autorizadas", []):
        registrar(403)
        raise HTTPException(403, "Este processo tem acesso restrito.")
    registrar(200)
    return {k: v for k, v in p.items() if k != "partes_autorizadas"}


@app.get("/registros")
def ver_registros():
    """Auditoria: quem consultou o quê e quando (últimas 50 consultas)."""
    return registros[-50:]

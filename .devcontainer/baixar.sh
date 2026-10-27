#!/usr/bin/env bash
# Primeira criação do ambiente: baixa tudo o que o kit usa (só acontece uma vez).
cd "$(dirname "$0")/.." || exit 1
for i in $(seq 60); do docker info >/dev/null 2>&1 && break; sleep 2; done
echo "== Baixando os programas do laboratório (só na primeira vez, 10 a 15 minutos) =="
docker network create kit-rede >/dev/null 2>&1 || true
(cd dify && docker compose pull -q)
(cd chatwoot && docker compose pull -q)
(cd servicos && docker compose build -q)
echo "== Download concluído =="

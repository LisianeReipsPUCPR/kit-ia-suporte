#!/usr/bin/env bash
# Corrige o "Erro" ao indexar documentos no Conhecimento do Dify:
# 1. garante a conexão com o pgvector no dify/.env (e reinicia o Dify se preciso);
# 2. troca os modelos de embedding do Gemini que o Google desativou pelo atual;
# 3. manda indexar de novo os documentos que ficaram com erro.
# Uso: bash .devcontainer/corrigir-conhecimento.sh
#      bash .devcontainer/corrigir-conhecimento.sh --vigiar   (fica rodando; usado pelo ligar.sh)
cd "$(dirname "$0")/.." || exit 1

bash .devcontainer/preparar.sh
# O docker compose só recria os containers cuja configuração mudou
(cd dify && docker compose up -d) >/dev/null 2>&1 || { echo "ERRO ao ligar o Dify."; exit 1; }

for i in $(seq 60); do
  [ "$(docker inspect -f '{{.State.Health.Status}}' "$(cd dify && docker compose ps -q api)" 2>/dev/null)" = healthy ] && break
  sleep 5
done

(cd dify && docker compose exec -T api python - "$@") < .devcontainer/corrigir_conhecimento.py

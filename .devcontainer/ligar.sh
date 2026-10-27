#!/usr/bin/env bash
# Liga o laboratório sempre que o Codespace abre. Na primeira vez também configura tudo.
cd "$(dirname "$0")/.." || exit 1
mkdir -p config
exec > >(tee -a config/inicio.log) 2>&1
echo "== Ligando o laboratório do Chatbot STJ =="
for i in $(seq 60); do docker info >/dev/null 2>&1 && break; sleep 2; done

DOM="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
if [ -n "$CODESPACE_NAME" ]; then
  export PUB_PAINEL="https://${CODESPACE_NAME}-8080.${DOM}"
  export PUB_DIFY="https://${CODESPACE_NAME}-8081.${DOM}"
  export PUB_CHATWOOT="https://${CODESPACE_NAME}-3000.${DOM}"
else
  export PUB_PAINEL="http://localhost:8080" PUB_DIFY="http://localhost:8081" PUB_CHATWOOT="http://localhost:3000"
fi
export KIT_EMAIL="equipe@suporte-lab.com.br"

# Primeira vez: senha e chaves secretas exclusivas deste ambiente
if [ ! -f config/.senha ]; then
  echo "Stj@$(tr -dc 'a-z0-9' </dev/urandom | head -c 8)7" > config/.senha
  sed -i "s#^SECRET_KEY_BASE=.*#SECRET_KEY_BASE=$(tr -dc 'a-f0-9' </dev/urandom | head -c 128)#" chatwoot/.env
  sed -i "s#^SECRET_KEY=.*#SECRET_KEY=kit-$(tr -dc 'a-f0-9' </dev/urandom | head -c 48)#" dify/.env
fi
export KIT_SENHA="$(cat config/.senha)"
sed -i "s#^FRONTEND_URL=.*#FRONTEND_URL=${PUB_CHATWOOT}#" chatwoot/.env
docker network create kit-rede >/dev/null 2>&1 || true

echo "[1/4] Ligando o Dify..."
(cd dify && docker compose up -d) || { echo "ERRO ao ligar o Dify. Chame a professora."; exit 1; }

echo "[2/4] Ligando o Chatwoot..."
cd chatwoot || exit 1
if [ ! -f ../config/.chatwoot_pronto ]; then
  echo "      Primeira vez: preparando o banco de dados (alguns minutos)..."
  docker compose up -d postgres redis
  sleep 15
  docker compose run --rm rails bundle exec rails db:chatwoot_prepare || { echo "ERRO ao preparar o banco do Chatwoot."; exit 1; }
  docker compose run --rm -e KIT_EMAIL -e KIT_SENHA -e PUB_PAINEL rails bundle exec rails runner /kit/seed_kit.rb \
    || { echo "ERRO ao configurar o Chatwoot."; exit 1; }
  touch ../config/.chatwoot_pronto
fi
docker compose up -d || { echo "ERRO ao ligar o Chatwoot."; exit 1; }
cd ..

echo "[3/4] Ligando os serviços do kit..."
(cd servicos && docker compose up -d --build) || { echo "ERRO ao ligar os serviços do kit."; exit 1; }

# O chat do painel precisa enxergar o Chatwoot: porta 3000 pública (só o Chatwoot, que tem login)
if [ -n "$CODESPACE_NAME" ]; then
  gh codespace ports visibility 3000:public -c "$CODESPACE_NAME" >/dev/null 2>&1 \
    || echo "      Aviso: torne a porta 3000 pública na aba PORTAS (botão direito > Visibilidade da porta > Public)."
fi

echo "[4/4] Configurando o Dify (primeira vez: até 10 minutos)..."
(cd servicos && docker compose run --rm -e KIT_EMAIL -e KIT_SENHA pagina python configurar_dify.py)

echo
echo "=============================================================="
echo " PRONTO! Abra o painel do kit:"
echo "   ${PUB_PAINEL}"
echo " (ou: aba PORTAS > linha '1. Painel do kit' > ícone do globo)"
echo " Login do Dify e do Chatwoot: ${KIT_EMAIL}  senha: ${KIT_SENHA}"
echo "=============================================================="

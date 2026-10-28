#!/usr/bin/env bash
# Cria os arquivos .env do Dify e do Chatwoot a partir dos modelos (.env.example),
# com chaves secretas exclusivas deste ambiente. Não mexe em arquivos que já existem.
cd "$(dirname "$0")/.." || exit 1
aleatorio() { tr -dc 'a-f0-9' </dev/urandom | head -c "$1"; }

if [ ! -f dify/.env ]; then
  sed -e "s#^EXPOSE_NGINX_PORT=.*#EXPOSE_NGINX_PORT=8081#" \
      -e "s#^EXPOSE_NGINX_SSL_PORT=.*#EXPOSE_NGINX_SSL_PORT=127.0.0.1:8444#" \
      -e "s#^VECTOR_STORE=.*#VECTOR_STORE=pgvector#" \
      -e "s#^SECRET_KEY=.*#SECRET_KEY=kit-$(aleatorio 48)#" \
      dify/.env.example > dify/.env
fi

# O .env.example do Dify não traz a conexão com o pgvector (ela fica em
# envs/core-services/shared.env.example); sem isso a indexação do Conhecimento falha.
if ! grep -q "^PGVECTOR_HOST=" dify/.env; then
  grep -E "^PGVECTOR_" dify/envs/core-services/shared.env.example >> dify/.env
fi

# A porta 8443 mostrava o HTTPS do nginx, que fica desligado (o Codespaces já dá o HTTPS):
# quem abria o link -8443 via erro. Agora a 8443 também entrega o Dify (ver override);
# o HTTPS interno fica só no localhost:8444. Corrige ambientes criados antes disso.
sed -i "s#^EXPOSE_NGINX_SSL_PORT=8443\$#EXPOSE_NGINX_SSL_PORT=127.0.0.1:8444#" dify/.env

if [ ! -f chatwoot/.env ]; then
  sed -e "s#^SECRET_KEY_BASE=.*#SECRET_KEY_BASE=$(aleatorio 128)#" \
      chatwoot/.env.example > chatwoot/.env
fi

#!/usr/bin/env bash
# Cria os arquivos .env do Dify e do Chatwoot a partir dos modelos (.env.example),
# com chaves secretas exclusivas deste ambiente. Não mexe em arquivos que já existem.
cd "$(dirname "$0")/.." || exit 1
aleatorio() { tr -dc 'a-f0-9' </dev/urandom | head -c "$1"; }

if [ ! -f dify/.env ]; then
  sed -e "s#^EXPOSE_NGINX_PORT=.*#EXPOSE_NGINX_PORT=8081#" \
      -e "s#^EXPOSE_NGINX_SSL_PORT=.*#EXPOSE_NGINX_SSL_PORT=8443#" \
      -e "s#^VECTOR_STORE=.*#VECTOR_STORE=pgvector#" \
      -e "s#^SECRET_KEY=.*#SECRET_KEY=kit-$(aleatorio 48)#" \
      dify/.env.example > dify/.env
fi

if [ ! -f chatwoot/.env ]; then
  sed -e "s#^SECRET_KEY_BASE=.*#SECRET_KEY_BASE=$(aleatorio 128)#" \
      chatwoot/.env.example > chatwoot/.env
fi

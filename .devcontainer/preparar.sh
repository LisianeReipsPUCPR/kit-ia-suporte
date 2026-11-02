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

# Ambientes criados antes dos volumes nomeados guardam os dados em pastas do projeto: continuam
# nelas, para o Dify não abrir vazio. O ambiente novo usa volumes (ver docker-compose.override.yaml).
montagem="$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Type}}{{end}}{{end}}' dify-db_postgres-1 2>/dev/null)"
if ! grep -q "^KIT_VOL_DB=" dify/.env; then
  if [ "$montagem" = bind ] || { [ -z "$montagem" ] && sudo -n test -e dify/volumes/db/data/pgdata/PG_VERSION 2>/dev/null; }; then
    cat >> dify/.env <<'PASTAS'

# Dados deste ambiente em pastas do projeto (criado antes dos volumes nomeados)
KIT_VOL_DB=./volumes/db/data
KIT_VOL_STORAGE=./volumes/app/storage
KIT_VOL_REDIS=./volumes/redis/data
KIT_VOL_WEAVIATE=./volumes/weaviate
KIT_VOL_SANDBOX=./volumes/sandbox/dependencies
KIT_VOL_PLUGINS=./volumes/plugin_daemon
PASTAS
  fi
fi

if [ ! -f chatwoot/.env ]; then
  sed -e "s#^SECRET_KEY_BASE=.*#SECRET_KEY_BASE=$(aleatorio 128)#" \
      chatwoot/.env.example > chatwoot/.env
fi

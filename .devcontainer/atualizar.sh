#!/usr/bin/env bash
# Traz a versão mais nova do kit do repositório da professora, toda vez que o Codespace liga.
# Nunca apaga trabalho do aluno: se a junção conflitar, desiste e o kit liga na versão atual.
# Falha de rede também não impede o laboratório de ligar. O resultado vai para o painel.
cd "$(dirname "$0")/.." || exit 0
PROFESSORA="LisianeReipsPUCPR"
ORIGEM="https://github.com/${PROFESSORA}/kit-ia-suporte.git"
mkdir -p config

resultado() {  # situacao, mensagem
  printf '{"situacao": "%s", "versao": "%s", "msg": "%s"}\n' "$1" "$(git rev-parse --short HEAD)" "$2" > config/atualizacao.json
  echo "      Atualização do kit: $2"
}

# A professora publica daqui: o ambiente dela não recebe nada automaticamente
if [ "$GITHUB_USER" = "$PROFESSORA" ]; then
  resultado ok "ambiente da professora: não se atualiza sozinho."
  exit 0
fi

if ! timeout 60 git fetch --quiet "$ORIGEM" main; then
  resultado aviso "sem conexão com o repositório da professora; segue na versão atual."
  exit 0
fi
if git merge-base --is-ancestor FETCH_HEAD HEAD; then
  resultado ok "já está na versão mais nova."
  exit 0
fi
if git -c user.name="Kit IA" -c user.email="kit-ia@users.noreply.github.com" \
     merge --quiet --no-edit FETCH_HEAD >/dev/null 2>&1; then
  resultado ok "atualizado para a versão mais nova."
  exit 0
fi
git merge --abort >/dev/null 2>&1
resultado conflito "suas alterações conflitam com a versão nova; chame a professora."
exit 0

#!/usr/bin/env bash
set -euo pipefail

senha_valida() {
  local senha="${1:-}"
  [[ -n "$senha" ]] &&
    [[ ${#senha} -ge 6 ]] &&
    [[ "$senha" =~ [A-Z] ]] &&
    [[ "$senha" =~ [a-z] ]] &&
    [[ "$senha" =~ [0-9] ]] &&
    [[ "$senha" =~ [^A-Za-z0-9] ]]
}

senha_gerar() {
  local chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%*?_' 
  local senha

  while :; do
    set +o pipefail
    senha=$(tr -dc "$chars" </dev/urandom | head -c 16)
    set -o pipefail
    if senha_valida "$senha"; then
      printf '%s' "$senha"
      return 0
    fi
  done
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  if [[ $# -gt 0 ]]; then
    if senha_valida "$1"; then
      printf '%s\n' "$1"
      exit 0
    fi
    echo "Senha inválida: deve ter pelo menos 6 caracteres, incluir maiúscula, minúscula, número e caractere especial." >&2
    exit 1
  fi

  senha_gerar
fi

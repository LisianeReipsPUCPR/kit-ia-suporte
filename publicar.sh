#!/usr/bin/env bash
# Publica o kit no GitHub e mostra o link (o "botão Play") para enviar aos alunos.
# Uso: abra um terminal DENTRO desta pasta e rode:  bash publicar.sh
#      (nome do repositório opcional: bash publicar.sh outro-nome)
# Windows: use o "Git Bash" (vem com o Git for Windows). Pode rodar de novo para enviar atualizações.
set -e
cd "$(dirname "$0")"
REPO="${1:-kit-ia-suporte}"

parar() { echo; echo "ERRO: $1"; echo; exit 1; }

echo "== Publicando o kit no GitHub =="

# 1. Programas necessários
command -v git >/dev/null 2>&1 || parar "o Git não está instalado.
  Windows: https://git-scm.com/download/win   (instale e rode este script pelo 'Git Bash')
  Linux:   sudo apt install git"
command -v gh >/dev/null 2>&1 || parar "o GitHub CLI (gh) não está instalado.
  Windows: https://cli.github.com  (baixe, instale e abra o Git Bash de novo)
  Linux:   sudo apt install gh"
[ -d .devcontainer ] || parar "rode este script dentro da pasta do kit (a que tem a pasta .devcontainer)."

# 2. Login no GitHub (abre o navegador só na primeira vez)
if ! gh auth status >/dev/null 2>&1; then
  echo "[1/4] Entrando no GitHub: siga as instruções (copie o código e confirme no navegador)."
  gh auth login --hostname github.com --git-protocol https --web
fi
gh auth setup-git >/dev/null 2>&1 || true
USUARIO="$(gh api user -q .login)" || parar "não consegui ler o seu usuário do GitHub."
ID="$(gh api user -q .id)"
echo "[1/4] Conectada ao GitHub como: $USUARIO"

# 3. Prepara os arquivos (só nesta pasta; não mexe em mais nada do computador)
echo "[2/4] Preparando os arquivos..."
[ -d .git ] || git init -q
git config user.name  >/dev/null 2>&1 || git config user.name "$USUARIO"
git config user.email >/dev/null 2>&1 || git config user.email "${ID}+${USUARIO}@users.noreply.github.com"
git config core.autocrlf false
git checkout -q -B main
git add -A
git diff --cached --quiet || git commit -q -m "Kit IA para Centros de Suporte ($(date +%d/%m/%Y\ %H:%M))"

# 4. Cria o repositório público (ou atualiza, se já existir) e envia
if gh repo view "$USUARIO/$REPO" >/dev/null 2>&1; then
  echo "[3/4] O repositório $USUARIO/$REPO já existe: enviando a versão atual..."
  git remote remove origin >/dev/null 2>&1 || true
  git remote add origin "https://github.com/$USUARIO/$REPO.git"
  git push -q -u origin main --force
else
  echo "[3/4] Criando o repositório público $USUARIO/$REPO e enviando os arquivos..."
  git remote remove origin >/dev/null 2>&1 || true
  gh repo create "$REPO" --public \
     --description "Laboratório da disciplina IA para Centros de Suporte (Chatbot STJ, dados fictícios)" \
     --source=. --remote=origin --push >/dev/null
fi

# 5. Link para os alunos
LINK="https://codespaces.new/$USUARIO/$REPO?quickstart=1"
printf '%s\n' "$LINK" > LINK-DOS-ALUNOS.txt
echo "[4/4] Pronto!"
echo
echo "=============================================================="
echo " Repositório: https://github.com/$USUARIO/$REPO"
echo " Link para os alunos (o 'botão Play'):"
echo "   $LINK"
echo " (o link também foi salvo em LINK-DOS-ALUNOS.txt)"
echo "=============================================================="
echo " Próximo passo: abra o link você mesma e siga o teste do PROFESSORA.md."

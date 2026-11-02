> **Observação:** quem fez o fork antes de 2 de novembro de 2026 precisa atualizá-lo uma única vez, porque
> ninguém consegue alterar o fork de outra pessoa de fora. Avise esses alunos: o passo a passo está em
> [Atualizar os alunos](#atualizar-os-alunos). Depois disso, o kit se atualiza sozinho sempre que o ambiente liga.

## Publicar (uma vez, 10 minutos)
1. Entrar em https://github.com (criar a conta, se precisar) › **New repository**.
   Nome: `kit-ia-suporte` · **Public** · Create repository.
2. Na página do repositório: **uploading an existing file** › arrastar **o conteúdo**
   da pasta `kit-ia-suporte-codespaces` (as pastas e arquivos, não a pasta em si).
   Incluir as pastas que começam com ponto (`.devcontainer`). Commit changes.
   - Se o Windows esconder `.devcontainer`: no Explorador, Exibir › Mostrar › Itens ocultos.
3. Montar o link para os alunos:
   `https://codespaces.new/SEU-USUARIO/kit-ia-suporte?quickstart=1`
   (trocar SEU-USUARIO). Esse é o "botão Play": abre o ambiente pronto ou reabre o existente.

## Testar (35 minutos)
- [ ] Abrir o link acima e escolher **Create new codespace** (a máquina de 4 núcleos é escolhida sozinha).
- [ ] Conferir se o terminal mostra o download e depois **PRONTO!** (primeira vez: 15 a 25 min).
- [ ] Abrir o painel e conferir se os itens ficam verdes, incluindo **Chatwoot configurado** e **Dify configurado**.
      Se "Dify configurado" ficar vermelho, anotar a linha `[dify] AVISO` do terminal.
- [ ] Entrar no Dify com o login do painel e conferir se o app **Bot STJ** já está lá.
- [ ] Instalar o Groq (ou o Gemini) com a sua chave e clicar em **Publicar** no Bot STJ.
- [ ] Testar na pré-visualização do Dify: `oi`, `qual o andamento do processo 0001234-52.2026.3.00.0000`,
      `quero fazer uma reclamação sobre a demora`, `receita de pudim`.
- [ ] Testar no balão do painel: conferir se `oi` responde e se `ATENDENTE` transfere a conversa para o Chatwoot.
- [ ] Rodar os testes de ouvidoria e tribunal do painel (200, 401, 403, 429).
- [ ] Fechar a aba, esperar o ambiente desligar (ou em github.com/codespaces › ... › Stop),
      reabrir pelo mesmo link e conferir se liga em 2 a 3 minutos com tudo no lugar.

Se um passo falhar, mandar o print e as últimas linhas do terminal (também ficam em `config/inicio.log`).

## Atualizar os alunos
Depois de enviar para a `main`, cada ambiente de aluno busca a versão nova sozinho ao ligar
(`.devcontainer/atualizar.sh`) e o painel mostra o resultado em **Kit atualizado**.
Se o fluxo do Bot STJ mudou, suba `VERSAO` em `servicos/app/configurar_dify.py`: a atualização do
Dify roda uma vez em cada ambiente e preserva o que o aluno personalizou.
Forks anteriores a este mecanismo precisam de uma ação, uma única vez:
- quem **já tem Codespace**: no Terminal, rodar
  `curl -fsSL https://raw.githubusercontent.com/LisianeReipsPUCPR/kit-ia-suporte/main/.devcontainer/atualizar.sh | bash && bash .devcontainer/ligar.sh`
  (não usar `git pull`: ele falha ou apaga os `.env` do aluno, com as chaves dele)
- quem **ainda não abriu**: na página do fork, clicar em **Sync fork** › **Update branch** e abrir o Codespace.

## Próxima aula: atualizar o kit com os alunos
Serve para quem fez o fork antes de 2 de novembro de 2026. Basta fazer uma vez.

**Antes da aula**
- [ ] Pedir a um aluno que faça os passos abaixo e confirmar que deu certo. Esse caminho ainda não foi testado em um Codespace real.
- [ ] Abrir um Codespace novo em um fork de teste e seguir o `COMECE-AQUI.md`, para conferir o caminho de quem começa agora.
- [ ] Avisar a turma para criar uma chave gratuita em https://console.groq.com/keys. Cada aluno usa a própria chave.

**Na aula, com os alunos**
1. Quem **já abriu o Codespace**: abrir o Codespace, clicar no Terminal (painel de baixo), colar o comando abaixo, teclar Enter e esperar aparecer **PRONTO!**.
   ```
   curl -fsSL https://raw.githubusercontent.com/LisianeReipsPUCPR/kit-ia-suporte/main/.devcontainer/atualizar.sh | bash && bash .devcontainer/ligar.sh
   ```
   Não usar `git pull`: ele falha ou apaga os `.env` do aluno, com as chaves dele.
2. Quem **ainda não abriu**: na página do fork, clicar em **Sync fork** › **Update branch** e abrir o Codespace normalmente.
3. Abrir o painel do kit e conferir se **Kit atualizado** está **OK**.
4. Clicar em **Abrir o Dify** › **Integrações** › **Groq** e colar a chave. Quem já usa o Gemini pode continuar com ele.
5. Voltar ao painel, conferir se a conta aparece como **conectada** e clicar em **Testar agora**.
6. Abrir uma **conversa nova** no balão de chat e enviar `oi`, `como emito uma certidão negativa?`, `receita de pudim` e `ATENDENTE`.

**Se algo der errado**
| O que aparece | O que fazer |
|---|---|
| **Kit atualizado** não aparece no painel | A atualização não aconteceu: repetir o passo 1 ou 2. |
| **Kit atualizado** com **ver aviso** | No Terminal, rodar `cat config/atualizacao.json` para ler o motivo. Em conflito, nada se perde e o kit segue na versão atual. |
| Conta **não conectada** | Refazer o passo 4 com a chave do próprio aluno. |
| **Limite atingido** | O painel mostra quando volta. No Groq costuma ser questão de segundos ou minutos, porque cada chave aguenta cerca de 5 perguntas por minuto. |
| **Chat chega ao robô: bloqueado** | Rodar `bash .devcontainer/ligar.sh` no Terminal e abrir uma conversa nova. |
| O robô não responde em uma conversa antiga | Ela já está com o atendente humano: abrir uma conversa nova. |

## Na aula
- Conferir se quem já tinha fork fez a atualização: no painel do kit, **Kit atualizado** precisa estar **OK**.
- Garantir que os alunos tenham conta no GitHub (gratuita, 5 minutos).
- Pedir que abram o link **logo no início** e, enquanto o ambiente liga (primeira vez), apresentar a parte teórica.
- Garantir que cada aluno tenha uma chave do Groq (gratuita, https://console.groq.com/keys).

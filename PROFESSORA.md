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
- [ ] Instalar o Gemini com a sua chave e clicar em **Publicar** no Bot STJ.
- [ ] Testar na pré-visualização do Dify: `oi`, `qual o andamento do processo 0001234-52.2026.3.00.0000`,
      `quero fazer uma reclamação sobre a demora`, `receita de pudim`.
- [ ] Testar no balão do painel: conferir se `oi` responde e se `ATENDENTE` transfere a conversa para o Chatwoot.
- [ ] Rodar os testes de ouvidoria e tribunal do painel (200, 401, 403, 429).
- [ ] Fechar a aba, esperar o ambiente desligar (ou em github.com/codespaces › ... › Stop),
      reabrir pelo mesmo link e conferir se liga em 2 a 3 minutos com tudo no lugar.

Se um passo falhar, mandar o print e as últimas linhas do terminal (também ficam em `config/inicio.log`).

## Na aula
- Garantir que os alunos tenham conta no GitHub (gratuita, 5 minutos).
- Pedir que abram o link **logo no início** e, enquanto o ambiente liga (primeira vez), apresentar a parte teórica.
- Garantir que cada aluno tenha uma chave do Google AI Studio (gratuita, conta Google).

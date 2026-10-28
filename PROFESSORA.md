
1. Entre em https://github.com (crie a conta, se precisar) e abra https://github.com/LisianeReipsPUCPR/kit-ia-suporte › **Fork** (canto superior direito) › mantenha o nome `kit-ia-suporte` › **Create fork**.
   * A cópia já vem completa, incluindo a pasta `.devcontainer`. Não é preciso enviar arquivos.
2. O link para os alunos é: `https://codespaces.new/SEU-USUARIO/kit-ia-suporte?quickstart=1` (troque SEU-USUARIO pelo seu usuário do GitHub). Esse é o "botão Play": abre o ambiente pronto ou reabre o existente.
3. Quando o repositório original for atualizado, entre no seu fork e clique em **Sync fork** › **Update branch** para receber as mudanças.

O passo 3 é opcional. Ele substitui o reenvio manual de arquivos que a versão anterior exigia.

## Testar (35 minutos)
- [ ] Abra o link acima. Escolha **Create new codespace** (a máquina de 4 núcleos é escolhida sozinha).
- [ ] O terminal mostra o download e depois **PRONTO!** (primeira vez: 15 a 25 min).
- [ ] O painel abre e os itens ficam verdes, incluindo **Chatwoot configurado** e **Dify configurado**.
      Se "Dify configurado" ficar vermelho, anote a linha `[dify] AVISO` do terminal.
- [ ] Dify: entra com o login do painel e o app **Bot STJ** já está lá.
- [ ] Instale o Gemini com a sua chave e clique em **Publicar** no Bot STJ.
- [ ] Na pré-visualização do Dify: `oi`, `qual o andamento do processo 0001234-52.2026.3.00.0000`,
      `quero fazer uma reclamação sobre a demora`, `receita de pudim`.
- [ ] Balão do painel: `oi` responde; `ATENDENTE` transfere e a conversa aparece no Chatwoot.
- [ ] Testes de ouvidoria e tribunal do painel (200, 401, 403, 429).
- [ ] Feche a aba, espere o ambiente desligar (ou em github.com/codespaces › ... › Stop),
      reabra pelo mesmo link: liga em 2 a 3 minutos e tudo continua lá.

Se um passo falhar, mande o print e as últimas linhas do terminal (também ficam em `config/inicio.log`).

## Na aula
- Alunos precisam de conta no GitHub (gratuita, 5 minutos).
- Peça que abram o link **logo no início**; enquanto liga (primeira vez), apresente a parte teórica.
- Cada aluno precisa de uma chave do Google AI Studio (gratuita, conta Google).

1. Entrar em https://github.com (criar a conta, se precisar) e abrir https://github.com/LisianeReipsPUCPR/kit-ia-suporte › **Fork** (canto superior direito) › manter o nome `kit-ia-suporte` › **Create fork**.
   * A cópia já vem completa, incluindo a pasta `.devcontainer`. Não é preciso enviar arquivos.
2. Montar o link para os alunos: `https://codespaces.new/SEU-USUARIO/kit-ia-suporte?quickstart=1` (trocar SEU-USUARIO pelo usuário do GitHub). Esse é o "botão Play": abre o ambiente pronto ou reabre o existente.
3. Quando o repositório original for atualizado, entrar no fork e clicar em **Sync fork** › **Update branch** para receber as mudanças.

O passo 3 é opcional. Com ele, não é preciso reenviar arquivos manualmente.

## Testar (35 minutos)
- [ ] Abrir o link acima e escolher **Create new codespace** (a máquina de 4 núcleos é escolhida sozinha).
- [ ] Aguardar o terminal mostrar o download e depois **PRONTO!** (primeira vez: 15 a 25 min).
- [ ] Verificar se o painel abre e se os itens ficam verdes, incluindo **Chatwoot configurado** e **Dify configurado**.
      Se "Dify configurado" ficar vermelho, anotar a linha `[dify] AVISO` do terminal.
- [ ] Entrar no Dify com o login do painel e conferir se o app **Bot STJ** já está lá.
- [ ] Instalar o Gemini com a chave pessoal e clicar em **Publicar** no Bot STJ.
- [ ] Na pré-visualização do Dify, testar: `oi`, `qual o andamento do processo 0001234-52.2026.3.00.0000`,
      `quero fazer uma reclamação sobre a demora`, `receita de pudim`.
- [ ] No balão do painel, conferir se `oi` responde e se `ATENDENTE` transfere a conversa para o Chatwoot.
- [ ] Rodar os testes de ouvidoria e tribunal do painel (200, 401, 403, 429).
- [ ] Fechar a aba, esperar o ambiente desligar (ou ir em github.com/codespaces › ... › Stop)
      e reabrir pelo mesmo link: deve ligar em 2 a 3 minutos com tudo preservado.

Se um passo falhar, tirar um print e copiar as últimas linhas do terminal (também ficam em `config/inicio.log`) para enviar.

## Na aula
- Garantir que os alunos tenham conta no GitHub (gratuita, 5 minutos).
- Pedir que abram o link **logo no início**; enquanto liga (primeira vez), apresentar a parte teórica.
- Garantir que cada aluno tenha uma chave do Google AI Studio (gratuita, conta Google).

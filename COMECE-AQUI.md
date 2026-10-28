# Laboratório do Chatbot STJ — comece aqui

Este é o **seu** ambiente: só você o vê. Os dados são fictícios.

## 1. Espere ligar
Na primeira vez, o laboratório leva de **15 a 25 minutos** para ligar. Nas próximas vezes, 2 a 3 minutos.

- Se aparecer no topo a faixa **Modo Restrito**, clique em **Gerenciar** › **Confiar**.
- Para acompanhar, abra o **Terminal** (painel de baixo) e digite:
  `tail -15 config/inicio.log`
  Aparecem as etapas **[1/4] a [4/4]**. Quando aparecer **PRONTO!**, siga para o passo 2.
  Se ainda não apareceu, espere um pouco e digite o comando de novo.

## 2. Abra o painel do kit
Clique no endereço que aparece depois de **PRONTO!** ou, na aba **PORTAS**, na linha
**1. Painel do kit**, clique no ícone do globo. O login e a senha aparecem no painel.

## 3. Ligue a IA (uma vez só, cerca de 10 minutos)

### A. Conecte o Gemini
1. No painel, clique em **Abrir o Dify** e entre com o login e a senha do painel.
2. No menu lateral esquerdo, clique em **Integrações**.
3. Clique na lupa, pesquise **Gemini** e clique em **Instalar**.
4. Dentro do Gemini, dê o nome **API Teste - Gemini** e cole a sua chave gratuita do
   Google AI Studio (https://aistudio.google.com/apikey).
5. Quando a lista de modelos aparecer, escolha **Gemini 3 Lite**.

### B. Crie a base de conhecimento
6. Aqui no Codespace, na lista de arquivos à esquerda, abra a pasta **base-de-conhecimento**,
   selecione os 5 arquivos (clique no primeiro, segure **Shift** e clique no último),
   clique com o botão direito e escolha **Baixar** (Download). Eles vão para o seu computador.
7. No Dify, clique em **Conhecimento** (menu superior) e, na tela da base de conhecimento:
   1. Clique em **Criar uma base de conhecimento pronta para uso**.
   2. Na próxima tela, clique em **Importar de arquivo**.
   3. Arraste os 5 arquivos baixados para a área indicada.
   4. Clique em **Próximo**.
8. Na barra superior aparece a etapa **(Step 2) Pré-processamento e Limpeza de Texto**.
   Deixe a segmentação como está (padrão). Em **Modo de índice**, escolha **Alta qualidade**
   e o modelo de embedding do Gemini. Se não aparecer nenhum, escolha **Econômico**.
9. Clique em **Salvar e processar** e espere todos os arquivos ficarem como **Disponível**.
   Se algum ficar como **Erro**, chame a professora antes de seguir.
10. Clique no nome da base (no topo) e renomeie para **Base STJ – Atendimento**.

### C. Ligue a base e o modelo ao bot
11. Vá em **Estúdio** e abra o app **Bot STJ**.
12. Clique no nó **Base de conhecimento** › no **+** ao lado de "Conhecimento" ›
    marque **Base STJ – Atendimento** › **Adicionar**.
13. Clique no nó **Classificador de escopo** e confira se o modelo é o **Gemini 3 Lite**.
    Faça o mesmo no nó **Redigir resposta (LLM)**. Se aparecer um aviso, escolha o modelo.
14. Clique em **Publicar** › **Publicar atualização**.

### D. Teste
15. No painel do kit, abra o balão de chat (canto inferior direito) e envie, um de cada vez:
    `oi`, depois `como emito uma certidão negativa?`, depois `receita de pudim`
    e, por último, `ATENDENTE`.
16. No painel, clique em **Abrir o Chatwoot** › **Conversas**: a conversa em que você pediu
    ATENDENTE aparece como **Aberta**.

## Dúvidas? Pergunte ao Copilot
Clique no ícone de **Chat** (canto superior direito desta tela) e pergunte em português, por exemplo:
"Para que serve a pasta servicos?" ou "O painel está com itens vermelhos, o que faço?".
Ele conhece este laboratório. Nunca cole senhas ou chaves no chat.

## Ao terminar a aula
Feche a aba do navegador. O ambiente desliga sozinho depois de um tempo sem uso e **tudo fica guardado**.
Para voltar: https://github.com/codespaces › clique no seu ambiente.

**Não crie um segundo ambiente** e **não cadastre cartão no GitHub**: a cota gratuita
dá para o curso inteiro se cada aluno usar um ambiente só.

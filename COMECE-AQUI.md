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

## 3. Ligue a IA (uma vez só, cerca de 3 minutos)

O bot, a base de conhecimento e o plugin do Groq já vêm prontos. Falta só a sua chave.

### A. Conecte o Groq
1. No painel, clique em **Abrir o Dify** e entre com o login e a senha do painel.
2. No menu lateral esquerdo, clique em **Integrações** e abra o **Groq**.
3. Dê o nome **API Teste - Groq** e cole a sua chave gratuita, criada em
   https://console.groq.com/keys. Os limites da sua conta aparecem em
   https://console.groq.com/settings/limits.

**Prefere usar o Gemini?** Em **Integrações**, instale **Gemini** e cole a chave gratuita do Google
AI Studio (https://aistudio.google.com/apikey). Depois, no app **Bot STJ**, escolha **Gemini 3.5
Flash Lite** nos nós **Classificador de escopo** e **Redigir resposta (LLM)** e clique em **Publicar**.
O limite gratuito do Gemini costuma ser bem menor: se o robô parar, o painel do kit avisa no item 1.

### B. Teste
4. No painel do kit, confira se a **Conta do Groq** aparece como **conectada** e clique em **Testar agora**.
5. Abra o balão de chat (canto inferior direito) e envie, um de cada vez:
   `oi`, depois `como emito uma certidão negativa?`, depois `receita de pudim`
   e, por último, `ATENDENTE`.
6. No painel, clique em **Abrir o Chatwoot** › **Conversas**: a conversa em que você pediu
   ATENDENTE aparece como **Aberta**.

**Quer montar a sua própria base?** Os artigos estão na pasta **base-de-conhecimento**. No Dify, em
**Conhecimento**, importe os arquivos e, em **Segmentação**, troque o **identificador de segmento** por
`\n\n\n`, com tamanho máximo 1024 e sobreposição 0: cada artigo precisa ficar inteiro em um só pedaço,
senão o robô recebe o texto pela metade e pode inventar o resto. O kit já traz a **Base STJ – Atendimento** assim.

**O kit se atualiza sozinho** sempre que o ambiente liga. O painel mostra o resultado em **Kit atualizado**.

## Dúvidas? Pergunte ao Copilot
Clique no ícone de **Chat** (canto superior direito desta tela) e pergunte em português, por exemplo:
"Para que serve a pasta servicos?" ou "O painel está com itens vermelhos, o que faço?".
Ele conhece este laboratório. Nunca cole senhas ou chaves no chat.

## Ao terminar a aula
Feche a aba do navegador. O ambiente desliga sozinho depois de um tempo sem uso e **tudo fica guardado**.
Para voltar: https://github.com/codespaces › clique no seu ambiente.

**Não crie um segundo ambiente** e **não cadastre cartão no GitHub**: a cota gratuita
dá para o curso inteiro se cada aluno usar um ambiente só.

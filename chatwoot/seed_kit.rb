# Kit IA para Centros de Suporte: prepara o Chatwoot na primeira execução.
# Cria a conta da equipe, o usuário administrador, a caixa "Chat on-line" e o bot "Lia",
# e grava os dados que o conector e a página de teste precisam em /kit/config/chatwoot.json.
# Pode ser executado de novo sem duplicar nada.
require 'json'

EMAIL = ENV.fetch('KIT_EMAIL', 'equipe@suporte-lab.com.br')
SENHA = ENV.fetch('KIT_SENHA', 'Suporte@2026')
BOT_URL = 'http://conector:8000/webhook'

user = User.find_by(email: EMAIL)
unless user
  user = User.new(name: 'Equipe Suporte', email: EMAIL, password: SENHA,
                  password_confirmation: SENHA, type: 'SuperAdmin')
  user.skip_confirmation!
  user.save!
end

account = Account.find_by(name: 'Central de Atendimento STJ (laboratório)') ||
          Account.create!(name: 'Central de Atendimento STJ (laboratório)', locale: 'pt_BR')
AccountUser.find_or_create_by!(account_id: account.id, user_id: user.id) { |au| au.role = :administrator }

inbox = account.inboxes.find_by(name: 'Chat on-line')
unless inbox
  canal = Channel::WebWidget.create!(account: account, website_url: ENV.fetch('PUB_PAINEL', 'http://localhost:8080'),
                                     widget_color: '#9E8954',
                                     welcome_title: 'Atendimento ao usuário',
                                     welcome_tagline: 'Assistente virtual do laboratório. Dados fictícios.')
  inbox = Inbox.create!(account: account, channel: canal, name: 'Chat on-line')
end
InboxMember.find_or_create_by!(user_id: user.id, inbox_id: inbox.id)

bot = AgentBot.find_by(name: 'Lia', account_id: account.id) ||
      AgentBot.create!(name: 'Lia', description: 'Assistente virtual (Dify)', outgoing_url: BOT_URL, account: account)
bot.update!(outgoing_url: BOT_URL) if bot.outgoing_url != BOT_URL
AgentBotInbox.find_or_create_by!(inbox_id: inbox.id, agent_bot_id: bot.id)

# Sem a tela de "primeira instalação": a conta já está pronta
::Redis::Alfred.delete(::Redis::Alfred::CHATWOOT_INSTALLATION_ONBOARDING)

dados = {
  account_id: account.id,
  bot_token: bot.access_token.token,
  website_token: inbox.channel.website_token,
  login: EMAIL,
  senha: SENHA
}
File.write('/kit/config/chatwoot.json', JSON.pretty_generate(dados))
puts "KIT: Chatwoot pronto (conta #{account.id}, caixa #{inbox.id}, bot #{bot.id})"

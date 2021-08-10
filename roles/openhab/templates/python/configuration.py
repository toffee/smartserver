# -*- coding: utf-8 -*-
LOG_PREFIX = "jsr223.jython"

allTelegramBots = [
{% for bot_name in vault_telegram_bots %}
  {% if loop.index > 1 %},{% endif %}"{{bot_name}}"
{% endfor %}
]

allTelegramAdminBots = [
{% for username in userdata %}{% if 'admin' in userdata[username].groups and userdata[username].telegram_bot is defined %}
  {% if loop.index > 1 %},{% endif %}"{{userdata[username].telegram_bot}}"
{% endif %}{% endfor %}
]

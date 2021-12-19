<Location />
  RewriteCond %{HTTP:Upgrade} =websocket [NC]
  RewriteRule /api(.*) ws://zigbee2mqtt:8084/api$1 [P,L]

  ProxyPreserveHost On
  ProxyPass http://zigbee2mqtt:8084/
  ProxyPassReverse http://zigbee2mqtt:8084/
</Location>


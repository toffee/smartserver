ProxyRequests Off
ProxyPreserveHost On

# HSTS (mod_headers is required) (15768000 seconds = 6 months)
Header always set Strict-Transport-Security "max-age=15768000"

AllowEncodedSlashes NoDecode

<Location />
  ProxyPass https://unifi:8443/
  ProxyPassReverse https://unifi:8443/
</Location>

<Location /wss/>
  ProxyPass wss://unifi:8443/wss/
  ProxyPassReverse wss://unifi:8443/wss/
</Location>

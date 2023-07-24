<Location />
  ProxyPass http://unifi:28443/
  ProxyPassReverse http://unifi:28443/

  RequestHeader set "X-Forwarded-Proto" expr=%{REQUEST_SCHEME}
  RequestHeader set "X-Forwarded-SSL" expr=%{HTTPS}
</Location>


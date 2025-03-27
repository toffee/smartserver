<Location />
  ProxyPass http://127.0.0.1:5000/
  ProxyPassReverse http://127.0.0.1:5000/

  RequestHeader set "X-Forwarded-Proto" expr=%{REQUEST_SCHEME}
</Location>


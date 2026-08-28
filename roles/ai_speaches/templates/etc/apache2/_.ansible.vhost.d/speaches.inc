<Location />
  ProxyPass http://speaches:8000/
  ProxyPassReverse http://speaches:8000/

  RequestHeader set "X-Forwarded-Proto" expr=%{REQUEST_SCHEME}
  RequestHeader set "X-Forwarded-SSL" expr=%{HTTPS}
</Location>


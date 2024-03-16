<Location />
  ProxyPass http://fireflyiii:8080/
  ProxyPassReverse http://fireflyiii:8080/
        
  RequestHeader set X-Forwarded-Proto expr=%{REQUEST_SCHEME}
  RequestHeader set X-Forwarded-SSL expr=%{HTTPS}
</Location>

#This does not work. Redirects to http://fireflyiii-importer:8080/token
<Location /importer>
  ProxyAddHeaders Off
  RequestHeader unset Accept-Encoding
  ProxyPass http://fireflyiii-importer:8080
  ProxyPassReverse http://fireflyiii-importer:8080
  AddOutputFilterByType SUBSTITUTE text/html
  Substitute "s|http://fireflyiii-importer:8080/|https://fireflyiii.{{server_domain}}/importer/|i"
</Location>

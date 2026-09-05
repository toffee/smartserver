<Location />
    ProxyPass http://fireflyiii-importer-calminia:8080/
    ProxyPassReverse http://fireflyiii-importer-calminia:8080/
    
    RequestHeader set X-Forwarded-Proto expr=%{REQUEST_SCHEME}
    RequestHeader set X-Forwarded-SSL expr=%{HTTPS}
</Location>
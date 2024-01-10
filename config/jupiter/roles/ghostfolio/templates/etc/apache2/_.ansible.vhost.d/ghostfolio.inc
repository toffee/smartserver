<LocationMatch "/assets/site.webmanifest">
  <RequireAny>
    Require all granted
  </RequireAny>
</LocationMatch>

<Location />
  ProxyPass http://ghostfolio:3333/
  ProxyPassReverse http://ghostfolio:3333/
</Location>
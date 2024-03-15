DocumentRoot "{{htdocs_path}}kintsugi"

Options +MultiViews	

<Location /dev/>
  ProxyPass http://jekyll-serve:4000/dev/
  ProxyPassReverse http://jekyll-serve:4000/dev/
</Location>
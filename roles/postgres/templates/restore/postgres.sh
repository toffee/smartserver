#!/usr/bin/bash

FILE=`ls -td ./postgres/{{database}}* 2>/dev/null | head -n 1`

read -r -p "Are you sure to import '$FILE' into postgresql database '{{database}}'? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
then
    bzcat $FILE | docker exec -i postgres sh -c "psql {{database}}"
{% if backup_cleanup is defined %}
    {{backup_cleanup}}
{% endif %}
fi

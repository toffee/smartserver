#!/usr/bin/bash

FOLDER=`ls -td ./influxdb/{{database}}* 2>/dev/null | head -n 1`
FOLDER_NAME="$(basename -- $FOLDER)"

read -r -p "Are you sure to import '$FOLDER' into influxdb database '{{database}}'? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
then
    podman exec influxdb influxd restore --bucket {{database}} --org default-org /var/lib/influxdb/data /var/lib/influxdb_backup/$FOLDER_NAME
fi

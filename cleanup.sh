#!/bin/bash

#systemctl stop unifi.service
systemctl stop zigbee2mqtt.service
systemctl stop vcontrold.service
systemctl stop php.service
systemctl stop redis.service
systemctl stop prometheus.service
systemctl stop loki.service
systemctl stop onlyoffice.service
systemctl stop grafana.service
systemctl stop librenms.service
systemctl stop fluentd.service
systemctl stop alertmanager.service
systemctl stop postfix.service
#systemctl stop pihole.service
systemctl stop mytracker.service
#systemctl stop minidlna.service
systemctl stop openhab.service
systemctl stop system_service.service
systemctl stop apache2.service
#systemctl stop telegraf.service
systemctl stop mysql.service
systemctl stop vsftpd.service
systemctl stop samba.service
systemctl stop wireguard_mobile.service
systemctl stop named.service
systemctl stop influxdb.service
systemctl stop mosquitto.service
#systemctl stop device_ping.service
systemctl stop speedtest.service

docker container prune
docker network prune
docker image prune -a
FROM openhab/openhab:{{openhab_version}}-debian

RUN apt-get update && \
  apt-get install -y ffmpeg

COPY init.sh /etc/cont-init.d/

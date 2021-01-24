FROM openhab/openhab:{{image_version}}-debian

RUN apt-get update && apt-get install iputils-ping && apt-get -y install ffmpeg

COPY init.sh /etc/cont-init.d/

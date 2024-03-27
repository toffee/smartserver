FROM postgres:{{image_version}}

USER root

RUN apk --no-cache add shadow

RUN groupmod -g {{system_groups['postgres'].id}} postgres && \
    usermod -u {{system_users['postgres'].id}} -g {{system_groups['postgres'].id}} postgres && \
    chown -R postgres:postgres /var/lib/postgresql/


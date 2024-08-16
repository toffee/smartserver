#!/bin/sh

exitcode=1
watched_pids=""

{% if entrypoint_pre is defined %}
{{entrypoint_pre}}
{% endif %}
ignore()
{
    echo "Entrypoint - Ignoring SIGHUP"
}

trap "ignore" SIGHUP

stop()
{
    echo "Entrypoint - Shutting down service"

    exitcode=0

{% if entrypoint_shutdown is defined %}{% for cmdline in entrypoint_shutdown %}
    {{ cmdline }}
{% endfor %}{% endif %}

    if [ ! -z "$watched_pids" ]; then
        echo "Entrypoint - Send 'TERM' to pid(s) '$watched_pids'"
        kill -s TERM $watched_pids

        # No need to wait. Otherwise "Terminated" log message will occur in journald
        #echo "Entrypoint - Wait for pid(s) '$watched_pids'"
        #wait $watched_pids
    fi

    #echo "Entrypoint - Exit $exitcode"
    #exit $exitcode
}

trap "stop" SIGTERM SIGINT

start()
{
    echo "Entrypoint - Starting service"
{% for cmdline in entrypoint_startup %}
    {{ cmdline }}
{% if cmdline[-2:] == ' &' %}
    PID=$!
    watched_pids="$watched_pids $PID"
{% endif %}
{% endfor %}

    if [ ! -z "$watched_pids" ]; then
        watched_pids=$(echo $watched_pids | xargs)
        echo "Entrypoint - Service started with pid(s) '$watched_pids'"
    else
        echo "Entrypoint - Service started"
    fi
}

start

{% if entrypoint_check is defined %}
    {{entrypoint_check}}
{% else %}
if [ ! -z "$watched_pids" ]; then
    echo "Entrypoint - Observe pid(s) '$watched_pids'"

    IFS=' '
    CMD=""
    for pid in $watched_pids
    do
        if [ ! -z "$CMD" ]; then
            CMD="$CMD &&"
        fi
        CMD="$CMD test -d /proc/$pid/"
    done

    #echo "Entrypoint - CMD: '$CMD'"
    while eval "$CMD"; do sleep 1 & wait; done
    #while true; do wait $watched_pids; break; done
fi
{% endif %}

if [ $exitcode -ne 0 ]; then
    echo "Entrypoint - Unexpected interruption with code '$exitcode'"
else
    echo "Entrypoint - Stopped with code '$exitcode'"
fi

exit $exitcode

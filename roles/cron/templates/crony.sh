#!/bin/bash

set -eu

script_name=$(basename "$0")

IFS='|' read -r journal_type name command <<< "$@"
journal_type="$(echo -e "${journal_type}" | sed -e 's/^[[:space:]]*//' | sed -e 's/[[:space:]]*$//' )"
name="$(echo -e "${name}" | sed -e 's/^[[:space:]]*//' | sed -e 's/[[:space:]]*$//')"
command="$(echo -e "${command}" | sed -e 's/^[[:space:]]*//' | sed -e 's/[[:space:]]*$//')"

# xargs does not work, becazse it is cleaning/modifing '"' inside the command
#journal_type="$(echo -e "${journal_type}" | xargs)"
#name="$(echo -e "${name}" | xargs)"
#command="$(echo -e "${command}" | xargs)"

# CHECK for still running jobs
result=$(pgrep -f "${script_name} ${journal_type} \\| ${name}");

#echo $result
#echo "pgrep -f \"${script_name} ${journal_type} | ${name}\""
#pgrep -f "${script_name} ${journal_type} \\| ${name}"

instances="$(wc -l <<< \"$result\")"

if [ "$instances" -gt "1" ]; then
    #pgrep -af "${script_name} ${journal_type} | ${name}"
    echo "CRON '$name' still running"  | systemd-cat -t $journal_type -p 4;
    exit
fi

#echo "$@";
#echo ":$name:";
#echo ":$command:";
#echo ":$journal_type:";

#exec > >(systemd-cat -t "$(realpath "$0")" -p info ) 2> >(systemd-cat -t "$(realpath "$0")" -p err )
#echo "stdbuf -i0 -o0 -e0 $command > >(systemd-cat -t $journal_type -p 6) 2> >(systemd-cat -t $journal_type -p 3)"

started=`date '+%Y-%m-%d %H:%M:%S'`

set +e
eval "$command" > >(systemd-cat -t $journal_type -p 6) 2> >(systemd-cat -t $journal_type -p 3)
RESULT=$?
set -e

if [ $RESULT -ne 0 ]
then
    JSON=$(jq -c -n --arg job "$name" --arg code "$RESULT" --arg cmd "$command" --arg error_out "failed" '{"job":"\($job)","code":"\($code)","cmd":"\($cmd)","message":"\($error_out)"}');
    echo "$JSON"  | systemd-cat -t $journal_type -p 3

    # wait until all logs arrive in journald
    sleep 1

    finished=`date '+%d.%m.%Y %H:%M:%S'`
    LOGS=$(journalctl --since "$started" -t $journal_type | tail -n 50)

    SUBJECT="CRON '$name' failed at $finished"

    MESSAGE="COMMAND:\n$command"
    MESSAGE+="\n\nCODE:\n$RESULT"

    MESSAGE+="\n\nLOGS:\n$LOGS"

    echo -e "$MESSAGE" | mail -s "$SUBJECT" root
#else
#    JSON=$(jq -c -n --arg job "$name" --arg code "$RESULT" --arg cmd "$command" --arg error_out "failed" '{"job":"\($job)","code":"\($code)","cmd":"\($cmd)","message":"\($error_out)"}');
#    echo "$JSON"  | systemd-cat -t $journal_type -p 6
fi

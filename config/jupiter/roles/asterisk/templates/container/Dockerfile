FROM alpine:{{image_version}}

RUN apk update && \
    apk --no-cache add tzdata && \
    apk --no-cache add asterisk
    
# -T    Display the time in [Mmm dd hh:mm:ss] format for each line of output to the CLI
# -W    Adjust terminal colors to compensate for a light background
# -p    Run as pseudo-realtime thread
# -v    Increase verbosity (multiple v's = more verbose)
# -d    Increase debugging (multiple d's = more debugging)
# -f    Do not fork
ENTRYPOINT ["/usr/sbin/asterisk", "-T", "-W", "-p", "-vvvdddf"]

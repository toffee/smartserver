FROM alpine:{{alpine_version}}

RUN apk --no-cache add git sqlite python3 python3-dev py3-pip tzdata 

RUN mkdir /mytracker && \
    git clone --single-branch --branch master https://github.com/toffee/MySensorsTracker.git /mytracker && \
    cd /mytracker && \
    pip3 install peewee flask wtforms paho-mqtt && \
    pip install WTForms==2.3.3 
    
#ENTRYPOINT ["/bin/sleep","3000000"]
ENTRYPOINT ["/usr/bin/python3","/mytracker/app.py"]


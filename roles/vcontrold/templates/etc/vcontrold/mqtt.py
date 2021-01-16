import subprocess
import signal
import sys
from datetime import datetime
import time
import paho.mqtt.client as mqtt
import telnetlib
import re

class Handler(object):
    '''Handler client'''
    def __init__(self):
        self.terminated = False
        self.process = None
        self.telnet_client = None
        self.mqtt_client = None
        self.lastPublishTime = datetime.now()

        #self.cmds = ['getTempAussen', 'getTempAussenGedaempft', 'getTempVorlaufSoll','getTempVorlauf','getTempKesselSoll','getTempKessel','getHeizkreisPumpeDrehzahl','getBrennerStarts','getBrennerStunden','getTempWasserSpeicher','getTempSolarKollektor','getSolarStunden','getTempSolarSpeicher','getSolarLeistung','getSammelstoerung','getLeistungIst','getBetriebsart','getTempRaumSoll','getSolarPumpeStatus','getNachladeunterdrueckungStatus']
        #commands with original vito.xml
        self.cmds = ['getTempA', 'getTempAtp', 'getTempAged', 'getTempAussen', 'getTempAussenGedaempft', 'getTempVorlaufSoll','getTempVorlauf','getTempKesselSoll','getTempKessel','getHeizkreisPumpeDrehzahl','getBrennerStarts','getBrennerStunden','getTempWasserSpeicher','getSammelstoerung','getLeistungIst', 'getTempRL17A', 'getNeigungM1', 'getNiveauM1', 'getTempRaumNorSollM1', 'getTempRaumRedSollM1', 'getBetriebArt']
        #commands with github vito.xml
        #self.cmds = ['getTempAtp', 'getTempAged', 'getTempVLsollM1','getTempVListM1','getTempKsoll','getTempKtp','getPumpeStatusM1','getBrennerStarts','getBrennerStunden1','getTempStp','getStatusStoerung','getLeistungIst','getBetriebArt','getTempRaumNorSollM1','getSolarStatusWW','getTempRL17A']
        
        self.writeCmds = ['setNeigungM1', 'setNiveauM1', 'setTempRaumNorSollM1', 'setTempRaumRedSollM1', 'setBetriebArt']

    def startDaemon(self):
        print("Start vcontrold ...", end='', flush=True)
        self.process = subprocess.Popen(['/usr/sbin/vcontrold', '-n'], stdout=subprocess.PIPE, universal_newlines=True)
        time.sleep(1)
        if self.damonIsAlive():
            print(" successful", flush=True)
        else:
            print(" failed", flush=True)
            raise Exception("Vcontrold not started") 
          
    def connectDaemon(self):
        retryCount = 0
        while retryCount <= 5:
            try:
                print("Connection to vcontrold ...", end='', flush=True)
                self.telnet_client = telnetlib.Telnet("localhost", "3002")
                print(" initialized", flush=True)

                out = self.telnet_client.read_until(b"vctrld>",10)
                if len(out) == 0:
                    raise Exception("Vcontrold not readable") 
                  
                print("Connection to vcontrold successful", flush=True)
                break
            except:
                if self.telnet_client != None:
                    self.telnet_client.close()

                print("Connection to vcontrold failed", flush=True)

                retryCount = retryCount + 1
                time.sleep(1)
                #raise Exception("Vcontrold not running") 
          
    def connectMqtt(self):
        print("Connection to mqtt ...", end='', flush=True)
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
        self.mqtt_client.on_disconnect = lambda client, userdata, rc: self.on_disconnect(client, userdata, rc)
        self.mqtt_client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg) 
        self.mqtt_client.connect("mosquitto", 1883, 60)
        print(" initialized", flush=True)
        
        self.mqtt_client.loop_start()
          
    def loop(self):
        dateTime = datetime.now()
        if dateTime.second == 0 or (dateTime - self.lastPublishTime).total_seconds() >= 60 :
            self.lastPublishTime = dateTime
            self.publish()
        else:
            time.sleep(60-(dateTime - self.lastPublishTime).total_seconds())

    def on_connect(self,client,userdata,flags,rc):
        print("Connected to mqtt with result code:"+str(rc), flush=True)
        if rc == 0:
            # subscribe for all devices of user
            #client.subscribe('+/vcontrol/setBetriebsartTo')
            for i, entry in enumerate(self.writeCmds):
                client.subscribe("+/vcontrol/{}".format(entry))
        
    def on_disconnect(self,client, userdata, rc):
        print("Disconnect from mqtt with result code:"+str(rc), flush=True)

    def on_message(self,client,userdata,msg):
        if not self.damonIsAlive():
            raise Exception("Vcontrold died") 
        
        print("Topic " + msg.topic + ", message:" + str(msg.payload), flush=True)
        # Topic /vcontrol/setTempRaumRedSollM1, message:b'4'
        vcommand = msg.topic[len("/vcontrol/"):]
        #print("Write command " + vcommand, flush=True)
        #cmd = "setBetriebsartTo{}".format(int(float(msg.payload.decode("ascii"))))
        cmd = vcommand + " {}".format(msg.payload.decode("ascii"))
        #print("Sent command " + cmd, flush=True)
        self.telnet_client.write(cmd.encode('ascii') + b"\n")
        out = self.telnet_client.read_until(b"vctrld>",10)
        if len(out) == 0:
            print("Set '" + cmd + "' not successful", flush=True, file=sys.stderr)
        else:
            print("Set '" + cmd + "' successful", flush=True)
        
    def publish(self):
        if not self.damonIsAlive():
            raise Exception("Vcontrold died") 
          
        print("Publish values to mqtt ...", end='', flush=True)
        try:
            for cmd in self.cmds:
                self.telnet_client.write(cmd.encode('ascii') + b"\n")
                out = self.telnet_client.read_until(b"vctrld>",10)
                #print("OUT " + out.decode("ascii"), flush=True)
                if len(out) == 0:
                    print(" failed with empty result", flush=True, file=sys.stderr)
                    return
                else:
                    search = re.search(r'[-]?[0-9]*\.?[0-9]+', out.decode("ascii"))
                    if search == None:
                        self.mqtt_client.publish('/vcontrol/getSammelstoerung', payload=999, qos=0, retain=False)
                        print(out.decode("ascii"), flush=True, file=sys.stderr)
                    else:
                        self.mqtt_client.publish('/vcontrol/' + cmd, payload=round(float(search.group(0)),2), qos=0, retain=False)                            
            print(" successful", flush=True)
        except Exception as e:
            print(" failed", flush=True)
            print(str(e), flush=True, file=sys.stderr)
          
    def terminate(self):
        if self.process != None:
            if self.damonIsAlive():
                print("Shutdown vcontrold", flush=True)
                self.process.terminate()
            self.process = None
      
        if self.telnet_client != None:
            print("Close connection to vcontrold", flush=True)
            self.telnet_client.close()
            self.telnet_client = None
            
            print("Close connection to mqtt", flush=True)
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.mqtt_client = None
            
        self.terminated = True
        
    def isTerminated(self):
        return self.terminated
      
    def damonIsAlive(self):
        return self.process.poll() == None
      
    def canRetry(self,e):
        self.retryCount = self.retryCount + 1
        if self.retryCount > 10 or not self.damonIsAlive():
            print(str(e), flush=True, file=sys.stderr)
            return False
        elif not handler.isTerminated():
            print("Retry: {}".format(str(e)), flush=True)
            return True
      
handler = Handler()
def cleanup(signum, frame):
    #print(signum)
    #print(frame)
    print("Shutdown vclient", flush=True)
    handler.terminate()
    exit(0)

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

try:
    handler.startDaemon()

    handler.connectMqtt()

    handler.connectDaemon()
except Exception as e:
    print(str(e), flush=True, file=sys.stderr)
    exit(1)
        
print("Start event loop", flush=True)
while not handler.isTerminated():          
    handler.loop()   
print("End event loop", flush=True)

if not handler.isTerminated():
    print("Shutdown handler", flush=True)
    handler.terminate()
    exit(1)
else:
    exit(0)

from hcnetsdk import HCNetSDK, NET_DVR_DEVICEINFO_V30, NET_DVR_DEVICEINFO_V30, NET_DVR_SETUPALARM_PARAM, fMessageCallBack, COMM_ALARM_V30, COMM_ALARM_VIDEO_INTERCOM, NET_DVR_VIDEO_INTERCOM_ALARM, NET_DVR_ALARMINFO_V30, ALARMINFO_V30_ALARMTYPE_MOTION_DETECTION, VIDEO_INTERCOM_ALARM_ALARMTYPE_DOORBELL_RINGING, VIDEO_INTERCOM_ALARM_ALARMTYPE_DISMISS_INCOMING_CALL, VIDEO_INTERCOM_ALARM_ALARMTYPE_TAMPERING_ALARM, VIDEO_INTERCOM_ALARM_ALARMTYPE_DOOR_NOT_CLOSED, COMM_UPLOAD_VIDEO_INTERCOM_EVENT, NET_DVR_VIDEO_INTERCOM_EVENT, VIDEO_INTERCOM_EVENT_EVENTTYPE_UNLOCK_LOG, VIDEO_INTERCOM_EVENT_EVENTTYPE_ILLEGAL_CARD_SWIPING_EVENT, NET_DVR_UNLOCK_RECORD_INFO
from ctypes import POINTER, cast, c_char_p, c_byte

import paho.mqtt.client as mqtt
import time

import logging
from systemd.journal import JournalHandler

log = logging.getLogger('hikvision')
log.addHandler(JournalHandler())
log.setLevel(logging.INFO)
log.info("Start hik.py")

#put your own values here
broker = 'mosquitto'    #ip of mqtt broker

def broker_on_connect(client, userdata, flags, rc):
    global log 
    log.info("Broker Connected with result code " + str(rc))
   
def broker_on_message(mosq, obj, msg):
    pass
    
def broker_on_publish(mosq, obj, mid):
    global log
    log.info("Broker received message " + str(mid))

def broker_on_subscribe(mosq, obj, mid, granted_qos):
    global log
    log.info("Broker Subscribed: %s %s" % (str(mid), str(granted_qos)))

def broker_on_disconnect(mosq, obj, rc):
    global log
    log.info("Broker disconnected")

def broker_on_log(mosq, obj, level, string):
    global log
    log.info(string)

mqttc = None

#connect to broker
mqttc = mqtt.Client()
#Assign event callbacks
mqttc.on_message = broker_on_message
mqttc.on_connect = broker_on_connect
mqttc.on_disconnect = broker_on_disconnect
mqttc.on_publish = broker_on_publish
mqttc.on_subscribe = broker_on_subscribe

try:
    #mqttc.username_pw_set(user, password)  #put your own mqtt user and password here if you are using them, otherwise comment out
    mqttc.connect(broker, 1883, 60) #Ping MQTT broker every 60 seconds if no data is published from this script.
    mqttc.loop_start()
except Exception as e:
    log.error("Unable to connect to MQTT Broker: %s" % e)
    mqttc = None
    exit(3)

def callback(command: int, alarmer_pointer, alarminfo_pointer, buffer_length, user_pointer):
    global log
    global mqttc
    
    if (command == COMM_ALARM_V30):
        alarminfo_alarm_v30: NET_DVR_ALARMINFO_V30 = cast(
            alarminfo_pointer, POINTER(NET_DVR_ALARMINFO_V30)).contents
        if (alarminfo_alarm_v30.dwAlarmType == ALARMINFO_V30_ALARMTYPE_MOTION_DETECTION):
            log.info(f"Motion detected")
        else:
            log.info(
                f"COMM_ALARM_V30, unhandled dwAlarmType: {alarminfo_alarm_v30.dwAlarmType}")
    elif(command == COMM_ALARM_VIDEO_INTERCOM):
        alarminfo_alarm_video_intercom: NET_DVR_VIDEO_INTERCOM_ALARM = cast(
            alarminfo_pointer, POINTER(NET_DVR_VIDEO_INTERCOM_ALARM)).contents        
        if (alarminfo_alarm_video_intercom.byAlarmType == VIDEO_INTERCOM_ALARM_ALARMTYPE_DOORBELL_RINGING):
            log.info("Doorbell ringing")
            mqttc.publish("hikvision/ringing", "ON")
        elif (alarminfo_alarm_video_intercom.byAlarmType == VIDEO_INTERCOM_ALARM_ALARMTYPE_DISMISS_INCOMING_CALL):
            log.info("Call dismissed")
            mqttc.publish("hikvision/ringing", "OFF")
        elif (alarminfo_alarm_video_intercom.byAlarmType == VIDEO_INTERCOM_ALARM_ALARMTYPE_TAMPERING_ALARM):
            log.info("Tampering alarm")
        elif (alarminfo_alarm_video_intercom.byAlarmType == VIDEO_INTERCOM_ALARM_ALARMTYPE_DOOR_NOT_CLOSED):
            log.info("Door not closed")
        else:
            log.info(
                f"COMM_ALARM_VIDEO_INTERCOM, unhandled byAlarmType: {alarminfo_alarm_video_intercom.byAlarmType}")
    elif(command == COMM_UPLOAD_VIDEO_INTERCOM_EVENT):
        alarminfo_upload_video_intercom_event: NET_DVR_VIDEO_INTERCOM_EVENT = cast(
            alarminfo_pointer, POINTER(NET_DVR_VIDEO_INTERCOM_EVENT)).contents
        if (alarminfo_upload_video_intercom_event.byEventType == VIDEO_INTERCOM_EVENT_EVENTTYPE_UNLOCK_LOG):
            ascii = list(alarminfo_upload_video_intercom_event.uEventInfo.struUnlockRecord.byControlSrc)
            ascii = ascii[0:ascii.index(0)]
            text = ''.join(chr(i) for i in ascii)
            log.info(f"Unlocked by: {list(alarminfo_upload_video_intercom_event.uEventInfo.struUnlockRecord.byControlSrc)}")
            log.info("Unlocked by: {}".format(text))
            mqttc.publish("hikvision/unlock", text)
        elif (alarminfo_upload_video_intercom_event.byEventType == VIDEO_INTERCOM_EVENT_EVENTTYPE_ILLEGAL_CARD_SWIPING_EVENT):
            log.info(f"Illegal card swiping")
        else:
            log.info(
                f"COMM_ALARM_VIDEO_INTERCOM, unhandled byEventType: {alarminfo_upload_video_intercom_event.byEventType}")
    else:
        log.info(f"Unhandled command: {command}")


HCNetSDK.NET_DVR_Init()
HCNetSDK.NET_DVR_SetValidIP(0, True)

device_info = NET_DVR_DEVICEINFO_V30()

user_id = HCNetSDK.NET_DVR_Login_V30("{{camera_09_ip}}".encode('utf-8'), 8000, "{{vault_camera_09_username}}".encode('utf-8'), "{{vault_camera_09_password}}".encode('utf-8'), device_info)

if (user_id < 0):
    log.error(
        f"NET_DVR_Login_V30 failed, error code = {HCNetSDK.NET_DVR_GetLastError()}")
    HCNetSDK.NET_DVR_Cleanup()
    exit(1)

alarm_param = NET_DVR_SETUPALARM_PARAM()
alarm_param.dwSize = 20
alarm_param.byLevel = 1
alarm_param.byAlarmInfoType = 1
alarm_param.byFaceAlarmDetection = 1

alarm_handle = HCNetSDK.NET_DVR_SetupAlarmChan_V41(user_id, alarm_param)

if (alarm_handle < 0):
    log.error(
        f"NET_DVR_SetupAlarmChan_V41 failed, error code = {HCNetSDK.NET_DVR_GetLastError()}")
    HCNetSDK.NET_DVR_Logout_V30(user_id)
    HCNetSDK.NET_DVR_Cleanup()
    exit(2)

message_callback = fMessageCallBack(callback)
HCNetSDK.NET_DVR_SetDVRMessageCallBack_V50(0, message_callback, user_id)

try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    log.info("Application interrupted...")

HCNetSDK.NET_DVR_CloseAlarmChan_V30(alarm_handle)
HCNetSDK.NET_DVR_Logout_V30(user_id)
HCNetSDK.NET_DVR_Cleanup()

mqttc.loop_stop()

log.info("Stop hik.py")

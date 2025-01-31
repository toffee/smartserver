# serial ports +++++++++++++++++++
port_vitoconnect = None  # '/dev/ttyS0'  older Pi:'/dev/ttyAMA0'  {optional} set None if no Vitoconnect
port_optolink = '/dev/ttyOptolink'   # '/dev/ttyUSB0'  {mandatory}

vs2timeout = 120                 # seconds to detect VS2 protocol on vitoconnect connection


# MQTT +++++++++++++++++++
mqtt = "mosquitto:1883"          # e.g. "192.168.0.123:1883"; set None to disable MQTT
mqtt_user = None                 # "<user>:<pwd>"; set None for anonymous connect
mqtt_topic = "vcontrol"          # "optolink"
mqtt_fstr = "{dpname}"           # "{dpaddr:04X}_{dpname}"
mqtt_listen = "vcontrol/cmnd"    # "optolink/cmnd"; set None to disable listening
mqtt_respond = "vcontrol/resp"   # "optolink/resp"


# TCP/IP +++++++++++++++++++
tcpip_port = None         # e.g. 65234 is used by Viessdataby default; set None to disable TCP/IP


# full raw timing
fullraw_eot_time = 0.05    # seconds. time no receive to decide end of telegram
fullraw_timeout = 2        # seconds. timeout, return in any case
olbreath = 0.1             # seconds of sleep after request-response cycle

# logging, info +++++++++++++++++++
log_vitoconnect = False    # logs communication with Vitoconnect (rx+tx telegrams)
show_opto_rx = False        # display on screen (no output when ran as service)

# format +++++++++++++++++++
max_decimals = 1
data_hex_format = '02x'    # set to '02X' for capitals
resp_addr_format = '04x'     # format of DP address in MQTT/TCPIP request response; e.g. 'd': decimal, '04X': hex 4 digits

# Viessdata utils +++++++++++++++++++
write_viessdata_csv = False
viessdata_csv_path = ""
buffer_to_write = 60
dec_separator = ","

# 1-wire sensors +++++++++++++++++++
w1sensors = {}


# polling datapoints +++++++++++++++++++
poll_interval = 60      # seconds. 0 for continuous, set -1 to disable Polling
poll_items = [
    # ([PollCycle,] Name, DpAddr, Len, Scale/Type, Signed)
    # Überblick - Warmwasser | Overview - DHW
    ("WW_Status_NR1~0x650A", 0x650A, 1),
    ("TiefpassTemperaturwertWW1~0x0812", 0x0812, 2, 0.1),
    ("TiefpassTemperaturwerWW2~0x0814", 0x0814, 2, 0.1),
    ("Speicherladepumpe~0x6513", 0x6513, 1),
    ("Zirkulationspumpe~0x6515", 0x6515, 1),
    ("WW_Einmalladung~0x65F5", 0x65F5, 1),
    # Bedienung - Betriebsdaten A1 | Service - Operating data A1
    ("Bedien_WW_Solltemperatur_60~0x6300", 0x6300, 1, 1),
    # Bedienung - Warmwasser A1
    # ("Schaltzeiten_A1M1_WW", 0x????, 56),    
    # Inbetriebnahme - Warmwasser | Commissioning
    ("K67_KonfiWW_Soll3~0x6767", 0x6767, 1),
    ("K73_KonfiZpumpeIntervallFreigabe~0x6773", 0x6773, 1), #0,1,2,3,4,5,6,7	0 Schaltuhr,1 pro Stunde,2 pro Stunde,3 pro Stunde,4 pro Stunde,5 pro Stunde,6 pro Stunde,EIN
    
    ("getTempA", 0x0800, 2, 0.1, True),
    ("getTempAussen", 0x5525, 2, 0.1, True),
    ("getTempAussenGedaempft", 0x5527, 2, 0.1, True),
    ("getTempVorlaufSoll", 0x2544, 2, 0.1, True),
    ("getTempVorlauf", 0x2900, 2, 0.1, True),
    ("getTempKesselSoll", 0x555A, 2, 0.1, True),
    ("getTempKessel", 0x0810, 2, 0.1, True),
    ("getHeizkreisPumpeDrehzahl", 0x7663, 1, 1),
    ("getBrennerStarts", 0x088A, 4, 1),
    ("getBrennerStunden", 0x08A7, 4, 0.000277777777778),
    ("getTempWasserSpeicher", 0x0812, 2, 0.1, True),
    ("getSammelstoerung", 0x0A82, 1),
    ("getLeistungIst", 0xA38F, 1, 1),
    ("getTempRL17A", 0x0808, 2, 0.1, True),
    ("getNeigungM1", 0x27D3, 1, 0.1),
    ("getNiveauM1", 0x27D4, 1, 1),
    ("getTempRaumNorSollM1", 0x2306, 1, 1),
    ("getTempRaumRedSollM1", 0x2307, 1, 1),
    ("getBetriebArt", 0x2323, 1, 1), #0,1,2,3,4	Abschalt,Nur WW,Heizen + WW,Dauernd Reduziert,Dauernd Normal
    ("getTempWWist", 0x0804, 2, 0.1, True),
    ("getTempWWsoll", 0x6300, 1, 1),
    ("dhwPreparationStatus", 0x650A, 1, 1),
    ("dhwOneTimeCharge", 0x65F5, 1, 1),
]


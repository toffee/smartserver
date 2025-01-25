'''
   Copyright 2024 philippoo66
   
   Licensed under the GNU GENERAL PUBLIC LICENSE, Version 3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       https://www.gnu.org/licenses/gpl-3.0.html

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

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
tcpip_port = 65234         # e.g. 65234 is used by Viessdataby default; set None to disable TCP/IP


# full raw timing
fullraw_eot_time = 0.05    # seconds. time no receive to decide end of telegram 
fullraw_timeout = 2        # seconds. timeout, return in any case 

# logging, info +++++++++++++++++++
log_vitoconnect = False    # logs communication with Vitoconnect (rx+tx telegrams)
show_opto_rx = True        # display on screen (no output when ran as service)

# format +++++++++++++++++++
max_decimals = 4
data_hex_format = '02x'    # set to '02X' for capitals
resp_addr_format = '04x'     # format of DP address in MQTT/TCPIP request response; e.g. 'd': decimal, '04X': hex 4 digits

# Viessdata utils +++++++++++++++++++
write_viessdata_csv = False
viessdata_csv_path = ""
buffer_to_write = 60
dec_separator = ","

# 1-wire sensors +++++++++++++++++++
w1sensors = {}
#     # addr : ('<w1_folder/sn>', '<slave_type>'),
#     0xFFF4 : ('28-3ce1d4438fd4', 'ds18b20'),   # highest known Optolink addr is 0xff17
#     0xFFFd : ('28-3ce1d443a4ed', 'ds18b20'),
# }


# polling datapoints +++++++++++++++++++
poll_interval = 30      # seconds. 0 for continuous, set -1 to disable Polling
poll_items = [
    # (Name, DpAddr, Len, Scale/Type, Signed)
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
    ("getTempAtp", 0x5525, 2, 0.1, True),
    ("getTempAged", 0x5527, 2, 0.1, True),
    ("getTempAussen", 0x5525, 2, 0.1, True),
    ("getTempAussenGedaempft", 0x5527, 2, 0.1, True),
    ("getTempVorlaufSoll", 0x2544, 2, 0.1, True), 
    ("getTempVorlauf", 0x2900, 2, 0.1, True),
    ("getTempKesselSoll", 0x555A, 2, 0.1, True),
    ("getTempKessel", 0x0810, 2, 0.1, True),
    ("getHeizkreisPumpeDrehzahl", 0x7663, 1, 1),
    ("getBrennerStarts", 0x088A, 4, 1),
    ("getBrennerStunden", 0x08A7, 4, 1),
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
    
    # Tabelle fuer Vitocalxxx-G mit Vitotronic 200 (Typ WO1C) (ab 04/2012)
    # ("error", 0x0491, 1, 1, False),
    # ("outside_temperature", 0x0101, 2, 0.1, True),
    # ("hk1_mode", 0xB000, 1, 1, False),			# betriebsart bit 4,5,6,7 comfort  bit 1 spar bit 0
    # ("hk1_requested_temperature", 0xA406, 2, 0.01, False),
    # ("hk1_normal_temperature", 0x2000, 2, 0.1, False),
    # ("hk1_reduced_temperature", 0x2001, 2, 0.1, False),
    # ("hk1_party_temperature", 0x2022, 2, 0.1, False),
    # ("hk1_temperature", 0x0116, 2, 0.1, False),
    # ("hk1_pump", 0x048D, 1, 1, False),
    # ("hk1_supply_temperature", 0x010A, 2, 0.1, False),
    # ("hk1_supply_target_temperature", 0x1800, 2, 0.1, False),
    # ("hk2_mode", 0xB001, 1, 1, False),
    # ("hk2_requested_temperature", 0xA446, 2, 0.01, False),
    # ("hk2_normal_temperature", 0x3000, 2, 0.1, False),
    # ("hk2_reduced_temperature", 0x3001, 2, 0.1, False),
    # ("hk2_party_temperature", 0x3022, 2, 0.1, False),
    # ("hk2_temperature", 0x0117, 2, 0.1, False),
    # ("hk2_pump", 0x048E, 1, 1, False),
    # ("hk2_supply_temperature", 0x0114, 2, 0.1, False),
    # ("hk2_supply_target_temperature", 0x1801, 2, 0.1, False),
    # ("buffer_temperature", 0x010B, 2, 0.1, False),
    # ("nc_cooling", 0x0492, 1, 1, False),
    # ("primary_supply_temperature", 0xB400, 3, 'b:0:1', 0.1, True), # Datalänge 3,Byte 0-1 Temperatur, Byte 3 Sensorstatus: 0-OK, 6-Nicht vorhanden
    # ("primary_return_temperature", 0xB401, 3, 'b:0:1', 0.1, True),
    # ("secondary_supply_temperature", 0xB402, 3, 'b:0:1', 0.1, True),
    # ("secondary_return_temperature", 0xB403, 3, 'b:0:1', 0.1, True),
    # ("liquid_gas_temperature", 0xB404, 3, 'b:0:1', 0.1, True),
    # ("evaporation_temperature", 0xB407, 3, 'b:0:1', 0.1, True),
    # ("condensation_temperature", 0xB408, 3, 'b:0:1', 0.1, True),
    # ("suction_gas_temperature", 0xB409, 3, 'b:0:1', 0.1, True),
    # ("hot_gas_temperature", 0xB40A, 3, 'b:0:1', 0.1, True),
    # ("superheating_target", 0xB40B, 3, 'b:0:1', 0.1, True),
    # ("superheating", 0xB40D, 3, 'b:0:1', 0.1, True),
    # ("suction_gas_pressure", 0xB410, 3, 'b:0:1', 0.1, True),
    # ("hot_gas_pressure", 0xB411, 3, 'b:0:1', 0.1, True),
    # ("primary_pump", 0xB420, 2, 1, False),
    # ("secondary_pump", 0xB421, 2, 1, False),
    # ("compressor", 0xB423, 2, 1, False),
    # ("expansion_valve", 0xB424, 2, 1, False),
    # ("nc_supply_temperature", 0x0119, 2, 0.1, False),
    # ("nc_supply_target_temperature", 0x1804, 2, 0.1, False),
    # ("eheater_power", 0x1909, 1, 3000, False),
    # ("eheater_3_energy", 0x0588, 4,  0.0008333, False),
    # ("eheater_6_energy", 0x0589, 4,  0.0016667, False),
    # ("thermal_energy", 0x1640, 4, 0.1, False),
    # ("electrical_energy", 0x1660, 4, 0.1, False),
    # ("thermal_power", 0x16A0, 4, 1, False),
    # ("electrical_power", 0x16A4, 4, 1, False),
    # ("cop", 0x1680, 1, 0.1, False),


    # # Tabelle fuer eine Vitodens 300 B3HB
    # ("Anlagenzeit", 0x088E, 8, 'vdatetime'),
    # ("AussenTemp", 0x0800, 2, 0.1, True),
    # ("KesselTemp", 0x0802, 2, 0.1, False),
    # ("SpeicherTemp", 0x0804, 2, 0.1, False),
    # ("AbgasTemp", 0x0808, 2, 0.1, False),
    # ("AussenTemp_fltrd", 0x5525, 2, 0.1, True),
    # ("AussenTemp_dmpd", 0x5523, 2, 0.1, True),
    # ("AussenTemp_mixed", 0x5527, 2, 0.1, True),
    # ("Eingang STB-Stoerung", 0x0A82, 1, 1, False),
    # ("Brennerstoerung", 0x0884, 1, 1, False),
    # ("Fehlerstatus Brennersteuergeraet", 0x5738, 1, 1, False),
    # ("Brennerstarts", 0x088A, 4, 1, False),
    # ("Betriebsstunden", 0x08A7, 4, 2.7777778e-4, False),  # 1/3600
    # ("Stellung Umschaltventil", 0x0A10, 1, 1, False),
    # ("Ruecklauftemp_calcd", 0x0C20, 2, 0.01, False),
    # ("Pumpenleistung", 0x0A3C, 1, 1, False),
    # ("Volumenstrom", 0x0C24, 2, 0.1, False),  # eigentlich scale 1 aber für Viessdata Grafik
    # ("KesselTemp_soll", 0x555A, 2, 0.1, False),
    # ("BrennerLeistung", 0xA38F, 1, 0.5, False),
    # ("BrennerModulation", 0x55D3, 1, 1, False),
    # ("Status", 0xA152, 2, 1, False),
    # ("SpeicherTemp_soll_akt", 0x6500, 2, 0.1, False),
    # ("Speicherladepumpe", 0x6513, 1, 1, False),
    # ("Zirkulationspumpe", 0x6515, 2, 1, False),

    # # ByteBit filter examples
    # ("Frostgefahr, aktuelle RTS etc", 0x2500, 22, 'b:0:21::raw'),
    # ("Frostgefahr", 0x2500, 22, 'b:16:16::raw'),
    # ("RTS_akt", 0x2500, 22, 'b:12:13', 0.1, False),
    
    # # 1-wire
    # ("SpeicherTemp_oben", 0xFFFd),
    # ("RuecklaufTemp_Sensor", 0xFFF4),
]


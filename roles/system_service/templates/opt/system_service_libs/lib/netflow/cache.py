import queue
import threading
import logging
import traceback
import time
import socket

import requests
import json

import schedule
import os

class Cache(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)

        self.max_location_cache_age = 60 * 60 * 24 * 7
        self.max_hostname_cache_age = 60 * 60 * 24 * 1

        self.is_running = False

        self.queue = queue.Queue()

        self.counter_lock = threading.Lock()
        self.counter_values = {"location_fetch": 0, "location_cache": 0, "hostname_fetch": 0, "hostname_cache": 0}

        self.dump_path = "/var/lib/system_service/netflow_cache.json"

        self.ip2location_url = "http://ip-api.com/json/{}?fields=country,countryCode,city,status,message"
        #self.ip2location_url = "https://api.hostip.info/get_json.php?ip={}"
        self.ip2location_state = True
        self.ip2location_throttled_until = 0

        self.location_lock = threading.Lock()
        self.hostname_lock = threading.Lock()

        self.ip2location_map = {}
        self.hostname_map = {}

    def start(self):
        self.is_running = True
        schedule.every().day.at("01:00").do(self.dump)
        schedule.every().hour.at("00:00").do(self.cleanup)
        self.restore()
        super().start()

    def restore(self):
        try:
            if os.path.exists(self.dump_path):
                with open(self.dump_path) as f:
                    self.ip2location_map, self.hostname_map  = json.load(f)
                logging.info("{} locations and {} hostnames loaded".format(len(self.ip2location_map),len(self.hostname_map)))
                return
            else:
                logging.info("No locations or hostnames loaded [empty file]")
        except Exception:
            logging.info("No locations or hostnames loaded [invalid file]")

    def dump(self):
        with open(self.dump_path, 'w') as f:
            with self.location_lock and self.hostname_lock:
                json.dump( [ self.ip2location_map, self.hostname_map ], f, ensure_ascii=False)
                logging.info("{} locations and {} hostnames saved".format(len(self.ip2location_map),len(self.hostname_map)))

    def cleanup(self):
        _now = time.time()
        location_count = 0
        with self.location_lock:
            for _ip in list(self.ip2location_map.keys()):
                if _now - self.ip2location_map[_ip]["time"] > self.max_location_cache_age:
                    del self.ip2location_map[_ip]
                    location_count += 1

        hostname_count = 0
        with self.hostname_lock:
            for _ip in list(self.hostname_map.keys()):
                if _now - self.hostname_map[_ip]["time"] > self.max_hostname_cache_age:
                    del self.hostname_map[_ip]
                    hostname_count += 1
        logging.info("Cleanup {} locations and {} hostnames".format(location_count, hostname_count))

    def terminate(self):
        if self.is_running:
            self.dump()
        self.is_running = False

    def run(self):
        logging.info("Netflow cache started")
        try:
            while self.is_running:
                try:
                    type, ip = self.queue.get(timeout=0.5)
                    if type == "location":
                        self._resolveLocationData(ip)
                    elif type == "hostname":
                        self._resolveHostnameData(ip)
                except queue.Empty:
                    pass
            logging.info("Netflow cache stopped")
        except Exception:
            logging.error(traceback.format_exc())
            self.is_running = False

    def increaseStats(self, type):
        with self.counter_lock:
            self.counter_values[type] += 1

    def getCountStats(self):
        with self.counter_lock:
            counter_values = self.counter_values
            self.counter_values = {"location_fetch": 0, "location_cache": 0, "hostname_fetch": 0, "hostname_cache": 0}
        return counter_values

    def isRunning(self):
        return self.is_running

    def getState(self):
        return self.ip2location_state

    def getLocationSize(self):
        return len(self.ip2location_map)

    def getLocation(self, ip, threaded):
        _ip = ip.compressed
        location = self.ip2location_map.get(_ip, None)
        if location is not None:
            #print("cachedLocation {}".format(ip))
            self.increaseStats("location_cache")
        elif threaded:
            self.queue.put(["location", ip])
            return None
        else:
            location = self._resolveLocationData(ip)
            if location is None:
                location = self._getUnknownLocationData(None)

        return location["data"]

    def _getUnknownLocationData(self, _now):
        return { "data": { "country_name": "Unknown", "country_code": "xx", "city": "Unknown" }, "time": _now }

    def _getPrivateLocationData(self, _now):
        return { "data": { "country_name": "Private", "country_code": "xx", "city": "Private" }, "time": _now }

    def _resolveLocationData(self, ip):
        _now = time.time()
        if self.ip2location_throttled_until > 0:
            if _now < self.ip2location_throttled_until:
                return None
            else:
                logging.info("Resume from throttled requests")
                self.ip2location_throttled_until = 0

        _ip = ip.compressed
        location = self.ip2location_map.get(_ip, None)
        if location is None:
            if ip.is_private:
                self.increaseStats("location_cache")
                location = self._getPrivateLocationData(_now)
                with self.location_lock:
                    self.ip2location_map[_ip] = location
            else:
                try:
                    response = requests.get(self.ip2location_url.format(_ip))
                except:
                    logging.error("Error fetching ip {}".format(_ip))
                    logging.error(":{}:".format(response.content))
                    logging.error(traceback.format_exc())
                    return None

                if response.status_code == 429:
                    logging.info("Rate limit is reached. Throttle requests for next 15 seconds".format(_ip))
                    self.ip2location_throttled_until = _now + 15
                    return None
                elif response.status_code == 200:
                    self.increaseStats("location_fetch")
                    if len(response.content) > 0:
                        try:
                            data = json.loads(response.content)
                        except:
                            logging.error("Error parsing ip {}".format(_ip))
                            logging.error(":{}:".format(response.content))
                            logging.error(traceback.format_exc())
                            return None

                        if data["status"] == "success":
                            if data["country"] == "":
                                data["country"] = "Unknown"
                            if data["countryCode"] == "":
                                data["countryCode"] = "xx"
                            if data["city"] == "":
                                data["city"] = "Unknown"
                            location = { "data": {"country_name": data["country"].title().replace(" ","\\ ").replace(",","\\,"), "country_code": data["countryCode"].lower(), "city": data["city"].replace(" ","\\ ").replace(",","\\,") }, "time": _now }
                        elif data["status"] == "fail":
                            if "private" in data["message"] or "reserved" in data["message"]:
                                location = self._getPrivateLocationData(_now)
                            else:
                                logging.error("Unhandled result: {}".format(response.content))
                                return None
                        else:
                            logging.error("Unhandled result: {}".format(response.content))
                            return None

                        #if "Private" in data["country_name"]:
                        #    location = { "data": {"country_name": "Private", "country_code": "xx", "city": "Private" }, "time": _now }
                        #else:
                        #    if "Unknown" in data["country_name"]:
                        #        data["country_name"] = "Unknown"
                        #        data["country_code"] = "xx"
                        #        data["city"] = "Unknown"
                        #    location = { "data": {"country_name": data["country_name"].title().replace(" ","\\ ").replace(",","\\,"), "country_code": data["country_code"].lower(), "city": data["city"].replace(" ","\\ ").replace(",","\\,") }, "time": _now }
                    else:
                        location = self._getUnknownLocationData(_now)
                    with self.location_lock:
                        self.ip2location_map[_ip] = location
                    self.ip2location_state = True
                else:
                    self.ip2location_state = False
                    return None
        else:
            self.increaseStats("location_cache")

        return location

    def getHostnameSize(self):
        return len(self.hostname_map)

    def getHostname(self, ip, threaded):
        _ip = ip.compressed
        hostname = self.hostname_map.get(_ip, None)
        if hostname is not None:
            self.increaseStats("hostname_cache")
        elif threaded:
            self.queue.put(["hostname", ip])
            return None
        else:
            hostname = self._resolveHostnameData(ip)

        return hostname["data"]

    def _resolveHostnameData(self, ip):
        _ip = ip.compressed
        hostname = self.hostname_map.get(_ip, None)
        if hostname is None:
            self.increaseStats("hostname_fetch")
            _hostname = socket.getfqdn(_ip)
            if ip.is_private and _hostname != _ip:
                _hostname = _hostname.split('.', 1)[0]
            hostname = { "data": _hostname, "time": time.time() }
            with self.hostname_lock:
                self.hostname_map[_ip] = hostname
        else:
            self.increaseStats("hostname_cache")
        return hostname

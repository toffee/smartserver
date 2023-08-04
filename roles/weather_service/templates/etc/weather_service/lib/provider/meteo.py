import traceback

from datetime import datetime, timedelta
from pytz import timezone
import time
import threading
import logging
import schedule
import os

import requests
import urllib.parse
import json
import decimal

from smartserver.confighelper import ConfigHelper

from lib.db import DBException

# possible alternative => https://open-meteo.com/

# https://api.weather.mg/

token_url    = "https://auth.weather.mg/oauth/token"
current_url  = 'https://point-observation.weather.mg/observation/hourly?locatedAt={location}&observedPeriod={period}&fields={fields}&observedFrom={start}&observedUntil={end}';
current_fields = [
    "airTemperatureInCelsius", 
    "feelsLikeTemperatureInCelsius",
    "relativeHumidityInPercent",
    "windSpeedInKilometerPerHour",
    "windDirectionInDegree",
    "effectiveCloudCoverInOcta"
]

forecast_url = 'https://point-forecast.weather.mg/forecast/hourly?locatedAt={location}&validPeriod={period}&fields={fields}&validFrom={start}&validUntil={end}';
forecast_config = {
	'PT0S': [
		"airTemperatureInCelsius", 
		"feelsLikeTemperatureInCelsius", 
        "relativeHumidityInPercent",
		"windSpeedInKilometerPerHour", 
		"windDirectionInDegree", 
		"effectiveCloudCoverInOcta", 
		"thunderstormProbabilityInPercent",
		"freezingRainProbabilityInPercent",
		"hailProbabilityInPercent",
		"snowfallProbabilityInPercent",
		"precipitationProbabilityInPercent",
		# https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
		"precipitationType"
	],
	'PT1H': [
		"precipitationAmountInMillimeter", 
		"sunshineDurationInMinutes"
	],
	'PT3H': [
		"maxWindSpeedInKilometerPerHour"
	]
}
    
summeryOffsets = [0,4,8]
summeryFields = ["airTemperatureInCelsius","effectiveCloudCoverInOcta"]

class AuthException(Exception):
    pass

class RequestDataException(Exception):
    pass

class CurrentDataException(RequestDataException):
    pass
  
class ForecastDataException(RequestDataException):
    pass

class Fetcher(object):
    def __init__(self, config):
        self.config = config

    def getAuth(self):
      
        fields = {'grant_type': 'client_credentials'};
      
        r = requests.post(token_url, data=fields, auth=(self.config.api_username, self.config.api_password))
        if r.status_code != 200:
            raise AuthException("Failed getting auth token. Code: {}, Raeson: {}".format(r.status_code, r.reason))
        else:
            data = json.loads(r.text)
            if "access_token" in data:
                return data["access_token"]
            
        raise AuthException("Failed getting auth token. Content: {}".format(r.text))
      
    def get(self, url, token):
      
        headers = {"Authorization": "Bearer {}".format(token)}
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            raise RequestDataException("Failed getting data. Code: {}, Raeson: {}".format(r.status_code, r.reason))
        else:
            return json.loads(r.text)
      
    def fetchCurrent(self, token, mqtt, currentFallbacks ):
        
        date = datetime.now(timezone(self.config.timezone))
        end_date = date.strftime("%Y-%m-%dT%H:%M:%S%z")
        end_date = u"{0}:{1}".format(end_date[:-2],end_date[-2:])
        
        date = date - timedelta(hours=2)
        start_date = date.strftime("%Y-%m-%dT%H:%M:%S%z")
        start_date = u"{0}:{1}".format(start_date[:-2],start_date[-2:])
        
        latitude, longitude = self.config.location.split(",")
        location = u"{},{}".format(longitude,latitude)
        
        url = current_url.format(location=location, period="PT0S", fields=",".join(current_fields), start=urllib.parse.quote(start_date), end=urllib.parse.quote(end_date))
        
        data = self.get(url,token)
        if "observations" not in data:
            raise CurrentDataException("Failed getting current data. Content: {}".format(data))
        else:
            data["observations"].reverse()
            observedFrom = None
            missing_fields = None

            _data = {"observation": None, "missing_fields": current_fields}
            for observation in data["observations"]:
                missing_fields = [field for field in current_fields if field not in observation]

                if _data["observation"] is None or len(_data["missing_fields"]) < len(missing_fields):
                    _data["observation"] = observation
                    _data["missing_fields"] = missing_fields

                if len(_data["missing_fields"]) == 0:
                    break

            for missing_field in list(_data["missing_fields"]):
                if missing_field not in currentFallbacks:
                    continue

                logging.info("Use fallback data for field {}".format(missing_field))

                _data["observation"][missing_field] = currentFallbacks[missing_field]
                _data["missing_fields"].remove(missing_field)


            #time.sleep(60000)

            if len(_data["missing_fields"]) > 0:
                raise CurrentDataException("Failed processing current data. Missing fields: {}, Content: {}".format(_data["missing_fields"], _data["observation"]))
            else:
                for field in current_fields:
                    mqtt.publish("{}/weather/provider/current/{}".format(self.config.publish_topic,field), payload=_data["observation"][field], qos=0, retain=False)
                observedFrom = _data["observation"]["observedFrom"]

                mqtt.publish("{}/weather/provider/current/refreshed".format(self.config.publish_topic), payload=observedFrom, qos=0, retain=False)

            logging.info("Current data published")
            
    def fetchForecast(self, token, mqtt ):
        date = datetime.now(timezone(self.config.timezone))
        date = date + timedelta(hours=1)
        date = date.replace(minute=0, second=0)
        start_date = date.strftime("%Y-%m-%dT%H:%M:%S%z")
        start_date = u"{0}:{1}".format(start_date[:-2],start_date[-2:])
        
        latitude, longitude = self.config.location.split(",")
        location = u"{},{}".format(longitude,latitude)
        
        currentFallbacks = None
        _entries = {}
        _periods = {}
        for period in forecast_config:
            fields = forecast_config[period]

            if period in ["PT0S", "PT1H"]:
                end_date = (date + timedelta(hours=167)).strftime("%Y-%m-%dT%H:%M:%S%z") # 7 days => 168 hours - 1 hour (because last one is excluded)
                end_date = u"{0}:{1}".format(end_date[:-2],end_date[-2:])
            elif period in ["PT3H"]:
                end_date = (date + timedelta(hours=170)).strftime("%Y-%m-%dT%H:%M:%S%z") # 7 days => 167 hours + 3 hours, because of 3 hours timerange
                end_date = u"{0}:{1}".format(end_date[:-2],end_date[-2:])
            else:
                raise RequestDataException("Unhandled period")

            url = forecast_url.format(location=location, period=period, fields=",".join(fields), start=urllib.parse.quote(start_date), end=urllib.parse.quote(end_date))
                   
            data = self.get(url,token)
            if data == None or "forecasts" not in data:
                raise ForecastDataException("Failed getting forecast data. Content: {}".format(data))
              
            _periods[period] = {"start": start_date, "end": end_date, "values": []}
            for forecast in data["forecasts"]:
                _periods[period]["values"].append({"from": forecast["validFrom"], "until": forecast["validUntil"]})

                if period == "PT0S":
                    values = {}
                    values["validFromAsString"] = forecast["validFrom"]
                    values["validUntilAsString"] = forecast["validUntil"]
                    values["validFromAsDatetime"] = datetime.strptime(u"{0}{1}".format(forecast["validFrom"][:-3],forecast["validFrom"][-2:]),"%Y-%m-%dT%H:%M:%S%z")
                    values["validUntilAsDatetime"] = datetime.strptime(u"{0}{1}".format(forecast["validUntil"][:-3],forecast["validUntil"][-2:]),"%Y-%m-%dT%H:%M:%S%z")
                    _entries[values["validFromAsString"]] = values

                    for field in fields:
                        values[field] = forecast[field]

                    currentFallbacks = values
                else:
                    validFrom = datetime.strptime(u"{0}{1}".format(forecast["validFrom"][:-3],forecast["validFrom"][-2:]),"%Y-%m-%dT%H:%M:%S%z")
                    validUntil = datetime.strptime(u"{0}{1}".format(forecast["validUntil"][:-3],forecast["validUntil"][-2:]),"%Y-%m-%dT%H:%M:%S%z")

                    #logging.info("{}: {} {}".format(period, forecast["validFrom"], forecast["validUntil"]))
                    for entry in _entries.values():
                        if entry["validFromAsDatetime"] >= validFrom and entry["validUntilAsDatetime"] <= validUntil:
                            for field in fields:
                                entry[field] = forecast[field]

        _forecast_values = list(_entries.values())
        forecast_values = list(filter(lambda d: len(d) == 19, _forecast_values)) # 15 values + 4 datetime related fields

        if len(forecast_values) < 168:
            for period, data in _periods.items():
                logging.info("PERIOD {}: {} => {}, COUNT: {}".format(period, data["start"], data["end"], len(data["values"])))
                logging.info("DATA: {}".format(data["values"]))
            raise ForecastDataException("Not enough forecast data. Unvalidated: {}, Validated: {}".format(len(_forecast_values), len(forecast_values)))

        for forecast in forecast_values:
            date = forecast["validFromAsString"]
            date = date.replace("+","plus")
            for field in forecast:
                if field.startswith("valid"):
                    continue
                mqtt.publish("{}/weather/provider/forecast/{}/{}".format(self.config.publish_topic,field,date), payload=forecast[field], qos=0, retain=False)
            #mqtt.publish("{}/weather/forecast/refreshed/{}".format(self.config.publish_topic,date), payload="1", qos=0, retain=False)
        mqtt.publish("{}/weather/provider/forecast/refreshed".format(self.config.publish_topic), payload="1", qos=0, retain=False)

        logging.info("Forecast data published • Total: {}".format(len(forecast_values)))

        return currentFallbacks

    def triggerSummerizedItems(self, db, mqtt):
        with db.open() as db:
            result = db.getFullDay()

            tmp = {}
            for field in summeryFields:
                tmp[field] = [ None, None, decimal.Decimal(0.0) ]
            for row in result:
                for field in tmp:
                    value = row[field]
                    if tmp[field][0] == None:
                        tmp[field][0] = decimal.Decimal(0.0) + value
                        tmp[field][1] = decimal.Decimal(0.0) + value
                    else:
                        if tmp[field][0] > value:
                            tmp[field][0] = value
                        if tmp[field][1] < value:
                            tmp[field][1] = value

                    tmp[field][2] = tmp[field][2] + value
            for field in summeryFields:
                tmp[field][2] = tmp[field][2] / len(result)

                mqtt.publish("{}/weather/provider/items/{}/{}".format(self.config.publish_topic,field,"min"), payload=str(tmp[field][0]).encode("utf-8"), qos=0, retain=False)
                mqtt.publish("{}/weather/provider/items/{}/{}".format(self.config.publish_topic,field,"max"), payload=str(tmp[field][1]).encode("utf-8"), qos=0, retain=False)
                mqtt.publish("{}/weather/provider/items/{}/{}".format(self.config.publish_topic,field,"avg"), payload=str(tmp[field][2]).encode("utf-8"), qos=0, retain=False)

            for offset in summeryOffsets:
                data = db.getOffset(offset)
                for field, value in data.items():
                    mqtt.publish("{}/weather/provider/items/{}/{}".format(self.config.publish_topic,field,offset), payload=str(value).encode("utf-8"), qos=0, retain=False)
            mqtt.publish("{}/weather/provider/items/refreshed".format(self.config.publish_topic), payload="1", qos=0, retain=False)

            logging.info("Summery data published")

class Meteo():
    '''Handler client'''
    def __init__(self, config, db, mqtt):
        self.is_running = False
        self.is_fetching = False

        self.config = config
        self.db = db
        self.mqtt = mqtt

        self.is_enabled = self.config.publish_topic and self.config.api_username and self.config.api_password

        self.event = threading.Event()

        self.dump_path = "{}provider_meteo.json".format(config.lib_path)
        self.version = 1
        self.valid_cache_file = True

        self.service_metrics = { "data_provider": -1, "data_current": -1, "data_forecast": -1, "publish": -1 }

        self.last_consume_error = None

        self.last_fetch = 0

    def start(self):
        self._restore()
        if not os.path.exists(self.dump_path):
            self._dump()
        self.is_running = True

        if not self.is_enabled:
            logging.info("Publishing disabled")
        else:
            schedule.every().hour.at("05:00").do(self.fetch)
            if time.time() - self.last_fetch > 60 * 60:
                self.fetch()

    def terminate(self):
        if self.is_running and os.path.exists(self.dump_path):
            self._dump()
        self.is_running = False
        self.event.set()

    def _restore(self):
        self.valid_cache_file, data = ConfigHelper.loadConfig(self.dump_path, self.version )
        if data is not None:
            self.last_fetch = data["last_fetch"]
            logging.info("Loaded provider state")

    def _dump(self):
        if self.valid_cache_file:
            ConfigHelper.saveConfig(self.dump_path, self.version, { "last_fetch": self.last_fetch } )
            logging.info("Saved provider state")

    def fetch(self):
        if self.is_fetching:
            logging.warn("Skip fetching. Older job is still runing")
            return

        if not self.is_running:
            return

        self.is_fetching = True

        error_count = 0
        while self.is_running:
            try:
                fetcher = Fetcher(self.config)

                authToken = fetcher.getAuth()

                currentFallbacks = fetcher.fetchForecast(authToken,self.mqtt)
                self.service_metrics["data_forecast"] = 1

                fetcher.fetchCurrent(authToken,self.mqtt, currentFallbacks)
                self.service_metrics["data_current"] = 1

                fetcher.triggerSummerizedItems(self.db, self.mqtt)
                
                date = datetime.now(timezone(self.config.timezone))
                target = date.replace(minute=5,second=0)
                
                if target <= date:
                    target = target + timedelta(hours=1)

                diff = target - date
                
                sleepTime = diff.total_seconds()  
                
                error_count = 0

                self.service_metrics["data_provider"] = 1
                self.service_metrics["publish"] = 1

                self.last_fetch = time.time()

                self.is_fetching = False
                return
            except ForecastDataException as e:
                logging.info("{}: {}".format(str(e.__class__),str(e)))
                self.service_metrics["data_forecast"] = 0
                error_count += 1
            except CurrentDataException as e:
                logging.info("{}: {}".format(str(e.__class__),str(e)))
                self.service_metrics["data_current"] = 0
                error_count += 1
            except (RequestDataException,AuthException,requests.exceptions.RequestException) as e:
                logging.info("{}: {}".format(str(e.__class__),str(e)))
                self.service_metrics["data_provider"] = 0
                error_count += 1
            except DBException:
                error_count += 1
            #except MQTT Exceptions?? as e:
            #    logging.info("{}: {}".format(str(e.__class__),str(e)))
            #    self.service_metrics["mqtt"] = 0
            #    error_count += 1
            except Exception as e:
                logging.info("{}: {}".format(str(e.__class__),str(e)))
                traceback.print_exc()
                self.service_metrics["publish"] = 0
                error_count += 1

            if error_count > 0:
                sleepTime = 600 * error_count if error_count < 6 else 3600

            logging.info("Sleep {} seconds".format(sleepTime))
            self.event.wait(sleepTime)
            self.event.clear()

    def getStateMetrics(self):
        state_metrics = []
        for name, value in self.service_metrics.items():
            state_metrics.append("weather_service_state{{type=\"provider\", group=\"{}\"}} {}".format(name,value))

        if not self.is_enabled:
            state = -1
        else:
            if self.is_fetching:
                state = 1 if time.time() - self.last_fetch < 60 * 60 * 3 else 0
            else:
                state = 1 if time.time() - self.last_fetch < 60 * 60 + 5 * 60 else 0

        state_metrics.append("weather_service_state{{type=\"provider\", group=\"running\"}} {}".format(state))
        return state_metrics



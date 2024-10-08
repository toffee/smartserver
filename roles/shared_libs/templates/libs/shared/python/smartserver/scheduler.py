import schedule
import threading
import logging
import traceback

from smartserver.metric import Metric


class Scheduler(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.is_running = False
        self.event = threading.Event()
        self.name = name

    def start(self):
        self.is_running = True
        super().start()

    def terminate(self):
        self.is_running = False
        self.event.set()
        self.join()

    def run(self):
        logging.info("Scheduler started")
        try:
            while self.is_running:
                n = schedule.idle_seconds()
                if n is None:
                    n = 1
                if n > 0:
                    self.event.wait(n)

                schedule.run_pending()

        except Exception as e:
            self.is_running = False
            raise e
        finally:
            logging.info("Scheduler stopped")

    def getStateMetrics(self):
        return [
            Metric.buildProcessMetric(self.name, "scheduler", "1" if self.is_running else "0")
        ]

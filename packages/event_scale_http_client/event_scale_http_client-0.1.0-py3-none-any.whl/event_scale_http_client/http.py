import requests
import time
from urllib3.util.retry import Retry


class Http:
    def __init__(self):
        self.retries = 0
        self.retry_callback = None
        self.delay = 1

        self.form = False

    def asForm(self):
        self.form = True
        return self

    def set_retries(self, retries: int):
        self.retries = retries
        return self

    def set_retry_callback(self, callback):
        self.retry_callback = callback
        return self

    def retry(self, retries: int, callback, delay: float = 1):
        """Return a configured Http instance with retry and callback."""
        self.retries = retries
        self.retry_callback = callback
        self.delay = delay
        return self

    def get(self, url: str, data: dict = None, **kwargs):
        return self.send("GET", url, params=data, **kwargs)

    def post(self, url: str, data: dict = None, **kwargs):
        return self.send("POST", url, data=data, **kwargs)

    def send(self, method: str, url: str, **kwargs):
        attempt = 0
        while True:
            try:
                response = requests.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except Exception as e:
                attempt += 1
                if attempt > self.retries:
                    raise e

                if self.retry_callback:
                    self.retry_callback(attempt, e)

                time.sleep(self.delay)

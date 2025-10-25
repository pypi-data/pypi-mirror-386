# HTTP Client

A lightweight, chainable HTTP client for Python that supports automatic retries, custom retry callbacks, and easy JSON or form submissions.

### Features

* Simple and expressive chainable API
* Built-in retry support with customizable retry callbacks
* Automatic JSON and form data handling
* Fully testable with responses
* No heavy dependencies — designed to be minimal and easy to extend

### Usage

1. Basic GET request

```python
from event_scale_http_client import Http

response = Http().get("http://127.0.0.1:7000/", {
    "name": "Alex"
})
print(response.status_code)
print(response.json())
```

2. Automatic retries with callback

You can define how many times the request should retry and handle each failed attempt with a callback:

```python
from event_scale_http_client import Http


def retry_callback(attempt, error):
    print(f"Attempt {attempt} failed due to: {error}")


(
    Http()
    .retry(3, retry_callback)
    .get("http://127.0.0.1:7000/")
)
```

Explanation:
* retry(3, callback) → retries up to 3 times if the request fails.
* The callback function receives two arguments:
attempt → current attempt number (starting at 1)
error → the exception or status that caused the failure

3. POST request with JSON body

```python
from event_scale_http_client import Http

data = {
    "name": "Bedram",
    "email": "tmgbedu@gmail.com"
}

response = Http().post("http://127.0.0.1:7000", data)
print(response.status_code)
```

* [x] Sends JSON data by default (Content-Type: application/json).

4. POST request as form data

```python
from event_scale_http_client import Http

(
    Http()
    .asForm()
    .post("http://127.0.0.1:7000", {
        "name": "Bedram",
        "email": "tmgbedu@gmail.com"
    })
)
```

* [x] Sends data as application/x-www-form-urlencoded.
* [x] Automatically encodes form fields.

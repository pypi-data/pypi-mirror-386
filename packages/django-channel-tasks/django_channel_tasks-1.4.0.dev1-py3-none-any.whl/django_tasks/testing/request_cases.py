import abc
import json
import logging
import os

from typing import Optional

import requests

from rest_framework.test import APIClient

from django_tasks.http_status import HttpStatus
from django_tasks.typing import JSON


class RequestResponseCase(metaclass=abc.ABCMeta):
    """An HTTP request-response example, for testing and documentation purposes."""
    #: Name of an environment variable containing a test API token.
    token_envvar: str = 'DJANGO_TASKS_API_TEST_TOKEN'

    #: The base URL for all requests.
    base_url: str = ''

    #: Headers included in all requests.
    default_request_headers: dict[str, str] = {
        'Authorization': f'Token {os.getenv(token_envvar, "")}',
        'Content-Type': 'application/json',
    }

    def __init__(self, method: str, uri: str, data: JSON = None, headers: Optional[dict[str, str]] = None):
        self.method = method.strip().lower()
        self.uri = uri.strip().lstrip('/')
        self.data = data
        self.headers = headers or {}
        self.headers.update(self.default_request_headers)

    @abc.abstractmethod
    def perform_request(self):
        """Perform the request, return the response."""

    @property
    def response(self):
        return self._response

    @property
    def status_code(self) -> HttpStatus:
        return self._status_code

    @property
    def response_json(self) -> JSON:
        return self._response_json

    def perform(self):
        """Performs the request and sets all required properties from the obtained response."""
        self._response = self.perform_request()
        self._status_code = HttpStatus(self.response.status_code)
        self._response_json = (json.loads(self.response.content)
                               if self.response.headers.get('content-type') == 'application/json'
                               else None)

    @property
    def url(self) -> str:
        return f'{self.base_url}/{self.uri}'

    @property
    def base_uri(self) -> str:
        return self.uri.split('?')[0] if '?' in self.uri else self.uri

    @property
    def action(self) -> str:
        return f"{self.method}-{self.base_uri.replace('/', '')}"

    @property
    def type_code(self) -> str:
        return self.__class__.__name__.replace('RequestResponseCase', '').lower()

    def generate_rst_lines(self, number: int):
        request_section = f'Request example {number}'
        response_section = f'Response example {number}'
        base_uri, type_code = self.base_uri, self.type_code

        yield f'.. _{self.method}-to-{base_uri}-{type_code}-{number}:\n\n'
        yield f'**[⇡] {request_section}**:\n\n'
        yield '.. sourcecode:: http\n\n'
        yield f'   {self.method.upper()} /{self.uri} HTTP/1.1\n'

        for key, header in self.headers.items():
            if key.lower() == 'authorization':
                word, token, *_ = header.split()

                if not (not _ and word.lower() in ['basic', 'token', 'bearer']):
                    logging.getLogger('pytest').warning(f"Unexpected authorization header format: {header}")

                yield f'   {key.capitalize()}: {word.capitalize()} {"*"*len(token)}\n'
            else:
                yield f'   {key.capitalize()}: {header}\n'

        if self.data:
            yield '   \n'
            for data_line in json.dumps(self.data, indent=4).splitlines():
                yield f'   {data_line}\n'

        yield f'\n.. _{self.method}-from-{base_uri}-{type_code}-{number}:\n\n'
        yield f'**[⇣] {response_section}**:\n\n'
        yield '.. sourcecode:: http\n\n'
        yield f'   HTTP/1.1 {self.status_code} {self.status_code.name}\n'

        for key, header in self.response.headers.items():
            yield f'   {key.capitalize()}: {header}\n'

        if self.response_json:
            yield '   \n'
            for data_line in json.dumps(self.response_json, indent=4).splitlines():
                yield f'   {data_line}\n'
        elif self.response.content:
            yield '   \n'
            yield f'   {self.response.content.decode()}\n'


class AsgiRequestResponseCase(RequestResponseCase):
    base_url = 'http://127.0.0.1:8001'

    def perform_request(self):
        return getattr(requests, self.method)(self.url, data=json.dumps(self.data).encode(), headers=self.headers)


class WsgiRequestResponseCase(RequestResponseCase):
    base_url = ''

    def perform_request(self):
        return getattr(APIClient(), self.method)(self.url, data=self.data, headers=self.headers)


class HttpEndpointCaseSet:
    def __init__(self, file_name: str, *request_response_cases: RequestResponseCase):
        self.file_name = file_name
        self.cases = request_response_cases

    @property
    def rst_path(self) -> str:
        return f"sphinx/source/requests/{self.file_name}.rst"

    def write_rst(self):
        with open(self.rst_path, 'w') as rst_file:
            for i, request_response_case in enumerate(self.cases, start=1):
                rst_file.writelines(request_response_case.generate_rst_lines(i))

                if i != len(self.cases):
                    rst_file.write('\n----\n\n')

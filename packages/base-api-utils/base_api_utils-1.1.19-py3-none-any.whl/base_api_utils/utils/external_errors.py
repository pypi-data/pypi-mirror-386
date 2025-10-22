import json
import logging

import pybreaker
import requests
from rest_framework.response import Response
from rest_framework import status

class NamedCircuitBreakerError(pybreaker.CircuitBreakerError):
    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Circuit breaker for {service_name} is open.")

def handle_external_service_errors(e):
    if isinstance(e, NamedCircuitBreakerError):
        logging.error(f"Circuit breaker error: {e}")
        return Response(
            {
                'message': f'The {e.service_name} is currently unavailable. Please try again later.',
                'errors': ['circuit_breaker_open']
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    if isinstance(e, pybreaker.CircuitBreakerError):
        logging.error(f"Circuit breaker error: {e}")
        return Response(
            {
                'message': 'An external service is temporarily unavailable due to repeated failures.',
                'errors': ['circuit_breaker_open']
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    if isinstance(e, requests.HTTPError) and e.response is not None:
        if 400 <= e.response.status_code < 500:
            try:
                error_data = e.response.json()
                error_desc = error_data.get('message', error_data.get('error', 'Unknown error'))
            except (json.JSONDecodeError, ValueError):
                error_desc = e.response.text or 'No error description available'

            status_code = e.response.status_code

            return Response(
                {
                    'message': f'External service returned a client error.',
                    'errors': [error_desc]
                },
                status=status_code
            )
        elif 500 <= e.response.status_code < 600:
            status_code = e.response.status_code
            return Response(
                {
                    'message': f'External service returned a server error.',
                    'errors': []
                },
                status=status_code
            )

    if isinstance(e, requests.RequestException):
        return Response(
            {
                'message': 'Failed to connect to the external service.',
                'errors': ['external_service_connection_failed']
            },
            status=status.HTTP_502_BAD_GATEWAY
        )

    return None  # Not handled here

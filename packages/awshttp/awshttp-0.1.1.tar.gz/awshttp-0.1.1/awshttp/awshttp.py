#!/usr/bin/env python3
"""AWS SigV4 signed HTTP requests using botocore.

This module provides a simple interface for making AWS SigV4 signed HTTP requests
with automatic credential detection. Perfect for Lambda functions and scripts.
"""

import json
import os
import time
from typing import Any, Callable

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

__version__ = '0.1.1'
__all__ = ['request', 'get', 'post', 'put', 'delete', 'patch', 'with_retry', 'post_json', 'put_json']


def request(
    uri: str,
    method: str = 'GET',
    service: str = 'execute-api',
    region: str | None = None,
    headers: dict[str, str] | None = None,
    data: str | bytes = '',
    verify: bool = True,
    allow_redirects: bool = False,
    timeout: float | None = None,
    session: boto3.Session | None = None,
) -> requests.Response:
    """Make a signed AWS request with automatic credential detection.
    
    Perfect for Lambda functions - automatically uses IAM role credentials.
    
    Args:
        uri: Full URL to request
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        service: AWS service name (execute-api, s3, ec2, etc.)
        region: AWS region (auto-detects from env if None)
        headers: Dict of HTTP headers
        data: Request body (string or bytes)
        verify: Verify SSL certificates
        allow_redirects: Follow redirects
        timeout: Request timeout in seconds
        session: Boto3 session (creates new if None)
    
    Returns:
        requests.Response object
    
    Example:
        import awshttp
        
        # In Lambda - credentials auto-detected
        response = awshttp.get('https://api.example.com/endpoint')
        print(response.json())
    """
    region = region or os.environ.get('AWS_DEFAULT_REGION') or os.environ.get('AWS_REGION', 'us-east-1')
    
    # Override defaults from environment
    if timeout is None:
        timeout = float(os.environ.get('AWSHTTP_TIMEOUT', 0)) or None
    if not verify and 'AWSHTTP_VERIFY_SSL' in os.environ:
        verify = os.environ.get('AWSHTTP_VERIFY_SSL', 'true').lower() == 'true'
    
    session = session or boto3.Session()
    credentials = session.get_credentials()
    
    aws_request = AWSRequest(method=method, url=uri, data=data, headers=headers or {})
    SigV4Auth(credentials, service, region).add_auth(aws_request)
    
    return requests.request(
        method=aws_request.method,
        url=aws_request.url,
        headers=dict(aws_request.headers),
        data=aws_request.body,
        verify=verify,
        allow_redirects=allow_redirects,
        timeout=timeout,
    )


def get(uri: str, **kwargs: Any) -> requests.Response:
    """Convenience method for GET requests."""
    return request(uri, method='GET', **kwargs)


def post(uri: str, data: str | bytes = '', **kwargs: Any) -> requests.Response:
    """Convenience method for POST requests."""
    return request(uri, method='POST', data=data, **kwargs)


def put(uri: str, data: str | bytes = '', **kwargs: Any) -> requests.Response:
    """Convenience method for PUT requests."""
    return request(uri, method='PUT', data=data, **kwargs)


def delete(uri: str, **kwargs: Any) -> requests.Response:
    """Convenience method for DELETE requests."""
    return request(uri, method='DELETE', **kwargs)


def patch(uri: str, data: str | bytes = '', **kwargs: Any) -> requests.Response:
    """Convenience method for PATCH requests."""
    return request(uri, method='PATCH', data=data, **kwargs)


def with_retry(
    retries: int = 3, 
    backoff: float = 1.0, 
    status_codes: tuple[int, ...] = (429, 500, 502, 503, 504)
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to add retry logic to requests.
    
    Args:
        retries: Number of retry attempts
        backoff: Base delay between retries (exponential backoff)
        status_codes: HTTP status codes that trigger retries
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(retries + 1):
                try:
                    response = func(*args, **kwargs)
                    if response.status_code not in status_codes:
                        return response
                except requests.RequestException:
                    if attempt == retries:
                        raise
                
                if attempt < retries:
                    time.sleep(backoff * (2 ** attempt))
            return response
        return wrapper
    return decorator


def post_json(uri: str, data: dict[str, Any], **kwargs: Any) -> requests.Response:
    """POST JSON data with automatic content-type header."""
    headers = kwargs.get('headers', {})
    headers['content-type'] = 'application/json'
    kwargs['headers'] = headers
    return post(uri, data=json.dumps(data), **kwargs)


def put_json(uri: str, data: dict[str, Any], **kwargs: Any) -> requests.Response:
    """PUT JSON data with automatic content-type header."""
    headers = kwargs.get('headers', {})
    headers['content-type'] = 'application/json'
    kwargs['headers'] = headers
    return put(uri, data=json.dumps(data), **kwargs)




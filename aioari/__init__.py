#
# Copyright (c) 2013, Digium, Inc.
# Copyright (c) 2016, fokin.denis@gmail.com
#

"""AIOARI client library
"""

from aioari.client import Client
from aioswagger11.http_client import AsynchronousHttpClient, ApiKeyAuthenticator
import urllib.parse

async def connect(base_url, username, password, loop=None):
    """Helper method for easily async connecting to ARI.

    :param base_url: Base URL for Asterisk HTTP server (http://localhost:8088/)
    :param username: ARI username
    :param password: ARI password
    :param loop: asyncio main loop (optional)
    :return:
    """
    host = urllib.parse.urlparse(base_url).netloc.split(':')[0]
    http_client = AsynchronousHttpClient(loop=loop, 
        auth=ApiKeyAuthenticator(host, username+':'+password))
    client = Client(base_url, http_client)
    await client.init()
    return client

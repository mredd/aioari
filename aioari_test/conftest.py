#!/usr/bin/env python

import httpretty as htpr
import os
from urllib import parse as urlparse
import aioari
import requests
import pytest


@pytest.fixture
def httpretty(request, event_loop):
    """Setup httpretty; create ARI client.
        """
    #super(AriTestCase, self).setUp()
    htpr.enable()
    request.instance.setUp(event_loop)

    yield 123

    request.instance.tearDown(event_loop)
    htpr.disable()
    htpr.reset()

#!/usr/bin/env python

"""Short example of how to use bridge objects.

This example will create a holding bridge (if one doesn't already exist). Any
channels that enter Stasis is placed into the bridge. Whenever a channel
enters the bridge, a tone is played to the bridge.
"""

#
# Copyright (c) 2013, Digium, Inc.
#

import asyncio
import aioari

import os
ast_url = os.getenv("AST_URL", 'http://localhost:8088/')
ast_username = os.getenv("AST_USER", 'asterisk')
ast_password = os.getenv("AST_PASS", 'asterisk')
ast_app = os.getenv("AST_APP", 'hello')

bridge = None

async def setup():
    global bridge
    client = await aioari.connect(ast_url, ast_username,ast_password)

    #
    # Find (or create) a holding bridge.
    #
    bridges = [b for b in (await client.bridges.list()) if
            b.json['bridge_type'] == 'holding']
    if bridges:
        bridge = bridges[0]
        print "Using bridge %s" % bridge.id
    else:
        bridge = await client.bridges.create(type='holding')
        print "Created bridge %s" % bridge.id
    return client

async def on_enter(bridge, ev):
    """Callback for bridge enter events.

    When channels enter the bridge, play tones to the whole bridge.

    :param bridge: Bridge entering the channel.
    :param ev: Event.
    """
    # ignore announcer channels - see ASTERISK-22744
    if ev['channel']['name'].startswith('Announcer/'):
        return
    await bridge.play(media="sound:ascending-2tone")


bridge.on_event('ChannelEnteredBridge', on_enter)


def stasis_start_cb(channel, ev):
    """Callback for StasisStart events.

    For new channels, answer and put them in the holding bridge.

    :param channel: Channel that entered Stasis
    :param ev: Event
    """
    await channel.answer()
    await bridge.addChannel(channel=channel.id)


client.on_channel_event('StasisStart', stasis_start_cb)

# Run the WebSocket
loop = asyncio.get_event_loop()
client = loop.run_until_complete(setup())
loop.run_until_complete(client.run(apps=ast_app))

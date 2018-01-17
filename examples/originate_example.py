#!/usr/bin/env python

"""Example demonstrating ARI channel origination.

"""

#
# Copyright (c) 2013, Digium, Inc.
#
import aioari
import asyncio

from aiohttp.web_exceptions import HTTPError, HTTPNotFound

import os
ast_url = os.getenv("AST_URL", 'http://localhost:8088/')
ast_username = os.getenv("AST_USER", 'asterisk')
ast_password = os.getenv("AST_PASS", 'asterisk')
ast_app = os.getenv("AST_APP", 'hello')
ast_outgoing = os.getenv("AST_OUTGOING", 'SIP/blink')


holding_bridge = None
async def init():
    global holding_bridge
    client = await aioari.connect(ast_url, ast_username,ast_password)

    #
    # Find (or create) a holding bridge.
    #
    bridges = [b for b in (await client.bridges.list())
            if b.json['bridge_type'] == 'holding']
    if bridges:
        holding_bridge = bridges[0]
        print ("Using bridge %s" % holding_bridge.id)
    else:
        holding_bridge = await client.bridges.create(type='holding')
        print ("Created bridge %s" % holding_bridge.id)
    return client


async def safe_hangup(channel):
    """Hangup a channel, ignoring 404 errors.

    :param channel: Channel to hangup.
    """
    try:
        await channel.hangup()
    except HTTPError as e:
        # Ignore 404's, since channels can go away before we get to them
        if e.response.status_code != HTTPNotFound.status_code:
            raise


async def on_start(objs, event):
    """Callback for StasisStart events.

    When an incoming channel starts, put it in the holding bridge and
    originate a channel to connect to it. When that channel answers, create a
    bridge and put both of them into it.

    :param incoming:
    :param event:
    """
    # Don't process our own dial
    if event['args'] == ['dialed']:
        return

    # Answer and put in the holding bridge
    incoming = objs['channel']
    await incoming.answer()
    p = await incoming.play(media="sound:pls-wait-connect-call")
    print(p)
    await asyncio.sleep(2)
    h = await holding_bridge.addChannel(channel=incoming.id)
    print(h)

    # Originate the outgoing channel
    outgoing = await client.channels.originate(
        endpoint=ast_outgoing, app=ast_app, appArgs="dialed")
    print("OUT:",outgoing)

    # If the incoming channel ends, hangup the outgoing channel
    incoming.on_event('StasisEnd', lambda *args: safe_hangup(outgoing))
    # and vice versa. If the endpoint rejects the call, it is destroyed
    # without entering Stasis()
    outgoing.on_event('ChannelDestroyed',
                      lambda *args: safe_hangup(incoming))

    async def outgoing_on_start(channel, event):
        """Callback for StasisStart events on the outgoing channel

        :param channel: Outgoing channel.
        :param event: Event.
        """
        # Create a bridge, putting both channels into it.
        print("Bridging",channel)
        bridge = await client.bridges.create(type='mixing')
        await outgoing.answer()
        await bridge.addChannel(channel=[incoming.id, outgoing.id])
        print("Bridged",incoming,outgoing)
        # Clean up the bridge when done
        outgoing.on_event('StasisEnd', lambda *args: bridge.destroy())

    outgoing.on_event('StasisStart', outgoing_on_start)


loop = asyncio.get_event_loop()
client = loop.run_until_complete(init())
client.on_channel_event('StasisStart', on_start)

# Run the WebSocket
loop.run_until_complete(client.run(apps=ast_app))


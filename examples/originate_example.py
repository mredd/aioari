#!/usr/bin/env python

"""Example demonstrating ARI channel origination.

"""

#
# Copyright (c) 2013, Digium, Inc.
#
import requests

import aioari

from requests import HTTPError

OUTGOING_ENDPOINT = "SIP/blink"

def init():
    client = await aioari.connect('http://localhost:8088/', 'hey', 'peekaboo')

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


def async safe_hangup(channel):
    """Hangup a channel, ignoring 404 errors.

    :param channel: Channel to hangup.
    """
    try:
        await channel.hangup()
    except HTTPError as e:
        # Ignore 404's, since channels can go away before we get to them
        if e.response.status_code != requests.codes.not_found:
            raise


async def on_start(incoming, event):
    """Callback for StasisStart events.

    When an incoming channel starts, put it in the holding bridge and
    originate a channel to connect to it. When that channel answers, create a
    bridge and put both of them into it.

    :param incoming:
    :param event:
    """
    # Only process channels with the 'incoming' argument
    if event['args'] != ['incoming']:
        return

    # Answer and put in the holding bridge
    await incoming.answer()
    await incoming.play(media="sound:pls-wait-connect-call")
    await holding_bridge.addChannel(channel=incoming.id)

    # Originate the outgoing channel
    outgoing = await client.channels.originate(
        endpoint=OUTGOING_ENDPOINT, app="hello", appArgs="dialed")

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
        bridge = await client.bridges.create(type='mixing')
        await outgoing.answer()
        await bridge.addChannel(channel=[incoming.id, outgoing.id])
        # Clean up the bridge when done
        outgoing.on_event('StasisEnd', lambda *args: bridge.destroy())

    outgoing.on_event('StasisStart', outgoing_on_start)


loop = asyncio.get_event_loop()
client = loop.run_until_complete(init())
client.on_channel_event('StasisStart', on_start)

# Run the WebSocket
loop.run_until_complete(client.run(apps="hello"))


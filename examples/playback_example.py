#!/usr/bin/env python

"""Example demonstrating using the returned object from an API call.

This app plays demo-contrats on any channel sent to Stasis(hello). DTMF keys
are used to control the playback.
"""

#
# Copyright (c) 2013, Digium, Inc.
#

import asyncio
import ari
import sys


async def on_start(channel, event):
    """Callback for StasisStart events.

    On new channels, answer, play demo-congrats, and register a DTMF listener.

    :param channel: Channel DTMF was received from.
    :param event: Event.
    """
    await channel.answer()
    playback = await channel.play(media='sound:demo-congrats')

    async def on_dtmf(channel, event):
        """Callback for DTMF events.

        DTMF events control the playback operation.

        :param channel: Channel DTMF was received on.
        :param event: Event.
        """
        # Since the callback was registered to a specific channel, we can
        #  control the playback object we already have in scope.
        digit = event['digit']
        if digit == '5':
            await playback.control(operation='pause')
        elif digit == '8':
            await playback.control(operation='unpause')
        elif digit == '4':
            await playback.control(operation='reverse')
        elif digit == '6':
            await playback.control(operation='forward')
        elif digit == '2':
            await playback.control(operation='restart')
        elif digit == '#':
            await playback.stop()
            await channel.continueInDialplan()
        else:
            print >> sys.stderr, "Unknown DTMF %s" % digit

    channel.on_event('ChannelDtmfReceived', on_dtmf)


loop = asyncio.get_event_loop()
client = loop.run_until_complete(ari.connect('http://localhost:8088/', 'hey', 'peekaboo'))

client.on_channel_event('StasisStart', on_start)

# Run the WebSocket
loop.run_until_complete(client.run(apps='hello'))

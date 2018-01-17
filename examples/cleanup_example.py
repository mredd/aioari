#!/usr/bin/env python

"""ARI resources may be closed, if an application only needs them temporarily.
"""

#
# Copyright (c) 2013, Digium, Inc.
#

import asyncio
import aioari
import logging
import sys

import os
ast_url = os.getenv("AST_URL", 'http://localhost:8088/')
ast_username = os.getenv("AST_USER", 'asterisk')
ast_password = os.getenv("AST_PASS", 'asterisk')
ast_app = os.getenv("AST_APP", 'hello')

logging.basicConfig()

loop = asyncio.get_event_loop()
client = loop.run_until_complete(aioari.connect(ast_url, ast_username,ast_password))


# noinspection PyUnusedLocal
async def on_start(objs, event):
    """Callback for StasisStart events.

    On new channels, register the on_dtmf callback, answer the channel and
    play "Hello, world"

    :param channel: Channel DTMF was received from.
    :param event: Event.
    """
    on_dtmf_handle = None

    async def on_dtmf(channel, event):
        """Callback for DTMF events.

        When DTMF is received, play the digit back to the channel. # hangs up,
        * plays a special message.

        :param channel: Channel DTMF was received from.
        :param event: Event.
        """
        digit = event['digit']
        if digit == '#':
            await channel.play(media='sound:goodbye')
            await asyncio.sleep(2)
            await channel.continueInDialplan()
            on_dtmf_handle.close()
        elif digit == '*':
            await channel.play(media='sound:asterisk-friend')
        else:
            await channel.play(media='sound:digits/%s' % digit)

    channel = objs['channel']
    on_dtmf_handle = channel.on_event('ChannelDtmfReceived', on_dtmf)
    await channel.answer()
    await channel.play(media='sound:hello-world')

client.on_channel_event('StasisStart', on_start)

# Run the WebSocket

async def run():
    """Thread for running the Websocket.
    """
    def fileCallback(*args):
        # Callbacks run in non-async context. Oh well.
        loop.call_soon(asyncio.ensure_future,client.close())
    loop.add_reader(sys.stdin.fileno(), fileCallback)
    await client.run(apps=ast_app)

print("Press enter to exit")
loop.run_until_complete(run())
print("Application finished")


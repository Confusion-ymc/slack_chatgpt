import asyncio

from loguru import logger
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp
from slack_sdk.errors import SlackApiError

import config
from chatGPT.api import BotManager, Reply
from config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN

# app = App(token=SLACK_BOT_TOKEN)
async_app = AsyncApp(token=SLACK_BOT_TOKEN)

bot_manager = BotManager()


async def reply(message, say, conversation_id):
    logger.info(f'[{message["user"]}]  {message["text"]}')
    bot = bot_manager.get_bot(conversation_id)
    reply_cache = Reply()
    asyncio.create_task(bot.async_ask_update_cache(message['text'], reply_cache))

    body = await say(':writing_hand:')
    ts = body['ts']

    send_len = 0
    while not reply_cache.finish:
        if send_len != len(reply_cache.text):
            reply_text = reply_cache.text + ' :writing_hand:'
            try:
                result = await async_app.client.chat_update(
                    channel=message['channel'],
                    ts=ts,
                    text=reply_text
                )
                send_len = len(reply_cache.text)
                ts = result['ts']
            except SlackApiError as e:
                if 'msg_too_long' in str(e):
                    body = await say(reply_text)
                    ts = body['ts']
            except Exception as e:
                await say('slack api Error!')
                logger.error(e)
                return
        else:
            await asyncio.sleep(0.5)
    await async_app.client.chat_update(
        channel=message['channel'],
        ts=ts,
        text=reply_cache.text
    )


@async_app.event("message")
async def message_hello(message, say):
    if message['type'] == 'message':
        if message['channel_type'] == 'im':
            await reply(message, say, message['user'])
        elif message['channel_type'] == 'group' and f'<@{config.BOT_ID}>' in message['text']:
            await reply(message, say, message['channel'])


async def run():
    await AsyncSocketModeHandler(async_app, app_token=SLACK_APP_TOKEN, proxy=config.PROXY).start_async()


# Start your app
if __name__ == "__main__":
    asyncio.run(run())

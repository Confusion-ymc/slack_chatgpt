import asyncio
import datetime
import traceback

from typing import Dict

from loguru import logger
from revChatGPT.V3 import Chatbot

import config


class Reply:
    def __init__(self):
        self.text = ''
        self.finish = False


class MyBot(Chatbot):
    def __init__(self, *args, **kwargs):
        super(MyBot, self).__init__(*args, **kwargs)
        self.run_task = False

    async def async_ask_update_cache(self, ask_message, reply_cache):
        logger.info(f'[线程启动] {ask_message}')
        error = ''
        if self.run_task:
            reply_cache.text = '请等待上一条消息处理完毕后发送'
            reply_cache.finish = True
        else:
            self.run_task = True
            try:
                full_content = ''
                async for content in self.ask_stream_async(ask_message):
                    full_content += content
                    reply_cache.text = full_content
                reply_cache.finish = True
            except Exception as e:
                error = str(e)
                logger.error(traceback.format_exc())
                reply_cache.text += '\n[抱歉, 接口异常, 请重试]'
                reply_cache.finish = True
            finally:
                self.run_task = False
        logger.warning(f'[线程退出] {ask_message} {error}')

    async def async_ask_stream_async(self, ask_message):
        logger.info(f'[线程启动] {ask_message}')
        if self.run_task:
            yield {'data': '请等待上一条消息处理完毕后发送', 'finish': True}
        else:
            try:
                full_content = ''
                async for content in self.ask_stream_async(ask_message):
                    full_content += content
                    yield {'data': full_content, 'finish': False}
                yield {'data': '', 'finish': True}
            except Exception as e:
                error = str(e)
                print(traceback.format_exc())
                yield {'data': '[抱歉，对话超过模型支持长度，已重置上下文]', 'finish': True}
                logger.warning(f'[线程退出] {ask_message} {error}')
            finally:
                self.run_task = False

    def ask_for_reply(self, ask_message):
        logger.info(f'[线程启动] {ask_message}')
        if self.run_task:
            yield {'data': '请等待上一条消息处理完毕后发送', 'finish': True}
        else:
            error = ''
            try:
                full_content = ''
                for content in self.ask_stream(ask_message):
                    full_content += content
                    yield {'data': full_content, 'finish': False}
                yield {'data': '', 'finish': True}
            except Exception as e:
                error = str(e)
                print(traceback.format_exc())
                yield {'data': '[抱歉，对话超过模型支持长度，已重置上下文]', 'finish': True}
                logger.warning(f'[线程退出] {ask_message} {error}')
            finally:
                self.run_task = False


class BotManager:
    def __init__(self):
        self.bot_pool: Dict[str, MyBot] = {}
        self.bot_last_use_time = {}

    def get_bot(self, conversation_id) -> MyBot:
        self.clear_bot()
        bot = self.bot_pool.get(conversation_id)
        if not bot:
            bot = MyBot(api_key=config.chatGPT_APIKEY, proxy=config.PROXY)
            self.bot_pool[conversation_id] = bot
        self.bot_last_use_time[conversation_id] = datetime.datetime.now()
        return bot

    def clear_bot(self, conversation_id=None):
        if conversation_id:
            del self.bot_last_use_time[conversation_id]
            del self.bot_pool[conversation_id]
            return
        copy_last_use_time = self.bot_last_use_time.copy()
        for conversation_id, use_time in copy_last_use_time.items():
            if (datetime.datetime.now() - use_time) > datetime.timedelta(hours=1):
                del self.bot_last_use_time[conversation_id]
                del self.bot_pool[conversation_id]


async def test():
    bot_manager = BotManager()
    bot = bot_manager.get_bot('asd')
    async for reply_data in bot.async_ask_stream_async('你好'):
        print(reply_data)


if __name__ == '__main__':
    asyncio.run(test())

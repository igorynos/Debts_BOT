from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from debts_main.debts_server import DebtsServer

from data import config

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def sunc_send_message_for_all(user, msg):
    await bot.send_message(user, msg)


server = DebtsServer(msg_cbs=sunc_send_message_for_all)

from loader import dp, server, bot
from aiogram import types


@dp.callback_query_handler(text='total')
async def total(call: types.CallbackQuery):
    acc = server.get_current_accounting(user=call.message.chat.id)
    total = server.total_report(acc[0])
    file_name = 'Reports/'+total[0]
    await bot.send_document(call.message.chat.id, open(file_name, 'rb'))

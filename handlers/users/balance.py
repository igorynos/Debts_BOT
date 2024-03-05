from loader import dp, server
from aiogram import types


@dp.callback_query_handler(text='wallets_balance')
async def wallets_balance(call: types.CallbackQuery):
    acc_id = server.get_current_accounting(user=call.message.chat.id)[0]
    balance = server.wallet_balances(acc_id)[0]
    text = 'Баланс кошельков:\n'
    for x in balance.items():
        text += f'\n{x[0]}:  {x[1]}'

    await call.message.answer(text=text)

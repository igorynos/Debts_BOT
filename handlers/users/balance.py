from loader import dp, server
from aiogram import types


@dp.message_handler(text='Баланс')
async def balance(message: types.Message):
    acc = server.get_current_accounting(user=message.chat.id)
    user_wallets = server.my_wallet(acc[0], message.chat.id)
    wallet = server.get_wallet_balance(acc[0], user_wallets)
    text = f"Ваш баланс в расчёте: {wallet[0][0]['balance']}"
    await message.answer(text=text)


@dp.callback_query_handler(text='wallets_balance')
async def wallets_balance(call: types.CallbackQuery):
    acc_id = server.get_current_accounting(user=call.message.chat.id)[0]
    balance = server.wallet_balances(acc_id)[0]
    text = 'Баланс кошельков:\n'
    for x in balance.items():
        text += f'\n{x[0]}:  {x[1]}'

    await call.message.answer(text=text)

from loader import dp, db, server
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
    acc_id = server.get_current_accounting(user=call.message.chat.id)
    sql = ("SELECT wallet_balance.balance"
           "FROM wallets JOIN wallet_balance ON wallets.wallet = wallet_balance.id "
           "WHERE wallets.accounting_id = %s")
    balance = db.execute(sql, acc_id[0], fetchall=True)
    # text = 'Баланс кошельков:\n'
    # for x in balance:
    #     text += f'\n{x[1]}:  {x[2]}'

    # await call.message.answer(text=text)

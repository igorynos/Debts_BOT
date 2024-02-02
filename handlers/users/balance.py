from loader import dp, db, server
from aiogram import types


@dp.message_handler(text='Баланс')
async def balance(message: types.Message):
    acc = server.get_current_accounting(user=message.chat.id)
    lst_wallet = server.get_wallet_balance(acc[0])
    sql = "SELECT id FROM wallets WHERE user_id=%s"
    user_wallets = db.execute(sql, parameters=(message.chat.id), fetchall=True)
    for x in lst_wallet[0]:
        for y in user_wallets:
            if y[0] is x['id']:
                wallet = server.get_wallet_balance(acc[0], y[0])
                text = f"Ваш баланс в расчёте: {wallet[0][0]['balance']}"
                await message.answer(text=text)


@dp.callback_query_handler(text='wallets_balance')
async def wallets_balance(call: types.CallbackQuery):
    acc_id = server.get_current_accounting(user=call.message.chat.id)
    sql = ("SELECT DISTINCT wallets.wallet, wallet_balance.name, wallet_balance.balance"
           "FROM wallets JOIN wallet_balance ON wallets.wallet = wallet_balance.id "
           "WHERE accounting_id = %s")
    balance = db.execute(sql, acc_id[0], fetchall=True)
    text = 'Баланс кошельков:\n'
    for x in balance:
        text += f'\n{x[1]}:  {x[2]}'

    await call.message.answer(text=text)

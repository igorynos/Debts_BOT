from loader import dp, db, server
from aiogram import types
from keyboards.inline.menu_acc import menu_acc


@dp.message_handler(text='Активный расчёт')
async def active_acc(message: types.Message):
    acc = server.get_current_accounting(user=message.chat.id)
    sql = "SELECT name FROM accountings WHERE id=%s"
    name_acc = db.execute(sql, parameters=(acc[0]), fetchone=True)
    lst_users = server.get_group_users(acc[0])
    text = '\nУчастники расчёта:'
    for x in lst_users[0]:
        sql = "SELECT user_nic FROM users WHERE id=%s"
        name = db.execute(sql, parameters=(x), fetchone=True)
        text += f"\n{name[0]}"
    await message.answer(text=f'Активный расчёт: \n{name_acc[0]}\n{text}', reply_markup=menu_acc)

from loader import dp, db, server
from aiogram import types
from keyboards.inline.menu_acc import menu_acc


@dp.message_handler(text='Активный расчёт')
async def active_acc(message: types.Message):
    acc = server.get_current_accounting(user=message.chat.id)[0]
    name_acc = server.accounting_name(acc)[0]
    lst_users = server.get_group_users(acc)[0]
    text = '\nУчастники расчёта:'
    for x in lst_users:
        name = server.user_name(x)[0]
        text += f"\n{name}"
    await message.answer(text=f'Активный расчёт: \n{name_acc}\n{text}', reply_markup=menu_acc)

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import types
from keyboards.inline.callback_data import pay_lst_callback, merge_wallets_callback

from loader import dp, db, server


menu_acc = InlineKeyboardMarkup()

purchase = InlineKeyboardButton(
    "🛒 Покупки", callback_data='purchase')

payment_doc = InlineKeyboardButton(
    "🧾 Платёж", callback_data='payment_doc')

merge_wallets = InlineKeyboardButton(
    "👛➕💰\nОбьединить кошельки", callback_data='merge_wallets')

menu_acc = InlineKeyboardMarkup().add(purchase, payment_doc).add(merge_wallets)


def pay_lst(message: types.Message):
    change_card = InlineKeyboardMarkup()

    acc = server.get_current_accounting(user=message.chat.id)
    lst_users = server.get_group_users(acc[0])

    for x in lst_users[0]:
        if x != message.chat.id:
            sql = "SELECT user_nic FROM users WHERE id=%s"
            nic = db.execute(sql, parameters=(x), fetchall=True)

            change_card.add(InlineKeyboardButton(
                text=f"{nic[0][0]}", callback_data=pay_lst_callback.new(id=x)))
    return change_card


def merge_wallets_keyboard(message: types.Message, del_user=None):
    change_card = InlineKeyboardMarkup()

    acc = server.get_current_accounting(user=message.chat.id)
    lst_users = server.get_group_users(acc[0])
    lst_users = list(lst_users[0])

    if del_user is not None:
        lst_users.remove(int(del_user))

    for x in lst_users:
        if x != message.chat.id:
            sql = "SELECT user_nic FROM users WHERE id=%s"
            nic = db.execute(sql, parameters=(x), fetchall=True)

            change_card.add(InlineKeyboardButton(
                text=f"{nic[0][0]}", callback_data=merge_wallets_callback.new(id=x)))
    change_card.add(InlineKeyboardButton(
        text=f"✅ Обьединить", callback_data='accept_merge_wallets'))
    return change_card

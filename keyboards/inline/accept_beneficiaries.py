from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import types
from keyboards.inline.callback_data import bnfcrs_callback

from loader import dp, server

accept_bnfcrs = InlineKeyboardMarkup().add(InlineKeyboardButton(
    "Да", callback_data='accept_bnfcrs_next')).add(InlineKeyboardButton(
        "Нет", callback_data='accept_bnfcrs_no'))


def add_bnfcrs(message, del_bnfcrs=None):
    change_card = InlineKeyboardMarkup()

    acc = server.get_current_accounting(user=message.chat.id)[0]
    lst_bnfcrs = server.get_group_users(acc)[0]
    lst_bnfcrs = list(lst_bnfcrs)
    lst_bnfcrs.remove(int(message.chat.id))

    if del_bnfcrs is not None:
        for bnfcr in del_bnfcrs:
            lst_bnfcrs.remove(int(bnfcr))

    for bnfcr in lst_bnfcrs:
        wallet_name = server.user_name(bnfcr)[0]

        change_card.add(InlineKeyboardButton(
            text=f"{wallet_name}", callback_data=bnfcrs_callback.new(id=bnfcr)))
    change_card.add(InlineKeyboardButton(
        text=f"✅ Завершить покупку", callback_data='accept_bnfcrs_next'))
    return change_card

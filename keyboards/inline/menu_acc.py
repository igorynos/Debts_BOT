from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import types
from keyboards.inline.callback_data import pay_lst_callback, merge_wallets_callback

from loader import dp, server


purchase_payment = InlineKeyboardButton(
    "💳 Покупки/Платежи", callback_data='purchase_payment')

purchase = InlineKeyboardButton(
    "🛒 Покупки", callback_data='purchase')

payment_doc = InlineKeyboardButton(
    "💸 Платёж", callback_data='payment_doc')

del_doc = InlineKeyboardButton(
    "❌ Отмена документа", callback_data='del_doc')


wallets = InlineKeyboardButton(
    "👛 Кошельки", callback_data='wallets')

wallets_balance = InlineKeyboardButton(
    "💰 Баланс", callback_data='wallets_balance')

merge_wallets = InlineKeyboardButton(
    "➕ Объединить кошельки", callback_data='merge_wallets')

leave_wallets = InlineKeyboardButton(
    "➖ Покинуть кошелёк", callback_data='leave_wallet')


total = InlineKeyboardButton(
    "📋 Отчёт", callback_data='total')

menu_acc = InlineKeyboardMarkup().add(
    purchase_payment).add(wallets).add(total)

menu_docs = InlineKeyboardMarkup().add(purchase, payment_doc).add(del_doc)

menu_wallets = InlineKeyboardMarkup().add(wallets_balance).add(
    merge_wallets, leave_wallets)


def pay_lst(message: types.Message):
    change_card = InlineKeyboardMarkup()

    acc = server.get_current_accounting(user=message.chat.id)[0]
    lst_users = server.get_group_users(acc)[0]

    for x in lst_users:
        if x != message.chat.id:
            nic = server.user_name(x)[0]

            change_card.add(InlineKeyboardButton(
                text=f"{nic}", callback_data=pay_lst_callback.new(id=x)))
    return change_card


def merge_wallets_keyboard(message: types.Message, del_wallets=None):
    change_card = InlineKeyboardMarkup()

    acc = server.get_current_accounting(user=message.chat.id)[0]
    lst_wallets = server.others_wallets(acc, message.chat.id)[0]
    lst_wallets = list(lst_wallets)

    if del_wallets is not None:
        for wallet in del_wallets:
            lst_wallets.remove(int(wallet))

    for wallet in lst_wallets:
        wallet_name = server.wallet_name(wallet)[0]

        change_card.add(InlineKeyboardButton(
            text=f"{wallet_name}", callback_data=merge_wallets_callback.new(id=wallet)))
    change_card.add(InlineKeyboardButton(
        text=f"✅ Объединить", callback_data='accept_merge_wallets'))
    return change_card

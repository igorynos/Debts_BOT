from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


accept_to_leave = InlineKeyboardMarkup().add(InlineKeyboardButton(
    "Да", callback_data='accept_to_leave_yes')).add(InlineKeyboardButton(
        "Нет", callback_data='accept_to_leave_no'))

accept_to_change_name_wallet = InlineKeyboardMarkup().add(InlineKeyboardButton(
    "Да", callback_data='change_wallname_yes')).add(InlineKeyboardButton(
        "Нет", callback_data='change_wallname_no'))

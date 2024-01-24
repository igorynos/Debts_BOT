from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import types

from datetime import datetime

from loader import db, dp, server
from keyboards.inline.callback_data import accounting_callback


async def accounting_list_active(message: types.Message):
    result = server.accounting_list('ACTIVE')
    try:
        result = result[0]
    except:
        await message.answer("Не удалось получить данные")

    change_card = InlineKeyboardMarkup()
    for x in result:
        start_time = x['start_time']
        change_card.add(InlineKeyboardButton(
            text=f"{x['name']} - {start_time.strftime('%Y-%m-%d %H:%M:%S')}", callback_data=accounting_callback.new(id=x['id'])))
    change_card.add(InlineKeyboardButton(
        "➕ Создать новый", callback_data='new_accounting'))
    change_card.add(InlineKeyboardButton(
        "◀️ Отмена", callback_data='main_menu'))
    await message.answer("Активные расчёты:", reply_markup=change_card)


join_acc_1 = InlineKeyboardMarkup().add(InlineKeyboardButton(
    "🚪 Подключиться", callback_data='join_acc'))
join_acc_2 = InlineKeyboardMarkup().add(InlineKeyboardButton(
    "Да", callback_data='join_acc_yes'), InlineKeyboardButton(
    "Нет", callback_data='join_acc_no'))

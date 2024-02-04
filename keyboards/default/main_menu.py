from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from loader import dp

from data.config import ADMINS


def main_menu(message):
    main_menu_button_1 = KeyboardButton(
        text='Расчёты', callback_data='Расчёты')
    main_menu_button_2 = KeyboardButton(
        text='Активный расчёт', callback_data='Активный расчёт')
    main_menu_button_3 = KeyboardButton(
        text='Баланс', callback_data='Баланс')
    main_menu_keyboard_admin = ReplyKeyboardMarkup(
        resize_keyboard=True).add(main_menu_button_2).add(main_menu_button_1, main_menu_button_3)
    main_menu_keyboard_user = ReplyKeyboardMarkup(
        resize_keyboard=True).add(main_menu_button_2).add(main_menu_button_1, main_menu_button_3)
    if str(message.chat.id) in ADMINS:
        return main_menu_keyboard_admin
    else:
        return main_menu_keyboard_user

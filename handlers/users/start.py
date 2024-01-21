from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.dispatcher.storage import FSMContext
from .reg_user import register_new_user_1

from keyboards.default.main_menu import main_menu


from loader import dp, db


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message, state: FSMContext):
    sql = f"SELECT * FROM users WHERE id = '{message.from_user.id}';"
    result = db.execute(sql, fetchone=True)
    if result is None:
        await message.answer(f"Привет, {message.from_user.full_name}!")
        await register_new_user_1(message, state=state)
    else:
        await message.answer(f"Главное меню", reply_markup=main_menu(message=message))


@dp.callback_query_handler(text='main_menu')
async def back_to_main_menu(call: types.CallbackQuery):
    await call.message.answer(f"Главное меню", reply_markup=main_menu(message=call.message))

from loader import dp, server
from aiogram import types
from aiogram.dispatcher.storage import FSMContext

from keyboards.default.main_menu import main_menu


async def register_new_user_1(message: types.Message, state=FSMContext):
    await message.answer("НИК (до 16 символов):")
    await state.set_state('nic')


@dp.message_handler(state="nic")
async def name_acc(message: types.Message, state: FSMContext):
    nic = message.text
    await state.finish()
    try:
        server.reg_user(user_id=message.chat.id, nic=nic)
        await message.answer(
            f"Зарегистрирован новый пользователь {nic}", reply_markup=main_menu(message=message))
    except ValueError('Пользователь с таким id уже зарегистрирован'):
        await message.answer('Пользователь с таким id уже зарегистрирован')

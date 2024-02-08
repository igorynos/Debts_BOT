from loader import dp, server
from aiogram import types
from aiogram.dispatcher.storage import FSMContext

from keyboards.inline.callback_data import merge_wallets_callback
from keyboards.inline.menu_acc import merge_wallets_keyboard
from handlers.users.active_acc import active_acc


dict_wallets = {}
dict_dell_users = {}


@dp.callback_query_handler(text='merge_wallets')
async def merge_wallets(call: types.CallbackQuery):
    acc = server.get_current_accounting(call.message.chat.id)[0]
    user_wallet = server.my_wallet(
        acc_id=acc, user=call.message.chat.id)[0]
    dict_wallets[f'{call.message.chat.id}'] = [user_wallet]
    dict_dell_users[f'{call.message.chat.id}'] = []

    await call.message.answer(text='Выберите пользователей, с которыми хотите обьединить кошельки:', reply_markup=merge_wallets_keyboard(call.message))


@dp.callback_query_handler(merge_wallets_callback.filter())
async def merge_wallets2(call: types.CallbackQuery, callback_data: dict):
    acc = server.get_current_accounting(call.message.chat.id)[0]
    id = callback_data.get('id')

    user_wallet = server.my_wallet(
        acc_id=acc, user=id)[0]

    dict_wallets[f'{call.message.chat.id}'].append(user_wallet)
    dict_dell_users[f'{call.message.chat.id}'].append(id)
    await call.message.answer(text='Выберите пользователей, с которыми хотите обьединить кошельки:', reply_markup=merge_wallets_keyboard(call.message, dict_dell_users[f'{call.message.chat.id}']))


@dp.callback_query_handler(text='accept_merge_wallets')
async def new_wallets(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(text='Напишите название кошелька')
    await state.set_state('new_wallets_2')


@dp.message_handler(state='new_wallets_2')
async def new_wallets_2(message: types.Message, state: FSMContext):
    await state.finish()
    acc = server.get_current_accounting(user=message.chat.id)
    server.merge_wallets(
        acc_id=acc[0], wallets_list=dict_wallets[f'{message.chat.id}'], name=message.text)
    await message.answer(text=f'Кошелёк "{message.text}" создан')
    await active_acc(message)

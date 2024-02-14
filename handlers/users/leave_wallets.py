from loader import dp, server
from aiogram import types
from aiogram.dispatcher.storage import FSMContext

from keyboards.inline.leave_wallet import accept_to_leave, accept_to_change_name_wallet
from handlers.users.active_acc import active_acc


dict_user = {}


class ArgListUser:
    def __init__(self, user_id):
        self.user_id = user_id
        self.acc = server.get_current_accounting(user=user_id)[0]
        self.wallet = server.my_wallet(self.acc, user_id)[0]
        self.wallet_name = server.wallet_name(self.wallet)[0]
        self.wallet_users = server.wallet_users(
            self.acc, self.user_id, self.wallet)[0]


async def accept_leave_wallets(message: types.Message):
    user = dict_user[f"{message.chat.id}"]
    text = f'Отделить свой кошелек от кошелька {user.wallet_name}?'
    await message.answer(text=text, reply_markup=accept_to_leave)


@dp.callback_query_handler(text='leave_wallet')
async def start_leave_wallet(call: types.CallbackQuery):
    id = call.message.chat.id
    obj = ArgListUser(id)
    dict_user[f'{id}'] = obj
    await accept_leave_wallets(call.message)


async def accept_leave_wallets(message: types.Message):
    user = dict_user[f"{message.chat.id}"]
    text = f'Отделить свой кошелек от кошелька {user.wallet_name}?'
    await message.answer(text=text, reply_markup=accept_to_leave)


@dp.callback_query_handler(text='accept_to_leave_yes')
async def check_other_users(call: types.CallbackQuery):
    user = dict_user[f"{call.message.chat.id}"]
    if len(user.wallet_users) <= 2:
        server.leave_wallet(user.acc, user.user_id)
        await call.message.answer(text=f'Вы покинули {user.wallet_name}?', reply_markup=active_acc)
    else:
        await call.message.answer(text=f'Оставить прежнее название кошелька, из которого Вы выходите?\n"{user.wallet_name}"', reply_markup=accept_to_change_name_wallet)


@dp.callback_query_handler(text='accept_to_leave_no')
async def exit_leave_wallet(call: types.CallbackQuery):
    await active_acc(call.message)


@dp.callback_query_handler(text='change_wallname_yes')
async def leave_wallet_old_name(call: types.CallbackQuery):
    user = dict_user[f"{call.message.chat.id}"]
    server.leave_wallet(user.acc, user.user_id, user.wallet_name)
    await call.message.answer(text=f'Вы покинули {user.wallet_name}?')
    await active_acc(call.message)


@dp.callback_query_handler(text='change_wallname_no')
async def write_new_wallet_name(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(text=f'Напишите новое название')
    await state.set_state('leave_wallet_new_name')


@dp.message_handler(state='leave_wallet_new_name')
async def leave_wallet_new_name(message: types.Message, state: FSMContext):
    await state.finish()
    user = dict_user[f"{message.chat.id}"]
    server.leave_wallet(user.acc, user.user_id, message.text)
    await message.answer(text=f'Вы покинули кошелёк {user.wallet_name}\n\nКошелёк {message.text} создан')
    await active_acc(message)

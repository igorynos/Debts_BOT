from loader import dp, server
from aiogram import types
from aiogram.dispatcher.storage import FSMContext

from keyboards.inline.callback_data import merge_wallets_callback
from keyboards.inline.menu_acc import merge_wallets_keyboard
from handlers.users.active_acc import active_acc


@dp.callback_query_handler(text='leave_wallet')
async def leave_wallets(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(text='Напишите название вашего кошелька')
    await state.set_state('leave_wallet_2')


@dp.message_handler(state='leave_wallet_2')
async def leave_wallet_2(message: types.Message, state: FSMContext):
    await state.finish()
    acc = server.get_current_accounting(user=message.chat.id)[0]
    wallet = server.my_wallet(acc, message.chat.id)[0]
    wallet_name = server.wallet_name(wallet)[0]
    server.leave_wallet(acc, message.chat.id, message.text)
    await message.answer(text=f'Вы покинули кошелёк {wallet_name}\n\nКошелёк {message.text} создан')
    await active_acc(message)

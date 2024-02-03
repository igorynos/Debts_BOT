from loader import dp, db, server
from aiogram import types
from aiogram.dispatcher.storage import FSMContext

from handlers.users.active_acc import active_acc
from keyboards.inline.menu_acc import pay_lst
from keyboards.inline.callback_data import pay_lst_callback


@dp.callback_query_handler(text='payment_doc')
async def payment_doc(call: types.CallbackQuery):
    await call.message.answer(text='Выберете получателя', reply_markup=pay_lst(call.message))


@dp.callback_query_handler(pay_lst_callback.filter())
async def payment_doc2(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    id = callback_data.get('id')
    await state.update_data({'rec': id})
    await call.message.answer(text='Напишите сумму платежа')
    await state.set_state('payment_doc3')


@dp.message_handler(state='payment_doc3')
async def payment_doc3(message: types.Message, state: FSMContext):
    await state.update_data({'sum': message.text})
    await message.answer(text='Напишите коментарий к покупке')
    await state.set_state('payment_doc4')


@dp.message_handler(state='payment_doc4')
async def payment_doc4(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    acc_id = server.get_current_accounting(user=message.chat.id)
    acc_id = int(acc_id[0])
    payer = int(message.chat.id)
    rec = int(data['rec'])
    amount = float(data['sum'].replace(',', '.'))
    comment = message.text

    server.add_payment_doc(
        acc_id=acc_id, recipient=rec, payer=payer, amount=amount, comment=comment)
    nic = server.user_name(rec)[0]
    await message.answer(f'Перевод пользователю {nic} на сумму {amount} совершён')
    await active_acc(message)

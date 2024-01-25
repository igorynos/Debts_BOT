from loader import dp, db, server
from aiogram import types
from aiogram.dispatcher.storage import FSMContext

from handlers.users.active_acc import active_acc


@dp.callback_query_handler(text='purchase')
async def purchase(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(text='Напишите сумму покупки')
    await state.set_state('purchase2')


@dp.message_handler(state='purchase2')
async def purchase2(message: types.Message, state: FSMContext):
    await state.update_data({'sum': message.text})
    await message.answer(text='Напишите коментарий к покупке')
    await state.set_state('purchase3')


@dp.message_handler(state='purchase3')
async def purchase3(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    acc_id = server.get_current_accounting(user=message.chat.id)
    purch = message.chat.id
    amount = float(data['sum'].replace(',', '.'))
    comment = message.text

    server.add_purchase_doc(
        acc_id=acc_id[0], purchaser=purch, amount=amount, comment=comment)

    await message.answer(f'Покупка {comment} на сумму {amount} добавленна')
    await active_acc(message)

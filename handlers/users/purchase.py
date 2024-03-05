from loader import dp, server
from aiogram import types
from aiogram.dispatcher.storage import FSMContext

from handlers.users.active_acc import active_acc
from keyboards.inline.accept_beneficiaries import add_bnfcrs, accept_bnfcrs
from keyboards.inline.callback_data import bnfcrs_callback

dict_answer = {}
dict_bnfcrs = {}


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
async def purchase2(message: types.Message, state: FSMContext):
    await state.update_data({'comment': message.text})
    data = await state.get_data()
    data['bnfcr'] = None
    dict_answer[message.chat.id] = data
    await state.finish()
    await message.answer(text="Покупка сделана для всех участников расчета?", reply_markup=accept_bnfcrs)


@dp.callback_query_handler(text='accept_bnfcrs_no')
async def bnfcrs(call: types.CallbackQuery):
    data = dict_answer[call.message.chat.id]
    data['bnfcr'] = [call.message.chat.id,]

    await call.message.answer(text='Выберите участников, для которых сделана покупка:', reply_markup=add_bnfcrs(call.message))


@dp.callback_query_handler(bnfcrs_callback.filter())
async def choose_bnfcrs(call: types.CallbackQuery, callback_data: dict):
    bnfcrs_id = callback_data.get('id')
    data = dict_answer[call.message.chat.id]
    data['bnfcr'].append(int(bnfcrs_id))
    await call.message.answer(text='Выберите участников, для которых сделана покупка:', reply_markup=add_bnfcrs(call.message, data['bnfcr'][1:]))


@dp.callback_query_handler(text='accept_bnfcrs_next')
async def purchase3(call: types.CallbackQuery):
    data = dict_answer[call.message.chat.id]
    acc_id = server.get_current_accounting(user=call.message.chat.id)
    purch = call.message.chat.id
    try:
        amount = float(data['sum'].replace(',', '.'))
        comment = data['comment']
        bnfcr = data['bnfcr']
        if bnfcr is not None:
            bnfcr = server.beneficiaries(bnfcr)[0]
        result = await server.add_purchase_doc(
            acc_id=acc_id[0], purchaser=purch, amount=amount, comment=comment, bnfcr=bnfcr)
        print(result)
        if result[1] != 'OK':
            raise Exception
        await call.message.answer(f'Покупка {comment} на сумму {amount} добавлена')
    except:
        await call.message.answer(f'Произошла ошибка!\nПроверьте данные ввода')

    await active_acc(call.message)

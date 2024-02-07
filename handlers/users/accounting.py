from loader import dp, server
from aiogram import types
from aiogram.dispatcher.storage import FSMContext

from keyboards.inline.lst_accounting import accounting_list_active, join_acc_1, join_acc_2
from keyboards.inline.callback_data import accounting_callback
from handlers.users.active_acc import active_acc

dict_new_acc = {}
dict_acc_name = {}
dict_temp_acc = {}


@dp.callback_query_handler(text='create_new_accounting_cansel')
@dp.message_handler(text='Расчёты')
async def accounting(message, state: FSMContext):
    if type(message) == types.Message:
        await accounting_list_active(message)
    else:
        await accounting_list_active(message.message)


@dp.callback_query_handler(text='new_accounting')
async def new_accounting_name(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(text='Напишите название расчёта')
    await state.set_state('new_accounting_name')


@dp.message_handler(state='new_accounting_name')
async def create_new_accounting(message: types.Message, state: FSMContext):
    await state.finish()
    server.new_accounting(name=message.text, users=[message.chat.id,])
    await message.answer(text=f'Расчёт {message.text} создан')
    await active_acc(message)


@dp.callback_query_handler(accounting_callback.filter())
async def accounting(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    id = callback_data.get('id')
    dict_temp_acc[f"{call.message.chat.id}"] = id
    users = server.get_group_users(id)[0]
    name = server.accounting_name(id)[0]

    text = f'Расчёт {name}\n'
    for i, x in enumerate(users):
        nic = server.user_name(x)[0]
        text += f'\n{i+1}. {nic}'
    await call.message.answer(text=text, reply_markup=join_acc_1)


@dp.callback_query_handler(text='join_acc')
async def join_acc1(call: types.CallbackQuery, state: FSMContext):
    obj = server.check_user(
        acc_id=dict_temp_acc[f"{call.message.chat.id}"], user=call.message.chat.id)
    print(obj)
    if obj[1] == 'OK':
        server.set_current_accounting(
            acc_id=dict_temp_acc[f"{call.message.chat.id}"], user=call.message.chat.id)
        await active_acc(call.message)
    else:
        await call.message.answer(text='Учесть совершенные покупки?', reply_markup=join_acc_2)


@dp.callback_query_handler(text='join_acc_yes')
@dp.callback_query_handler(text='join_acc_no')
async def join_acc2(call: types.CallbackQuery, state: FSMContext):
    if call.data == "join_acc_yes":
        server.join_user(
            dict_temp_acc[f"{call.message.chat.id}"], call.message.chat.id, True)
    elif call.data == "join_acc_no":
        server.join_user(
            dict_temp_acc[f"{call.message.chat.id}"], call.message.chat.id, False)
    await active_acc(call.message)

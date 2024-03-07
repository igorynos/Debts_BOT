from loader import dp, server, bot
from aiogram import types
from keyboards.inline.del_docs import delete_docs, accept_delete_docs, choise_docs_to_del
from keyboards.inline.callback_data import del_docs_callback
from handlers.users.active_acc import active_acc

dict_del_doc = {}


@dp.callback_query_handler(text='del_doc')
async def del_doc(call: types.CallbackQuery):
    await bot.send_message(chat_id=call.message.chat.id, text='Какой документ вы хотите удалить?', reply_markup=delete_docs)


@dp.callback_query_handler(text='del_docs_purch')
@dp.callback_query_handler(text='del_docs_pay')
async def del_doc(call: types.CallbackQuery):
    user_id = call.message.chat.id
    if call.data == 'del_docs_purch':
        doc_type = 'purchase'
        user_type = 'purchaser'
    else:
        doc_type = 'payment'
        user_type = 'payer'

    acc = server.get_current_accounting(user_id)[0]
    query = f"SELECT id, comment, amount, time FROM {doc_type}_docs WHERE accounting_id = {acc} AND {user_type} = {user_id}"
    result = server.execute(query, fetchall=True)[0]
    await bot.send_message(chat_id=user_id, text='Выберите документ', reply_markup=choise_docs_to_del(call.message, result, doc_type))


@dp.callback_query_handler(del_docs_callback.filter())
async def accept_del_docs(call: types.CallbackQuery, callback_data: dict):
    dict_del_doc[call.message.chat.id] = callback_data
    doc_type = callback_data.get('doc_type')
    doc_id = callback_data.get('id')
    query = f"SELECT comment, amount FROM {doc_type}_docs WHERE id = {doc_id}"
    result = server.execute(query, fetchone=True)[0]
    await call.message.answer(f"Вы действительно хотите удалить документ '{result['comment']} - {result['amount']}'?", reply_markup=accept_delete_docs)


@dp.callback_query_handler(text='del_yes')
@dp.callback_query_handler(text='del_no')
async def del_docs(call: types.CallbackQuery):
    if call.data == 'del_yes':
        data = dict_del_doc[call.message.chat.id]
        doc_id = data['id']
        doc_type = data['doc_type']
        await call.message.answer(f"Документ удалён")
        await server.del_doc(doc_id=doc_id, doc_type=doc_type)
        await active_acc(call.message)
    else:
        dict_del_doc[call.message.chat.id] = None
        await active_acc(call.message)

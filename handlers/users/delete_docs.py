from loader import dp, server, bot
from aiogram import types
from keyboards.inline.del_docs import delete_docs, choise_docs_to_del
from keyboards.inline.callback_data import del_docs_callback


@dp.callback_query_handler(text='del_doc')
async def del_doc(call: types.CallbackQuery):
    await bot.send_message(chat_id=call.message.chat.id, text='Какой документ вы хотите удалить?', reply_markup=delete_docs)


@dp.callback_query_handler(text='del_docs_purch')
@dp.callback_query_handler(text='del_docs_pay')
async def del_doc(call: types.CallbackQuery):
    user_id = call.message.chat.id
    if call.data == 'del_docs_purch':
        doc_type = 'purchase'
    else:
        doc_type = 'payment'

    acc = server.get_current_accounting(user_id)[0]
    query = f"SELECT id, comment, amount, time FROM {doc_type}_docs WHERE accounting_id = {acc}"
    result = server.execute(query, fetchall=True)[0]
    await bot.send_message(chat_id=user_id, text='Выберите документ', reply_markup=choise_docs_to_del(call.message, result, doc_type))


@dp.callback_query_handler(del_docs_callback.filter())
async def del_docs(call: types.CallbackQuery, callback_data: dict):
    doc_id = callback_data.get('id')
    doc_type = callback_data.get('doc_type')

    await server.del_doc(doc_id=doc_id, doc_type=doc_type)

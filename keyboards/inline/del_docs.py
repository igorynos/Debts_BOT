from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from keyboards.inline.callback_data import del_docs_callback

delete_docs = InlineKeyboardMarkup().add(InlineKeyboardButton(
    "Покупки", callback_data='del_docs_purch'), InlineKeyboardButton(
        "Платежи", callback_data='del_docs_pay'))

accept_delete_docs = InlineKeyboardMarkup().add(InlineKeyboardButton(
    "Да", callback_data='del_yes'), InlineKeyboardButton(
        "Нет", callback_data='del_no'))


def choise_docs_to_del(message, lst_docs, doc_type):
    choise_docs = InlineKeyboardMarkup()

    for doc in lst_docs:
        text = f"{doc['comment']} - {doc['amount']}   {doc['time']}"
        choise_docs.add(InlineKeyboardButton(
            text=text, callback_data=del_docs_callback.new(id=doc['id'], doc_type=doc_type)))
    return choise_docs

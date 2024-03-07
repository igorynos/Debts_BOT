import asyncio
import debts_server


def check_accounting(func):
    def wrap(*args, **kwargs):
        self = args[0]
        try:
            if self.accounting is None:
                self.accounting = self.choose_accounting()
            if self.accounting is None:
                return
            return func(*args, **kwargs)
        except Exception as ex:
            print(ex)
    return wrap


def acheck_accounting(func):
    async def wrap(*args, **kwargs):
        self = args[0]
        try:
            if self.accounting is None:
                self.accounting = self.choose_accounting()
            if self.accounting is None:
                return
            return await func(*args, **kwargs)
        except Exception as ex:
            print(ex)
    return wrap


def result(res):
    if isinstance(res, tuple):
        if res[1] != 'OK':
            print(res[1])
        return res[0]


class DebtsCLI(object):
    def __init__(self):
        self.accounting = None
        self.server = debts_server.DebtsServer(self.message_cbs)

    @acheck_accounting
    async def purchase(self):
        print('Документ "Покупка"')
        usr = int(input("покупатель: "))
        amnt = int(input("сумма: "))
        cmnt = input("комментарий: ")
        if not result(await self.server.add_purchase_doc(self.accounting, usr, amnt, bnfcr=None, comment=cmnt)):
            print('Документ не добавлен')

    @acheck_accounting
    async def add_payment(self):
        print('Документ "Платеж"')
        pyr = int(input("плательщик: "))
        rcpnt = int(input("получатель: "))
        amnt = int(input("сумма: "))
        cmnt = input("комментарий: ")
        if not result(await self.server.add_payment_doc(self.accounting, pyr, rcpnt, amnt, comment=cmnt)):
            print('Документ не добавлен')

    @acheck_accounting
    async def cancel_doc(self):
        print('Отменить документ\n  1: покупки\n  2: платежа')
        doc_type = int(input("выберите тип документа: "))
        if doc_type == 1:
            query = ("SELECT id, time, purchaser, comment, amount "
                     "FROM purchase_docs "
                     "WHERE accounting_id = %s")
            doc_type = 'purchase'
        elif doc_type == 2:
            query = ("SELECT id, time, payer, recipient, comment, amount "
                     "FROM payment_docs "
                     "WHERE accounting_id = %s")
            doc_type = 'payment'
        else:
            print('Неверный тип документа')
            return
        docs = result(self.server.execute(query, self.accounting, fetchall=True))
        for doc in docs:
            if doc_type == 'purchase':
                print(f"{doc['id']:06} от {str(doc['time'])[:-3]}: {doc['purchaser']}   "
                      f"'{doc['comment']}'    {doc['amount']}")
            else:
                print(f"{doc['id']:06} от {str(doc['time'])[:-3]}: {doc['payer']} -> {doc['recipient']}   "
                      f"'{doc['comment']}'    {doc['amount']}")
        doc_id = int(input("ведите номер документа: "))
        result(await self.server.del_doc(doc_id, doc_type))

    def reg_user(self):
        print('Регистрация нового пользователя')
        nic = input("ник (до 16 символов): ")
        user_id = int(input("id: "))
        result(self.server.reg_user(user_id, nic))

    @acheck_accounting
    async def join_user(self):
        usr = int(input("присоединить пользователя: "))
        if usr == 0:
            return
        recalc = input("учесть совершенные покупки? д/н (y/n)").lower()[:1] in ('д', 'y')
        result(await self.server.join_user(self.accounting, usr, recalc))

    def choose_accounting(self):
        accountings = result(self.server.accounting_list('ACTIVE'))
        if accountings is None:
            return
        print('Активные расчеты:')
        for acc in accountings:
            print(f"{acc['id']}\t'{acc['name']}'  начало: {acc['start_time']}")
        accounting_id = int(input('Введите номер расчета. 0 - чтобы создать новый  '))

        if accounting_id == 0:
            name = input("Введите имя для нового расчета: ")
            cursor = self.server.connection.cursor()
            print("В системе зарегиспрированы пользователи:")
            cursor.execute("SELECT id, user_nic FROM users")
            users = cursor.fetchall()
            for user in users:
                print(f"{user['id']}:  {user['user_nic']}")
            user_list = list(map(int, input("Перечислите через запятую ID участников расчета: ").split(',')))
            accounting_id = result(self.server.new_accounting(name, user_list))
            if accounting_id is None:
                return

        accountings = result(self.server.accounting_list('ACTIVE'))
        if accountings is None:
            return
        for acc in accountings:
            if acc['id'] == accounting_id:
                return accounting_id
        print('Неверный номер расчета')
        return

    @check_accounting
    async def merge_wallets(self):
        print("В системе зарегиспрированы кошельки:")
        wallets = result(self.server.get_wallet_balance(self.accounting))
        for wallet in wallets:
            print(f"{wallet['id']}: {wallet['name']}")
        wallets_list = list(map(int, input("Перечислите через запятую номера объединяемых кошельков: ").split(',')))
        result(await self.server.merge_wallets(self.accounting, wallets_list))

    @check_accounting
    async def leave_wallet(self):
        cursor = self.server.connection.cursor()
        cursor.execute("SELECT id, user_nic FROM users")
        users = cursor.fetchall()
        for user in users:
            print(f"{user['id']}:  {user['user_nic']}")
        user = int(input("Выберите ID пользователя: "))
        result(await self.server.leave_wallet(self.accounting, user))

    @check_accounting
    def show_balance(self):
        balance = result(self.server.get_wallet_balance(self.accounting))
        if balance is None:
            return
        for blnc in balance:
            print(f"{blnc['id']} {blnc['name']}  -  {blnc['balance']}")

    @check_accounting
    def show_wallets(self):
        wallets = result(self.server.wallet_balances(self.accounting))
        if wallets is None:
            return
        for name in wallets.keys():
            print(f"{name}:    {wallets[name]}")

    @check_accounting
    def my_wallet(self):
        usr = int(input("пользователь: "))
        print(f"{result(self.server.my_wallet(self.accounting, usr))}")

    @check_accounting
    def others_wallets(self):
        usr = int(input("пользователь: "))
        print(f"{result(self.server.others_wallets(self.accounting, usr))}")

    @check_accounting
    def report(self):
        if self.accounting is None:
            return
        if result(self.server.total_report(self.accounting)) is None:
            return

    def close_accounting(self):
        if self.accounting is None:
            return
        if result(self.server.close_accounting(self.accounting)) is None:
            return
        self.accounting = None

    @staticmethod
    async def message_cbs(user, msg):
        print(msg)
        print(user)

    async def run(self):
        while True:
            cmd = input('Ведите команду: ')
            if cmd.lower()[:3] in ('hel', 'пом'):
                print('зарегистрировать (register)    - зарегистрировать нового пользователя \n'
                      'присоединить (join)            - присоединить пользователя к расчету \n' 
                      'расчет (accounting)            - выбрать или создать расчет \n'
                      'покупка (purchase)             - создать документ "Покупка" \n'
                      'платеж (payment)               - создать документ "Платеж" \n'
                      'отмена (cancel)                - отменить документ \n'
                      'баланс (balance)               - посмотреть текущий баланс \n'
                      'кошельки (wallets)             - посмотреть баланс всех кошельков \n'
                      'объединить (merge)             - объединить кошельки \n'
                      'мой (my)                       - посмотреть идентификатор моего кошелька \n'
                      'чужие (others)                 - посмотреть идентификаторы чужих кошельков \n'
                      'выйти (leave)                  - выйти из кошелька \n'
                      'отчет (report)                 - отчет по расчету \n'
                      'закрыть (close)                - закрыть расчет \n'
                      'выход (exit)                   - завершить программу')
            elif cmd.lower()[:3] in ('зар', 'рег', 'reg'):
                self.reg_user()
            elif cmd.lower()[:3] in ('при', 'joi'):
                await self.join_user()
            elif cmd.lower()[:3] in ('рас', 'acc'):
                self.accounting = self.choose_accounting()
            elif cmd.lower()[:3] in ('объ', 'mer'):
                await self.merge_wallets()
            elif cmd.lower()[:3] in ('пок', 'pur'):
                await self.purchase()
            elif cmd.lower()[:3] in ('пла', 'pay'):
                await self.add_payment()
            elif cmd.lower()[:3] in ('отм', 'can'):
                await self.cancel_doc()
            elif cmd.lower()[:3] in ('бал', 'bal'):
                self.show_balance()
            elif cmd.lower()[:3] in ('кош', 'wal'):
                self.show_wallets()
            elif cmd.lower()[:3] == 'мой' or cmd.lower()[:2] == 'my':
                self.my_wallet()
            elif cmd.lower()[:3] in ('чуж', 'oth'):
                self.others_wallets()
            elif cmd.lower()[:3] in ('вый', 'lea'):
                await self.leave_wallet()
            elif cmd.lower()[:3] in ('отч', 'rep'):
                self.report()
            elif cmd.lower()[:3] in ('зак', 'clo'):
                self.close_accounting()
            elif cmd.lower()[:3] in ('вых', 'exi'):
                break
            elif cmd.lower()[:3] in ('set',):
                self.server.set_current_accounting(None, 1)
                print(result(self.server.get_current_accounting(1)))
            else:
                print('Неизвестная команда')


if __name__ == '__main__':
    cli = DebtsCLI()
    asyncio.run(cli.run())

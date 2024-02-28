import asyncio
import debts_server

accounting = None


def check_accounting(func):
    def wrap(*args, **kwargs):
        global accounting
        try:
            if accounting is None:
                accounting = choose_accounting()
                if accounting is None:
                    return
                return func(*args, **kwargs)
        except Exception as ex:
            print(ex)
            return
    return wrap


def acheck_accounting(func):
    async def aNone():
        pass

    async def wrap(*args, **kwargs):
        global accounting
        try:
            if accounting is None:
                accounting = choose_accounting()
                if accounting is None:
                    return await aNone()
                return await func(*args, **kwargs)
        except Exception as ex:
            print(ex)
            return await aNone()

    return wrap


def result(res):
    if isinstance(res, tuple):
        if res[1] != 'OK':
            print(res[1])
        return res[0]


@acheck_accounting
async def purchase():
    global server, accounting
    print('Документ "Покупка"')
    usr = int(input("покупатель: "))
    amnt = int(input("сумма: "))
    cmnt = input("комментарий: ")
    doc = asyncio.create_task(server.add_purchase_doc(accounting, usr, amnt, bnfcr=None, comment=cmnt))
    res = await doc
    if not (result(res)):
        print('Документ не добавлен')


@acheck_accounting
async def add_payment():
    global server, accounting
    print('Документ "Платеж"')
    pyr = int(input("плательщик: "))
    rcpnt = int(input("получатель: "))
    amnt = int(input("сумма: "))
    cmnt = input("комментарий: ")
    if not result(await server.add_payment_doc(accounting, pyr, rcpnt, amnt, comment=cmnt)):
        print('Документ не добавлен')


def reg_user():
    global server, accounting
    print('Регистрация нового пользователя')
    nic = input("ник (до 16 символов): ")
    user_id = int(input("id: "))
    result(server.reg_user(user_id, nic))


@check_accounting
def join_user():
    global server, accounting
    usr = int(input("присоединить пользователя: "))
    if usr == 0:
        return
    recalc = input("учесть совершенные покупки? д/н (y/n)").lower()[:1] in ('д', 'y')
    result(server.join_user(accounting, usr, recalc))


def choose_accounting():
    global server, accounting
    accountings = result(server.accounting_list('ACTIVE'))
    if accountings is None:
        return
    print('Активные расчеты:')
    for acc in accountings:
        print(f"{acc['id']}\t'{acc['name']}'  начало: {acc['start_time']}")
    accounting_id = int(input('Введите номер расчета. 0 - чтобы создать новый  '))

    if accounting_id == 0:
        name = input("Введите имя для нового расчета: ")
        cursor = server.connection.cursor()
        print("В системе зарегиспрированы пользователи:")
        cursor.execute("SELECT id, user_nic FROM users")
        users = cursor.fetchall()
        for user in users:
            print(f"{user['id']}:  {user['user_nic']}")
        user_list = list(map(int, input("Перечислите через запятую ID участников расчета: ").split(',')))
        accounting_id = result(server.new_accounting(name, user_list))
        if accounting_id is None:
            return

    accountings = result(server.accounting_list('ACTIVE'))
    if accountings is None:
        return
    for acc in accountings:
        if acc['id'] == accounting_id:
            return accounting_id
    print('Неверный номер расчета')
    return


@check_accounting
def merge_wallets():
    global server, accounting
    print("В системе зарегиспрированы кошельки:")
    wallets = result(server.get_wallet_balance(accounting))
    for wallet in wallets:
        print(f"{wallet['id']}: {wallet['name']}")
    wallets_list = list(map(int, input("Перечислите через запятую номера объединяемых кошельков: ").split(',')))
    result(server.merge_wallets(accounting, wallets_list))


@check_accounting
def leave_wallet():
    global server, accounting
    cursor = server.connection.cursor()
    cursor.execute("SELECT id, user_nic FROM users")
    users = cursor.fetchall()
    for user in users:
        print(f"{user['id']}:  {user['user_nic']}")
    user = int(input("Выберите ID пользователя: "))
    server.leave_wallet(accounting, user)


@check_accounting
def show_balance():
    global server, accounting
    balance = result(server.get_wallet_balance(accounting))
    if balance is None:
        return
    for blnc in balance:
        print(f"{blnc['id']} {blnc['name']}  -  {blnc['balance']}")


@check_accounting
def show_wallets():
    global server, accounting
    wallets = result(server.wallet_balances(accounting))
    if wallets is None:
        return
    for name in wallets.keys():
        print(f"{name}:    {wallets[name]}")


@check_accounting
def my_wallet():
    global server, accounting
    usr = int(input("пользователь: "))
    print(f"{result(server.my_wallet(accounting, usr))}")


@check_accounting
def others_wallets():
    global server, accounting
    usr = int(input("пользователь: "))
    print(f"{result(server.others_wallets(accounting, usr))}")


@check_accounting
def report():
    global server, accounting
    if accounting is None:
        return
    if result(server.total_report(accounting)) is None:
        return


def close_accounting():
    global server, accounting
    if accounting is None:
        return
    if result(server.close_accounting(accounting)) is None:
        return
    accounting = None


async def message_cbs(user, msg):
    print(msg)
    print(user)


async def main():
    global server, accounting
    server = debts_server.DebtsServer(message_cbs)

    while True:
        cmd = input('Ведите команду: ')
        if cmd.lower()[:3] in ('hel', 'пом'):
            print('зарегистрировать (register)    - зарегистрировать нового пользователя \n'
                  'присоединить (join)            - присоединить пользователя к расчету \n' 
                  'расчет (accounting)            - выбрать или создать расчет \n'
                  'покупка (purchase)             - создать документ "Покупка" \n'
                  'платеж (payment)               - создать документ "Платеж" \n'
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
            reg_user()
        elif cmd.lower()[:3] in ('при', 'joi'):
            join_user()
        elif cmd.lower()[:3] in ('рас', 'acc'):
            accounting = choose_accounting()
        elif cmd.lower()[:3] in ('объ', 'mer'):
            merge_wallets()
        elif cmd.lower()[:3] in ('пок', 'pur'):
            await purchase()
        elif cmd.lower()[:3] in ('пла', 'pay'):
            await add_payment()
        elif cmd.lower()[:3] in ('бал', 'bal'):
            show_balance()
        elif cmd.lower()[:3] in ('кош', 'wal'):
            show_wallets()
        elif cmd.lower()[:3] == 'мой' or cmd.lower()[:2] == 'my':
            my_wallet()
        elif cmd.lower()[:3] in ('чуж', 'oth'):
            others_wallets()
        elif cmd.lower()[:3] in ('вый', 'lea'):
            leave_wallet()
        elif cmd.lower()[:3] in ('отч', 'rep'):
            report()
        elif cmd.lower()[:3] in ('зак', 'clo'):
            close_accounting()
        elif cmd.lower()[:3] in ('вых', 'exi'):
            break
        elif cmd.lower()[:3] in ('set',):
            server.set_current_accounting(None, 1)
            print(result(server.get_current_accounting(1)))
        else:
            print('Неизвестная команда')

if __name__ == '__main__':
    asyncio.run(main())


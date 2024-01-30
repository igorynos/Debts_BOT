import pymysql
import configparser
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

from data import config


def try_and_log(msg):
    """
    Декоратор выполняет метод класса.
    При возникновения исключения выводит в лог два сообщения
    с текстом, который передается в декоратор как аргумент,
    и с текстом исключения.

    Возвращает кортеж из двух элементов:
    Если было исключение - None и описание ошибки msg;
    если не было - объект, возвращаемый методом, и 'OK'
    Args:
        msg (str): текст выводимый в лог при возникновении исключения
    """

    def dcrtr(func):
        def wrap(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs), 'OK'
            except Exception as ex:
                dtl_msg = f"{msg}: {ex}"
                self.logger.error(dtl_msg)
                return None, dtl_msg

        return wrap

    return dcrtr


def result(res):
    """
    Извлекает результат выполнения функции из кортежа, созданного декоратором try_and_log.
    Если выполнение функции не было успешным, генерирует исключение.
    Args:
        res (tuple): кортеж, возвращаемый декоратором try_and_log
    Raises:
        Exception: Исключение обработанное декориратором try_and_log
    Returns:
        Any: Результат возвращаемый декорируемой функцией
    """
    if res[1] != 'OK':
        raise Exception(res[1])
    return res[0]


# noinspection PyTypeChecker
class DebtsServer(object):
    """
    Класс осуществляет подключение к базе данных
    и содержит методы для работы с пользователями и расчетами
    """

    def __init__(self):
        """
        Инициализация DebtsServer. \n
        Параметры БД считывает из файла debts.ini \n
        Запускает вывод в лог Logs/debts.log.

        """
        self.__shutdown = False

        self.logger = logging.getLogger('debts')
        if not os.path.isdir("Logs"):
            os.mkdir("Logs")
        self.logger_handler = TimedRotatingFileHandler('Logs/debts.log', encoding='utf-8', when='midnight',
                                                       backupCount=30)
        self.logger.addHandler(self.logger_handler)
        self.logger.setLevel(logging.DEBUG)
        self.logger.info(
            "\n****************************************************\n")
        self.logger_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s]:  %(message)s'))
        self.logger.info('Запуск приложения "Долговая книга')

        self.cfg = configparser.ConfigParser()
        # noinspection PyBroadException
        try:
            self.host = config.IP
            self.port = config.PORT
            self.database = config.DATABASE
            # self.cfg.read('debts.ini')
            # self.host = self.cfg['DB']['address']
            # self.port = int(self.cfg['DB']['port'])
            # self.database = self.cfg['DB']['database']
        except Exception:
            # if 'DB' not in self.cfg.sections():
            #     self.cfg.add_section('DB')
            self.host = 'yar.diskstation.me'
            self.port = 13306
            self.database = 'bot_debts'
            # # self.cfg['DB']['address'] = config.IP
            # # self.cfg['DB']['port'] = config.PORT
            # # self.cfg['DB']['database'] = config.DATABASE
            # self.cfg['DB']['address'] = self.host
            # self.cfg['DB']['port'] = str(self.port)
            # self.cfg['DB']['database'] = self.database
            # with open('debts.ini', 'w') as configfile:
            #     self.cfg.write(configfile)

        self.connection = None
        self.logger.info(f'Подключение к базе данных {self.database} '
                         f'на сервере {self.host}{f":{self.port}" if self.port != 3306 else ""}')
        try:
            # noinspection PyUnresolvedReferences
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user='bot',
                password='F28-cjr8s]bg!2eE',
                database=self.database,
                cursorclass=pymysql.cursors.DictCursor
            )
            self.logger.info('Подключение выполнено успешно')
        except pymysql.err.OperationalError:
            self.logger.error('Невозможно подключиться к базе данных')

    @try_and_log('Ошибка регистрации пользователя')
    def reg_user(self, user_id, nic):
        """
        Регистрирует пользователя в системе (cоздает запись в таблице users) \n
        Телефон является уникальным атрибутом.
        Если пользователь с таким телефоном уже зарегистрирован, возвращает ошибку
        Args:
            user_id (int):   уникальный идентификатор пользователя
            nic (str): ник пользователя
        Returns:
            int: идентификатор пользователя
        """
        with self.connection.cursor() as cursor:
            self.logger.info(f'Регистрация')
            self.logger.info(f'id={user_id}, nic="{nic}"')
            query = "SELECT id FROM users WHERE id = %s"
            self.logger.info(f'query={query}"')
            cursor.execute(query, user_id)
            if cursor.fetchone() is not None:
                raise ValueError('Пользователь с таким id уже зарегистрирован')
            query = "INSERT INTO users (id, user_nic) VALUES (%s, %s)"
            self.logger.info(f'query={query}"')
            cursor.execute(query, [user_id, nic])
            self.connection.commit()
            self.logger.info(
                f"Зарегистрирован новый пользователь {nic} (id: {user_id})")

    @try_and_log('Ошибка при создании новой группы пользователей')
    def new_group(self, accounting, users):
        """
        Метод создает новую группу пользователей для выбранного расчета
        Args:
            accounting (int): ID расчета в БД accountings.id
            users (int): ID пользователя в БД users.id
        Returns:
            int: ID группы пльзователей в БД groups.id
        """
        with self.connection.cursor() as cursor:
            # Создаем для нового расчета новую группу
            query = "INSERT INTO groups (accounting_id, user_id) VALUES " + \
                    ", ".join(["(%s, %s)"] * len(users))
            args = [[accounting, user][i] for user in users for i in range(2)]
            cursor.execute(query, args)
            self.connection.commit()
            cursor.execute('SELECT LAST_INSERT_ID() AS id')
            group_id = cursor.fetchone()['id']
            self.logger.info(f"Создана новая группа {group_id} для расчета {accounting}. "
                             f"Участники: {', '.join(map(str, users))}")
            return id

    @try_and_log('Ошибка создания нового кошелька')
    def new_wallet(self, user, wallet_name=None):
        """
        Создает в базе данных новый кошелек для одного пользователя
        Args:
            user (int): ID пользователя в БД users.id
            wallet_name (str, optional): Имя кошелька. По умолчанию: ник пользователя.
        Returns:
            int: ID кошелька в БД wallet_balance.id
        """
        with self.connection.cursor() as cursor:
            if wallet_name is None:
                cursor.execute(
                    "SELECT user_nic FROM users WHERE id = %s", user)
                wallet_name = cursor.fetchone()['user_nic']
            cursor.execute(
                "INSERT INTO wallet_balance (balance, name) VALUES (0, %s)", wallet_name)
            self.connection.commit()
            cursor.execute('SELECT LAST_INSERT_ID() AS id')
            self.logger.info(f"Создан новый кошелек {wallet_name}")
            return cursor.fetchone()['id']

    @try_and_log('Ошибка присвоения пользователям кошельков')
    def assign_wallet(self, accounting, users, wallets):
        """
        Присваивает пользователям из сиска users кошельки из списка wallets
        Args:
            accounting (int): ID расчета в БД accountings.id
            users (list(int)): Список идентификаторов пользователей
            wallets (list(int)): Список идентификаторов кошельков
        """
        if isinstance(users, int):
            users = [users]
            wallets = [wallets]
        with self.connection.cursor() as cursor:
            query = "INSERT INTO wallets (user_id, accounting_id, wallet) VALUES " + \
                    ", ".join(["(%s, %s, %s)"] * len(users))
            args = [[users[i], accounting, wallets[i]][j]
                    for i in range(len(users)) for j in range(3)]
            cursor.execute(query, args)
            self.connection.commit()
            self.logger.info(f"Участникам {', '.join(map(str, users))} "
                             f"присвоены кошельки {', '.join(map(str, wallets))}")

    @try_and_log('Ошибка при создании нового расчета')
    def new_accounting(self, name, users):
        """
        Создает новый расчет и новую группу пользователей
        Args:
            name (str): Название расчета
            users (list): Список идентификаторов пользователей данного расчета
        Raises:
            Exception: Вызывается если при создании новая группа не была создана
        Returns:
            int: ID идентификатор расчета в БД accountins.id
        """
        with self.connection.cursor() as cursor:
            query = "INSERT INTO accountings (name, start_time) " \
                    "VALUES (%s,  NOW())"
            cursor.execute(query, name)
            self.connection.commit()
            cursor.execute('SELECT LAST_INSERT_ID() AS id')
            accounting_id = cursor.fetchone()['id']
            self.logger.info(f"Создан новый расчет {accounting_id} '{name}'")
            result(self.new_group(accounting_id, users))
            query = "INSERT INTO user_balance (user_id, accounting_id, balance) VALUES " + \
                    ", ".join(["(%s, %s, %s)"] * len(users))
            args = [[user, accounting_id, 0][i]
                    for user in users for i in range(3)]
            cursor.execute(query, args)
            self.connection.commit()
            self.logger.info(
                f"К расчету {accounting_id} добавлены участники {', '.join(map(str, users))}")
            wallets = []
            for user in users:
                wallets.append(result(self.new_wallet(user)))
                result(self.set_current_accounting(accounting_id, user))
            result(self.assign_wallet(accounting_id, users, wallets))
            return accounting_id

    @try_and_log('Ошибка получения списка расчетов')
    def accounting_list(self, status):
        """
        Получает из БД и возвращает список расчетов
        Args:
            status (str): статус выводимых расчетов
                'ACTIVE' - выводятся только активные расчеты \n
                'ARCHIVE' - выводятся только закрытые расчеты \n
                'ALL' - ыводятся все расчеты
        Returns:
            list: Список расчетов с заданным статусом.
            Каждый расчет в списке возвращаятся в виде словаря с ключами:
                `id` идентификатор \n
                `name` - название расчета \n
                `start_time` время открытия \n
                `end_time` время закрыимя

        """
        with self.connection.cursor() as cursor:
            query = "SELECT * FROM accountings "
            if status.upper() == 'ACTIVE':
                query += "WHERE start_time IS NOT NULL AND end_time IS NULL"
            elif status.upper() == 'ARCHIVE':
                query += "WHERE end_time IS NOT NULL"
            cursor.execute(query)
            return cursor.fetchall()

    @try_and_log('Ошибка при создании нового множества бенефициаров')
    def new_beneficiaries(self, users):
        """
        Создает новое множество бенефициаров
        Args:
            users (list): Список пользователей входящих в множество бенефициаров
        Returns:
            int: ID множества бенефициаров в БД beneficiaries.bnfcr_group
        """
        with self.connection.cursor() as cursor:
            # Вычисление номера для новой группы
            cursor.execute("SELECT MAX(bnfcr_group) FROM beneficiaries")
            new_bnfcr_group = cursor.fetchone()['MAX(bnfcr_group)']
            if new_bnfcr_group is None:
                new_bnfcr_group = 1
            else:
                new_bnfcr_group += 1
            query = "INSERT INTO beneficiaries (bnfcr_group, user_id) VALUES " + \
                    ", ".join(["(%s, %s)"] * len(users))
            args = [[new_bnfcr_group, user][i]
                    for user in users for i in range(2)]
            cursor.execute(query, args)
            self.connection.commit()
            self.logger.info(f"Создано новое множество бенефициаров {new_bnfcr_group}. "
                             f"Участники: {', '.join(map(str, users))}")
            return new_bnfcr_group

    @try_and_log('Ошибка получения идентификатора множества бенефициаров')
    def beneficiaries(self, users):
        """
        Ищет в БД и возвращает идентификатор множества бенефициаров. При необходимости создает новое множество
        Args:
            users (list): Список пользователей (бенефициаров)
        Returns:
            int: Идентификатор множества в БД beneficiaries.bnfcr_group
        """
        with self.connection.cursor() as cursor:
            query = "SELECT DISTINCT bnfcr_group FROM beneficiaries"
            cursor.execute(query)
            bnfcr_set = set(map(lambda x: x['bnfcr_group'], cursor.fetchall()))
            if len(bnfcr_set) == 0:
                return result(self.new_beneficiaries(users))
            for user in users:
                query = "SELECT bnfcr_group FROM beneficiaries " \
                        "WHERE user_id = %s"
                cursor.execute(query, user)
                bnfcr_set &= set(
                    map(lambda x: x['bnfcr_group'], cursor.fetchall()))
                if len(bnfcr_set) == 0:
                    return result(self.new_beneficiaries(users))
            else:
                for bs in bnfcr_set:
                    query = "SELECT count(id) AS len FROM beneficiaries " \
                            "WHERE bnfcr_group = %s"
                    cursor.execute(query, bs)
                    l1 = len(users)
                    l2 = cursor.fetchone()['len']
                    if l1 == l2:
                        return bs
                else:
                    return result(self.new_beneficiaries(users))

    @try_and_log("Ошибкаchar")
    def free_users(self, acc_id):
        pass

    @try_and_log("Ошибка закрытия расчета")
    def close_accounting(self, acc_id):

        """
        Закрывает заданный расчет. \n
        Если в нем ненулевой баланс (более одного рубля), вызывается исключение
        Args:
            acc_id (int): идентификатор расчета accountings.id
        Raises:
            Exception: Если баланс ненулевой
        """
        balance = result(self.get_wallet_balance(acc_id))
        for blnc in balance:
            if abs(blnc['balance']) >= 1:
                raise Exception(
                    'Невозможно закрыть расчет с ненулевым балансом')
        with self.connection.cursor() as cursor:
            query = "UPDATE accountings SET end_time = NOW()" \
                    "WHERE id = %s"
            cursor.execute(query, acc_id)
            self.connection.commit()
            self.logger.info(f"расчет {acc_id} закрыт")

    @try_and_log('Ошибка получения списка участников расчета')
    def get_group_users(self, acc_id):
        """
        Возвращает кортеж идентификаторов пользователей, учавствующих в заданном расчете
        Args:
            acc_id (int): идентификатор расчета accountings.id
        Returns:
            tuple: кортеж идентификаторов пользователей
        """
        with self.connection.cursor() as cursor:
            query = "SELECT user_id FROM groups WHERE accounting_id = %s"
            cursor.execute(query, acc_id)
            u = cursor.fetchall()
            return tuple(map(lambda x: x['user_id'], u))

    @try_and_log('Ошибка получения списка бенефициаров')
    def get_beneficiaries(self, bnfcr):
        """
        Возвращает список пользователей множества бенефициалов
        Args:
            bnfcr (int): идентификатор множества бенефициаров beneficiaries.bnfcr_group
        Returns:
            list: список пользователей
        """
        with self.connection.cursor() as cursor:
            query = "SELECT user_id FROM beneficiaries WHERE bnfcr_group = %s"
            cursor.execute(query, bnfcr)
            u = cursor.fetchall()
            return list(map(lambda x: x['user_id'], u))

    # noinspection PyTypeChecker
    @try_and_log('Ошибка добавления пользователя к документу "Покупка')
    def add_user_to_purchase(self, acc_id, user, doc):
        """
        Добавляет пользователя в множество бенефициаров покупки
        Args:
            acc_id (int): идентификатор расчета accountings.id
            user (int): идентификаторр пользователя в БД users.id
            doc (int): идентификаторр документа покупки в БД purchase_docs.id
        """
        with self.connection.cursor() as cursor:
            self.post_purchase_doc(acc_id, doc, reject=True)
            query = "SELECT bnfcr_group FROM purchase_docs WHERE id = %s"
            cursor.execute(query, doc)
            bnfcr = cursor.fetchone()['bnfcr_group']
            users = result(self.get_beneficiaries(bnfcr))
            if user not in users:
                users.append(user)
            bnfcr = result(self.beneficiaries(users))
            query = "UPDATE purchase_docs SET bnfcr_group = %s WHERE id = %s"
            cursor.execute(query, [bnfcr, doc])
            self.connection.commit()
            self.logger.info(
                f"Пользователь {user} добавлен к списку бенефициаров документа покупки {doc}")
            self.post_purchase_doc(acc_id, doc, reject=False)

    # noinspection PyTypeChecker
    @try_and_log('Ошибка объединения кошелков')
    def merge_wallets(self, acc_id, wallets_list, name=None):
        """
        Объединяет список кошельков в один. \n
        Имя нового кошелька складывается из имен кошельков в списке, разделенных символом '+'

        Args:
            acc_id (int): идентификатор расчета accountings.id
            wallets_list (list(int)): Список идентификаторов объединяемых кошельков
            name (str): Название объединенного кошелька
        """
        with self.connection.cursor() as cursor:
            if len(wallets_list) < 2:
                return
            wallets = result(self.get_wallet_balance(acc_id, wallets_list))
            balance = wallets[0]['balance']
            default_name = name is None
            if default_name:
                name = wallets[0]['name']
            for wallet in wallets[1:]:
                query = "UPDATE wallets SET wallet = %s WHERE wallet = %s"
                cursor.execute(query, [wallets[0]['id'], wallet['id']])
                balance += wallet['balance']
                if default_name:
                    name += '+' + wallet['name']
            query = "UPDATE wallet_balance SET balance = %s, name = %s WHERE id = %s"
            cursor.execute(query, [balance, name, wallets[0]['id']])
            self.connection.commit()
            for wallet in wallets[1:]:
                query = "DELETE FROM wallet_balance WHERE id = %s"
                cursor.execute(query, wallet['id'])
            self.connection.commit()

    # noinspection PyTypeChecker
    @try_and_log('Ошибка присвоения пользователю номера текущего расчета')
    def set_current_accounting(self, acc_id, user):
        """
        Устанавливает указанный расчет как текущий для данного пользователя
        Args:
            acc_id: идентификатор расчета accountings.id
            user: идентификаторр пользователя в БД users.id
        """
        with self.connection.cursor() as cursor:
            query = "UPDATE users SET current_accounting = %s WHERE id = %s"
            cursor.execute(query, [acc_id, user])
            self.connection.commit()
            if acc_id is None:
                self.logger.info(
                    f"Пользователю {user} сброшен номер текущего расчета")
            else:
                self.logger.info(
                    f"Пользователю {user} присвоен номер текущего расчета {acc_id}")

    # noinspection PyTypeChecker
    @try_and_log('Ошибка получения номера текущего расчета')
    def get_current_accounting(self, user):
        """
        Возвращает идентификатор текущего расчета данного пользователя
        Args:
            user: идентификаторр пользователя в БД users.id
        Returns:
            int: идентификатор расчета accountings.id
        """
        with self.connection.cursor() as cursor:
            query = "SELECT current_accounting FROM users WHERE id = %s"
            cursor.execute(query, user)
            return cursor.fetchone()['current_accounting']

    # noinspection PyTypeChecker
    @try_and_log('Ошибка присединения пользователя к рассчету')
    def join_user(self, acc_id, user, recalc=False, wallet=None):
        """
        Добавляет пользователя к расчету
        Если установлен флаг recalc, все покупки в данном расчете пересчитываются с учетом нового пользователя
        Args:
            acc_id (int): идентификатор расчета accountings.id
            user (int): Идентификатор пользователя в БД users.id
            recalc (bool, optional): Флаг перерасчета. По умолчанию False
            wallet (int, optional): Идентификатор кошелька в БД wallet_balance.id.
        """
        with self.connection.cursor() as cursor:
            query = "SELECT current_accounting FROM users WHERE id = %s"
            cursor.execute(query, user)
            cur_acc = cursor.fetchone()
            if acc_id == cur_acc:
                return

            query = "UPDATE users SET current_accounting = %s WHERE id = %s"
            cursor.execute(query, [acc_id, user])
            query = "SELECT user_id FROM groups WHERE accounting_id = %s"
            cursor.execute(query, acc_id)
            users = cursor.fetchall()
            if user in users:
                result(self.set_current_accounting(acc_id, user))
                return

            query = "INSERT INTO groups (accounting_id, user_id) VALUES (%s, %s)"
            cursor.execute(query, [acc_id, user])
            query = "INSERT INTO user_balance (accounting_id, user_id, balance) VALUES (%s, %s, 0)"
            cursor.execute(query, [acc_id, user])
            self.connection.commit()
            if recalc:
                query = "SELECT id FROM purchase_docs WHERE accounting_id = %s"
                cursor.execute(query, acc_id)
                docs = cursor.fetchall()
                for doc in docs:
                    result(self.add_user_to_purchase(acc_id, user, doc['id']))
            self.logger.info(
                f"Пользователь {user} добавлен к расчету {acc_id}")
            result(self.set_current_accounting(acc_id, user))
            if wallet is None:
                wallet = result(self.new_wallet(user))
                self.update_wallet_balance(acc_id)
            result(self.assign_wallet(acc_id, user, wallet))
            self.update_wallet_balance(acc_id)

    # noinspection PyTypeChecker

    @try_and_log("Ошибка проверки пользователя")
    def check_user(self, acc_id, user):
        """
        Проверяет: входит ли пользователь в группу расчета
        Args:
            acc_id (int): идентификатор расчета accountings.id
            user (int): Идентификатор пользователя в БД users.id
        Raises:
            ValueError: Если пользователь н входит в группу
        """
        with self.connection.cursor() as cursor:
            query = "SELECT user_id FROM groups WHERE accounting_id = %s"
            cursor.execute(query, acc_id)
            users = [usr['user_id'] for usr in cursor.fetchall()]
            if user not in users:
                raise ValueError('Пользователь не входит в групу рассчета')

    # noinspection PyTypeChecker
    @try_and_log("Ошибка создания документа 'Покупка'")
    def add_purchase_doc(self, acc_id, purchaser, amount, bnfcr=None, comment=''):
        """
        Добавляет документ покупки. \n
        Если множество бенефициаров не задано, считается на всех участников расчета
        Args:
            acc_id (int): идентификатор расчета accountings.id
            purchaser (int): Покупатель. Идентификатор пользователя в БД users.id
            amount (float): Сумма покупки
            bnfcr (int, optional): Идентификатор множества бенефициаров beneficiaries.bnfcr_group. По умолчанию  None.
            comment (str, optional): Комментарий. По умолчанию  ''.
        Returns:
            int: Идентификатор документа покупки в БД purchase_docs.id.
        """

        if bnfcr is None:
            bnfcr_repr = "ВСЕ"
            bnfcr = result(self.beneficiaries(
                result(self.get_group_users(acc_id))))
        else:
            bnfcr_repr = str(bnfcr)
        result(self.check_user(acc_id, purchaser))
        with self.connection.cursor() as cursor:
            query = "INSERT INTO purchase_docs (purchaser, accounting_id, bnfcr_group, amount, comment) " \
                    "VALUES (%s, %s, %s, %s, %s) "
            cursor.execute(query, [purchaser, acc_id, bnfcr, amount, comment])
            self.connection.commit()
            cursor.execute('SELECT LAST_INSERT_ID() AS id')
            doc = cursor.fetchone()['id']
            self.logger.info(f"Создан документ покупки {doc}. "
                             f"Плательщик: {purchaser}, сумма: {amount}, группа бенефициаров: {bnfcr_repr}")
            result(self.post_purchase_doc(acc_id, doc))
            return doc

    # noinspection PyTypeChecker
    @try_and_log("Ошибка создания документа 'Платеж'")
    def add_payment_doc(self, acc_id, payer, recipient, amount, comment=''):
        """
        Добавляет документ платежа.
        Args:
            acc_id (int): идентификатор расчета accountings.id
            payer (_type_): Плательщик. Идентификатор пользователя в БД users.id
            recipient (_type_): Получатель. Идентификатор пользователя в БД users.id
            amount (_type_): Сумма
            comment (str, optional): Комментарий. По умолчанию ''.
        Returns:
            int: Идентификатор документа платежа в БД paymet_docs.id
        """
        result(self.check_user(acc_id, payer))
        result(self.check_user(acc_id, recipient))
        with self.connection.cursor() as cursor:
            query = "INSERT INTO payment_docs (payer, recipient, accounting_id, amount, comment) " \
                    "VALUES (%s, %s, %s, %s, %s) "
            cursor.execute(query, [payer, recipient, acc_id, amount, comment])
            self.connection.commit()
            cursor.execute('SELECT LAST_INSERT_ID() AS id')
            doc = cursor.fetchone()['id']
            self.logger.info(f"Создан документ платежа {doc}. "
                             f"Плательщик: {payer}, получатель: {recipient} сумма: {amount}")
            result(self.post_payment_doc(acc_id, doc))
            return doc

    # ПРОВЕДЕНИЕ/ОТМЕНА ДОКУМЕНТОВ

    # noinspection PyTypeChecker
    @try_and_log("Ошибка проведения/отмены документа 'Покука'")
    def post_purchase_doc(self, acc_id, doc_id, reject=False):
        """
        Проводит или отменяет проведение документа покупки в зависимости от флага reject
        Args:
            acc_id (int): идентификатор расчета accountings.id
            doc_id (int): Идентификатор документа покупки в БД purchase_docs.id
            reject (bool, optional): Флаг отмены проведения. По умолчанию False.
        """
        with self.connection.cursor() as cursor:
            sign = -1 if reject else 1
            query = "SELECT purchaser, bnfcr_group, amount FROM purchase_docs WHERE id = %s"
            cursor.execute(query, doc_id)
            document = cursor.fetchone()
            query = "SELECT user_id FROM beneficiaries WHERE bnfcr_group = %s"
            cursor.execute(query, document['bnfcr_group'])
            users = cursor.fetchall()
            for user in users:
                query = "SELECT balance FROM user_balance WHERE user_id = %s AND accounting_id = %s"
                cursor.execute(query, [user['user_id'], acc_id])
                user['balance'] = round(
                    cursor.fetchone()['balance'] - sign * document['amount'] / len(users), 2)
                if user['user_id'] == document['purchaser']:
                    user['balance'] += sign * document['amount']
                query = "UPDATE user_balance SET balance = %s WHERE user_id = %s AND accounting_id = %s"
                cursor.execute(
                    query, [user['balance'], user['user_id'], acc_id])
            cursor.execute("UPDATE purchase_docs SET posted = %s WHERE id = %s", [
                           not reject, doc_id])
            self.connection.commit()
            self.update_wallet_balance(acc_id)
            if reject:
                self.logger.info(
                    f"Отменено проведение документа покупки {doc_id}")
            else:
                self.logger.info(f"Проведен документ покупки {doc_id}")

    # noinspection PyTypeChecker
    @try_and_log("Ошибка проведения/отмены документа 'Платеж'")
    def post_payment_doc(self, acc_id, doc_id, reject=False):
        """
        Проводит или отменяет проведение документа платежа в зависимости от флага reject
        Args:
            acc_id (int): идентификатор расчета accountings.id
            doc_id (int): Идентификатор документа платежа в БД paymet_docs.id
            reject (bool, optional): Флаг отмены проведения. По умолчанию False.
        """
        with self.connection.cursor() as cursor:
            sign = -1 if reject else 1
            query = "SELECT payer, recipient, amount FROM payment_docs WHERE id =%s"
            cursor.execute(query, doc_id)
            doc = cursor.fetchone()
            query = "SELECT balance FROM user_balance WHERE user_id = %s AND accounting_id = %s"
            cursor.execute(query, [doc['payer'], acc_id])
            balance = round(cursor.fetchone()[
                            'balance'] + sign * doc['amount'], 2)
            query = "UPDATE user_balance SET balance = %s WHERE user_id = %s AND accounting_id = %s"
            cursor.execute(query, [balance, doc['payer'], acc_id])
            query = "SELECT balance FROM user_balance WHERE user_id = %s AND accounting_id = %s"
            cursor.execute(query, [doc['recipient'], acc_id])
            balance = round(cursor.fetchone()[
                            'balance'] - sign * doc['amount'], 2)
            query = "UPDATE user_balance SET balance = %s WHERE user_id = %s AND accounting_id = %s"
            cursor.execute(query, [balance, doc['recipient'], acc_id])
            cursor.execute(
                f"UPDATE payment_docs SET posted = {not reject} WHERE id = {doc_id}")
            self.connection.commit()
            self.update_wallet_balance(acc_id)
            if reject:
                self.logger.info(
                    f"Отменено проведение документа пплатежа {doc_id}")
            else:
                self.logger.info(f"Проведен документ пплатежа {doc_id}")

    # noinspection PyTypeChecker
    @try_and_log("Ошибка проведения/отмены всех документа расчета")
    def post_all_docs(self, acc_id, reject=False):
        """
        Проводит или отменяет проведение всех документов в расчете в зависимости от флага reject
        Args:
            acc_id (int): идентификатор расчета accountings.id
            reject (bool, optional): Флаг отмены проведения. По умолчанию False.
        """
        with self.connection.cursor() as cursor:
            if reject:
                query = "UPDETE user_balance SET balance = 0 WHERE accounting_id = %s"
                cursor.execute(query, acc_id)
                query = "UPDETE purchase_docs SET posted = FALSE WHERE accounting_id = %s"
                cursor.execute(query, acc_id)
                query = "UPDETE payment_docs SET posted = FALSE WHERE accounting_id = %s"
                cursor.execute(query, acc_id)
                self.connection.commit()
                self.logger.info(
                    f"Отненено проведение всех документов расчета {acc_id}")
            else:
                query = "SELECT id FROM purchase_docs WHERE accounting_id = %s"
                cursor.execute(query, acc_id)
                docs = cursor.fetchall()
                for doc in docs:
                    result(self.post_purchase_doc(acc_id, doc['doc_id']))
                query = "SELECT id FROM payment_docs WHERE accounting_id = %s}"
                cursor.execute(query, acc_id)
                docs = cursor.fetchall()
                for doc in docs:
                    result(self.post_payment_doc(acc_id, doc['doc_id']))
            return

    # БАЛАНС

    # noinspection PyTypeChecker
    @try_and_log("Ошибка обновления баланса")
    def update_wallet_balance(self, acc_id):
        """
        Обновляет значения балансов кошельков. \n
        Суммирует балансы пользователей, привязанных к кошельку
        Args:
            acc_id (int): идентификатор расчета accountings.id
        """
        with self.connection.cursor() as cursor:
            wallets = result(self.get_wallet_balance(acc_id))
            for wallet in wallets:
                query = "SELECT SUM(balance) AS balance FROM user_balance " \
                        "WHERE user_id in (SELECT user_id FROM wallets WHERE wallet = %s) " \
                        "AND accounting_id = %s"
                cursor.execute(query, (wallet['id'], acc_id))
                balance = cursor.fetchone()['balance']
                query = "UPDATE wallet_balance SET balance = %s WHERE id = %s"
                cursor.execute(query, [balance, wallet['id']])
                self.logger.info(
                    f"Обновлен баланс кошелька {wallet['id']}: {balance}")
            self.connection.commit()

    @try_and_log("Ошибка получения баланса")
    def get_user_balance(self, acc_id):
        """
        Возвращает баланс расчета в виде списка словарей с ключами
            'user_id' - идентификатор пользователя \n
            'user_nic' - ник пользователя \n
            'balance' - текущий баланс пользователя
        Args:
            acc_id (int): идентификатор расчета accountings.id
        Returns:
            list: баланс
        """
        with self.connection.cursor() as cursor:
            query = "SELECT user_id, user_nic, balance FROM user_balance " \
                    "JOIN users ON user_balance.user_id = users.id " \
                    "WHERE accounting_id = %s"
            cursor.execute(query, acc_id)
            return cursor.fetchall()

    @try_and_log("Ошибка получения баланса")
    def get_wallet_balance(self, acc_id, wallet_list=None):
        """
        Возвращает баланс расчета в виде списка словарей с ключами
            'id' - идентификатор кошелька \n
            'name' - название кошелька \n
            'balance' - текущий баланс кошелька
        Args:
            acc_id (int): идентификатор расчета accountings.id
            wallet_list (int/list(int), optional): идентификатор или список идентификаторов баланса кошелька
        Returns:
            list: баланс
        """
        with self.connection.cursor() as cursor:
            query = "SELECT id, name, balance FROM wallet_balance " \
                    "WHERE id in (SELECT wallet FROM wallets " \
                    "WHERE wallets.accounting_id = %s) "
            args = [acc_id]
            if wallet_list is not None:
                if isinstance(wallet_list, int):
                    wallet_list = (wallet_list,)
                query += "AND id in(" + \
                    ", ".join(['%s'] * len(wallet_list)) + ")"
                args += wallet_list
            cursor.execute(query, args)
            res = cursor.fetchall()
            return res

    @try_and_log("Ошибка вывода полного отчета")
    def total_report(self, acc_id):
        """
        Создает отчет по заданному расчету, сохраняет его в текстовом файле и возвращает имя файла
        Args:
            acc_id (int): идентификатор расчета accountings.id
        Returns:
            str: имя файла отчета
        """
        if not os.path.isdir("Reports"):
            os.mkdir("Reports")
        with self.connection.cursor() as cursor:
            query = "SELECT name, start_time, end_time FROM accountings WHERE id = %s"
            cursor.execute(query, acc_id)
            res = cursor.fetchone()
            query = ("SELECT DISTINCT wallets.wallet, wallet_balance.name, wallet_balance.balance  "
                     "FROM wallets JOIN wallet_balance ON wallets.wallet = wallet_balance.id "
                     "WHERE accounting_id = %s")
            cursor.execute(query, acc_id)
            wallets = cursor.fetchall()
            file_name = (f"rpt_total_{res['name']}_"
                         f"{datetime.now().year}{datetime.now().month:02}{datetime.now().day:02}_"
                         f"{datetime.now().hour:02}{datetime.now().minute:02}{datetime.now().second:02}"
                         f"{(datetime.now().microsecond//10000):02}.txt").replace(' ', '_')
            with open(f"Reports/{file_name}", 'w') as report:
                report.write(f'Отчет по расчету "{res["name"]}" \n')
                report.write(f'время начала: {res["start_time"]} \n')
                report.write(
                    f'время окончания: {res["end_time"] if res["end_time"] is not None else "-" } \n')
                report.write(f"\nПОКУПКИ\n")
                for wallet in wallets:
                    query = ("SELECT users.id, users.user_nic FROM wallets "
                             "JOIN users ON users.id = wallets.user_id "
                             "WHERE wallet = %s")
                    cursor.execute(query, wallet['wallet'])
                    users = cursor.fetchall()
                    for user in users:
                        query = ("SELECT time, comment, amount FROM purchase_docs "
                                 "WHERE accounting_id = %s AND purchaser = %s")
                        cursor.execute(query, (acc_id, user['id']))
                        docs = cursor.fetchall()
                        if len(docs) == 0:
                            continue
                        report.write(f"  Покупки {user['user_nic']} \n")
                        for doc in docs:
                            report.write(
                                f"    {doc['time']}:     {doc['comment']}  -  {doc['amount']} \n")
                report.write(f"\nПЛАТЕЖИ\n")
                for wallet in wallets:
                    query = ("SELECT users.id, users.user_nic FROM wallets "
                             "JOIN users ON users.id = wallets.user_id "
                             "WHERE wallet = %s")
                    cursor.execute(query, wallet['wallet'])
                    users = cursor.fetchall()
                    for user in users:
                        query = ("SELECT time, users.user_nic AS recipient, comment, amount FROM payment_docs "
                                 "JOIN users ON users.id = recipient "
                                 "WHERE accounting_id = %s AND payer = %s")
                        cursor.execute(query, (acc_id, user['id']))
                        docs = cursor.fetchall()
                        if len(docs) == 0:
                            continue
                        report.write(f"  Платежи {user['user_nic']} \n")
                        for doc in docs:
                            report.write(f"    {doc['time']}:    {doc['recipient']}  "
                                         f"({doc['comment']})  -  {doc['amount']} \n")
                report.write(f"\nБАЛАНС\n")
                for wallet in wallets:
                    report.write(
                        f"  {wallet['name']}  -  {wallet['balance']} \n")
                self.logger.info(
                    f"Отчет по расчету {acc_id} сохранен в файле {file_name}")
            return file_name

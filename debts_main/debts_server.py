import asyncio

import pymysql
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
        def wrap(*args, **kwargs):
            self = args[0]
            try:
                self.connection.ping(reconnect=True)
                return func(*args, **kwargs), 'OK'
            except Exception as ex:
                dtl_msg = f"{msg}: {ex}"
                self.logger.error(dtl_msg)
                return None, dtl_msg

        return wrap

    return dcrtr


def atry_and_log(msg):
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
        async def wrap(*args, **kwargs):
            self = args[0]
            try:
                self.connection.ping(reconnect=True)
                return await func(*args, **kwargs), 'OK'
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

    def __init__(self, msg_cbs=None):
        """
        Инициализация DebtsServer. \n
        Параметры БД считывает из файла .env \n
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

        try:
            self.host = config.IP
            self.port = config.PORT
            self.database = config.DATABASE
            self.db_user = config.PGUSER
            self.password = config.PGPASSWORD
        except Exception as ex:
            self.logger.error(
                f"Невозможно прочитать файл конфигурации:\n\t{ex}")

        self.connection = None
        self.logger.info(f'Подключение к базе данных {self.database} '
                         f'на сервере {self.host}{f":{self.port}" if self.port != 3306 else ""}')
        try:
            # noinspection PyUnresolvedReferences
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.db_user,
                password=self.password,
                database=self.database,
                cursorclass=pymysql.cursors.DictCursor
            )
            self.logger.info('Подключение выполнено успешно')
        except pymysql.err.OperationalError:
            self.logger.error('Невозможно подключиться к базе данных')
        self.msg_cbs = msg_cbs

    @try_and_log('Ошибка исполнения внешнего запроса')
    def execute(self, query: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = tuple()

        self.logger.debug(f'query = "{query}, ({parameters})')
        with self.connection.cursor() as cursor:
            cursor.execute(query, parameters)
            data = None

            if commit:
                self.connection.commit()
            elif fetchone:
                data = cursor.fetchone()
            elif fetchall:
                data = cursor.fetchall()

            return data

    ######################################################################
    #              Методы работы с пользователями и группами             #
    ######################################################################

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
            cursor.execute(query, user_id)
            if cursor.fetchone() is not None:
                raise ValueError('Пользователь с таким id уже зарегистрирован')
            query = "INSERT INTO users (id, user_nic) VALUES (%s, %s)"
            self.logger.info(f'query={query}"')
            cursor.execute(query, [user_id, nic])
            self.connection.commit()
            self.logger.info(
                f"Зарегистрирован новый пользователь {nic} (id: {user_id})")

    @try_and_log('Ошибка подучения имени пользователя')
    def user_name(self, user):
        """
        Метод возвращает имя пользователя
        Args:
            user (int): ID пользователя в БД users.id
        Returns:
            str: Имя пользователя
        """
        with self.connection.cursor() as cursor:
            query = "SELECT user_nic FROM users WHERE id = %s"
            cursor.execute(query, user)
            return cursor.fetchone()['user_nic']

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

    @try_and_log("Ошибка при проверке пользователя")
    def check_user(self, acc_id=None, user=None):
        """
        Если acc_id целое число, проверяет: входит ли пользователь в группу расчета.
        Если acc_id is None, проверяет его наличие в базе таблице пользователей.
        Args:
            acc_id (int): Идентификатор расчета accountings.id
            user (int): Идентификатор пользователя в БД users.id
        Returns:
            bool: Результат поиска пользователя
        """
        with self.connection.cursor() as cursor:
            if acc_id is not None:
                query = "SELECT id FROM groups WHERE accounting_id = %s AND user_id = %s"
                cursor.execute(query, (acc_id, user))
                where = f"в группе расчета {acc_id}"
            else:
                query = "SELECT id FROM users WHERE id = %s"
                cursor.execute(query, user)
                where = "в базе данных"
            users = cursor.fetchall()
            if len(users) == 0:
                self.logger.info(f"Пользователь {user} не найден {where}")
                return False
            else:
                self.logger.info(f"Пользователь {user} найден {where}")
                return True

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

    ######################################################################
    #                   Методы работы с расчетами                        #
    ######################################################################

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
            self.logger.info(f"К расчету {accounting_id} добавлены участники {', '.join(map(str, users))}")
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
        query = "SELECT * FROM accountings "
        if status.upper() == 'ACTIVE':
            query += "WHERE start_time IS NOT NULL AND end_time IS NULL"
        elif status.upper() == 'ARCHIVE':
            query += "WHERE end_time IS NOT NULL"
        return result(self.execute(query, fetchall=True))

    @try_and_log('Ошибка подучения названия расчета')
    def accounting_name(self, acc_id):
        """
        Метод возвращает название расчета
        Args:
            acc_id (int): ID расчета в БД accountings.id
        Returns:
            str: Имя пользователя
        """
        with self.connection.cursor() as cursor:
            query = "SELECT name FROM accountings WHERE id = %s"
            cursor.execute(query, acc_id)
            return cursor.fetchone()['name']

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
            wallet (int, optional): Идентификатор кошелька в БД wallets.id.
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

    ######################################################################
    #                   Методы работы с кошельками                       #
    ######################################################################

    @try_and_log('Ошибка создания нового кошелька')
    def new_wallet(self, user, wallet_name=None):
        """
        Создает в базе данных новый кошелек для одного пользователя
        Args:
            user (int): ID пользователя в БД users.id
            wallet_name (str, optional): Имя кошелька. По умолчанию: ник пользователя.
        Returns:
            int: ID кошелька в БД wallets.id
        """
        self.logger.debug(f"Запрос на создаие нового кошелька. user={user}, name='{wallet_name}'")
        with self.connection.cursor() as cursor:
            if wallet_name is None:
                cursor.execute(
                    "SELECT user_nic FROM users WHERE id = %s", user)
                wallet_name = cursor.fetchone()['user_nic']
            result(self.execute("INSERT INTO wallets (balance, name) VALUES (0, %s)",
                                wallet_name, commit=True))
            self.logger.info(f"Создан новый кошелек {wallet_name}")
            return result(self.execute('SELECT LAST_INSERT_ID() AS id', fetchone=True))['id']

    @try_and_log('Ошибка подучения названия кошелька')
    def wallet_name(self, wallet):
        """
        Метод возвращает имя пользователя
        Args:
            wallet (int): ID кошелька в БД wallets.id
        Returns:
            str: Имя кошелька
        """
        query = "SELECT name FROM wallets WHERE id = %s"
        return result(self.execute(query, wallet, fetchone=True))['name']

    @try_and_log('Ошибка присвоения пользователям кошельков')
    def assign_wallet(self, acc_id, users, wallets):
        """
        Присваивает пользователям из сиска users кошельки из списка wallets
        Args:
            acc_id (int): ID расчета в БД accountings.id
            users (list(int)): Список идентификаторов пользователей
            wallets (list(int)): Список идентификаторов кошельков
        """
        if isinstance(users, int):
            users = [users]
            wallets = [wallets]
        self.logger.debug(f"Запрос на присвоение кошелька пользователям. acc_id={acc_id}, "
                          f"users=({', '.join(map(str, users))}), "
                          f"walets=({', '.join(map(str, wallets))})"
                          )
        with self.connection.cursor():
            query = "INSERT INTO wallet_users (user_id, accounting_id, wallet) VALUES " + \
                    ", ".join(["(%s, %s, %s)"] * len(users))
            args = [[users[i], acc_id, wallets[i]][j]
                    for i in range(len(users)) for j in range(3)]
            result(self.execute(query, args, commit=True))
            self.logger.info(f"Участникам {', '.join(map(str, users))} "
                             f"присвоены кошельки {', '.join(map(str, wallets))}")

    @try_and_log('Ошибка получения списка пользователей кошелька')
    def wallet_users(self, acc_id, user=None, wallet=None):
        """
        Возвращает список пользователей входящих в один кошелек \n
        Кошелек задается или явно через ID (wallets.id) или через ID пользователя и расчета.
        Если задано и то и другое, поиск ведется по ID пользователя и расчета
        Args:
            acc_id (int): ID расчета в БД accountings.id
            user (int):   ID пользователя в БД users.id
            wallet (int): ID кошелька в БД wallets.id
        Returns:
            list(int):  список идентификаторов пользователей

        """
        if user is not None:
            wallet = result(self.my_wallet(acc_id, user))
        if wallet is None:
            return []
        with self.connection.cursor() as cursor:
            query = "SELECT user_id FROM wallet_users WHERE wallet = %s"
            cursor.execute(query, wallet)
            return [user['user_id'] for user in cursor.fetchall()]

    @try_and_log('Ошибка получения номера собственного кошелька')
    def my_wallet(self, acc_id, user):
        """
            Возвращает идентификатор кошелька, к которому присединет пользователь
            Args:
                acc_id (int): идентификатор расчета accountings.id
                user: идентификаторр пользователя в БД users.id
            Returns:
                int: идентификатор кошелька wallet_users.wallet
        """
        with self.connection.cursor():
            query = "SELECT wallet FROM wallet_users WHERE accounting_id = %s AND user_id = %s"
            return result(self.execute(query, (acc_id, user), fetchone=True))['wallet']

    @try_and_log('Ошибка получения списка чужих кошельков')
    def others_wallets(self, acc_id, user):
        """
            Возвращает список идентификаторов чужих кошельков
            Args:
                acc_id (int): идентификатор расчета accountings.id
                user: идентификаторр пользователя в БД users.id
            Returns:
                lst(int): список идентификаторов кошельков wallet_users.wallet
        """
        my_wallet = self.my_wallet(acc_id, user)[0]
        with self.connection.cursor():
            query = "SELECT DISTINCT wallet FROM wallet_users WHERE accounting_id = %s"
            all_wallets = [wlt['wallet'] for wlt in result(self.execute(query, acc_id, fetchall=True))]
            all_wallets.remove(my_wallet)
            return all_wallets

    @try_and_log('Ошибка получения баласа кошельков')
    def wallet_balances(self, acc_id):
        """
            Возвращает словарь состоящий из имен и балансов всех кошельков расчета
            Args:
                acc_id (int): идентификатор расчета accountings.id
            Returns:
                dict: словарь: ключи - названия кошельков; значения - балансы
        """
        with self.connection.cursor():
            query = ("SELECT wallets.name as name, wallets.balance as balance "
                     "FROM wallet_users JOIN wallets ON wallet_users.wallet = wallets.id "
                     "WHERE accounting_id = %s")
            wallets = result(self.execute(query, acc_id, fetchall=True))
            return {wallet['name']: wallet['balance'] for wallet in wallets}

    @try_and_log('Ошибка получения баласа кошельков пользователей')
    def user_wallet_balance(self, acc_id):
        """
        Возвращает баланс кошельков пользователей расчета в виде списка словарей с ключами
            'user_id' - идентификатор пользователя \n
            'balance' - баланс кошелька пользователя
            Args:
                acc_id (int): идентификатор расчета accountings.id
            Returns:
                list(dict)
        """
        with self.connection.cursor():
            query = ("SELECT wallet_users.user_id, wallets.balance, users.user_nic FROM wallet_users "
                     "JOIN wallets ON wallet_users.wallet = wallets.id "
                     "JOIN users ON users.id = wallet_users.user_id "
                     "WHERE accounting_id = %s")
            return result(self.execute(query, acc_id, fetchall=True))

    # noinspection PyTypeChecker
    @try_and_log('Ошибка объединения кошельков')
    def merge_wallets(self, acc_id, wallets_list, name=None):
        """
        Объединяет список кошельков в один. \n
        Имя нового кошелька складывается из имен кошельков в списке, разделенных символом '+'

        Args:
            acc_id (int): идентификатор расчета accountings.id
            wallets_list (list(int)): Список идентификаторов объединяемых кошельков
            name (str): Название объединенного кошелька
        """
        self.logger.debug(f"Запрос на объединение кошельков. acc_id={acc_id}, "
                          f"wallets_list=({', '.join(map(str, wallets_list))}), "
                          f"name='{name}'"
                          )
        with self.connection.cursor():
            if len(wallets_list) < 2:
                return
            wallets = result(self.get_wallet_balance(acc_id, wallets_list))
            balance = wallets[0]['balance']
            default_name = name is None
            if default_name:
                name = wallets[0]['name']
            for wallet in wallets[1:]:
                query = "UPDATE wallet_users SET wallet = %s WHERE wallet = %s"
                result(self.execute(query, (wallets[0]['id'], wallet['id'])))
                balance += wallet['balance']
                if default_name:
                    name += '+' + wallet['name']
            query = "UPDATE wallets SET balance = %s, name = %s WHERE id = %s"
            result(self.execute(query, (balance, name, wallets[0]['id']), commit=True))
            self.logger.info(f"Кошельки {', '.join(map(str, wallets_list))} объединены под номером {wallets_list[0]}")
            self.logger.info(f"Название нового кошелька: '{name}'")
            for wallet in wallets[1:]:
                query = "DELETE FROM wallets WHERE id = %s"
                result(self.execute(query, wallet['id']))
            self.connection.commit()
            self.logger.info(f"Удалены неиспользуемые кошельки {', '.join(map(str, wallets_list[1:]))}")

    @try_and_log('Ошибка выхода пользователя из кошелька')
    def leave_wallet(self, acc_id, user, name=None):
        """
        Метод для выхода пользователя из кошелька \n
        Имя нового кошелька складывается из имен кошельков в списке, разделенных символом '+'

        Args:
            acc_id: идентификатор расчета accountings.id
            user (int): идентификатор пользователя users.id
            name (str): Новое название кошелька после выхода пользователя
        """
        wallet = result(self.my_wallet(acc_id, user))
        self.logger.debug(f"Запрос на выход из кошелька. acc_id={acc_id}, user={user} "
                          f"wallet={wallet}, name='{name}'"
                          )
        with self.connection.cursor() as cursor:
            if name is None:
                query = "SELECT user_id FROM wallet_users WHERE wallet = %s AND user_id != %s"
                cursor.execute(query, (wallet, user))
                users = cursor.fetchall()
                if len(users) == 1:
                    name = result(self.user_name(users[0]['user_id']))
                else:
                    name = result(self.wallet_name(wallet))
            query = "SELECT balance FROM user_balance WHERE accounting_id = %s AND user_id = %s"
            user_balance = result(self.execute(query, (acc_id, user), fetchone=True))['balance']
            query = "SELECT user_nic FROM users WHERE id = %s"
            user_nic = result(self.execute(query, user, fetchone=True))['user_nic']
            query = "SELECT balance FROM wallets WHERE id = %s"
            wallet_balance = result(self.execute(query, wallet, fetchone=True))['balance']
            query = "INSERT INTO wallets (balance, name) VALUES (%s, %s)"
            cursor.execute(query, (user_balance, user_nic))
            self.connection.commit()
            query = "SELECT LAST_INSERT_ID() AS id"
            new_wallet = result(self.execute(query, fetchone=True))['id']
            print(new_wallet)
            query = "UPDATE wallets SET balance = %s, name = %s WHERE id = %s"
            result(self.execute(query, (wallet_balance-user_balance, name, wallet)))
            query = "UPDATE wallet_users SET wallet = %s WHERE user_id = %s AND accounting_id = %s"
            result(self.execute(query, (new_wallet, user, acc_id), commit=True))
            self.logger.info(f"Пользователю {user} вышел из кошелька {wallet}")
            self.logger.info(f"Кошелькам присвоены названия '{name}' и '{user_nic}'")

    # noinspection PyTypeChecker
    @try_and_log("Ошибка обновления баланса")
    def update_wallet_balance(self, acc_id):
        """
        Обновляет значения балансов кошельков. \n
        Суммирует балансы пользователей, привязанных к кошельку
        Args:
            acc_id (int): идентификатор расчета accountings.id
        """
        self.logger.debug(f"Запрос на обновление баланса кошельков. acc_id={acc_id}")
        with self.connection.cursor() as cursor:
            wallets = result(self.get_wallet_balance(acc_id))
            for wallet in wallets:
                query = "SELECT SUM(balance) AS balance FROM user_balance " \
                        "WHERE user_id in (SELECT user_id FROM wallet_users WHERE wallet = %s) " \
                        "AND accounting_id = %s"
                cursor.execute(query, (wallet['id'], acc_id))
                balance = cursor.fetchone()['balance']
                query = "UPDATE wallets SET balance = %s WHERE id = %s"
                cursor.execute(query, [balance, wallet['id']])
                self.logger.info(
                    f"Обновлен баланс кошелька {wallet['id']}: {balance}")
            self.connection.commit()

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
            query = "SELECT id, name, balance FROM wallets " \
                    "WHERE id in (SELECT wallet FROM wallet_users " \
                    "WHERE wallet_users.accounting_id = %s) "
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

    ######################################################################
    #                   Методы работы с документами                      #
    ######################################################################

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
            self.logger.info(f"Пользователь {user} добавлен к списку бенефициаров документа покупки {doc}")
            self.post_purchase_doc(acc_id, doc, reject=False)

    # noinspection PyTypeChecker

    # noinspection PyTypeChecker
    @atry_and_log("Ошибка создания документа 'Покупка'")
    async def add_purchase_doc(self, acc_id, purchaser, amount, bnfcr=None, comment=''):
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
        if not result(self.check_user(acc_id, purchaser)):
            return None
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
            await self.notice_purchase(doc)
            return doc

    # noinspection PyTypeChecker
    @atry_and_log("Ошибка создания документа 'Платеж'")
    async def add_payment_doc(self, acc_id, payer, recipient, amount, comment=''):
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
        if not result(self.check_user(acc_id, payer)):
            return None
        if not result(self.check_user(acc_id, recipient)):
            return None
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
            await self.notice_payment(doc)
            return doc

    # noinspection PyTypeChecker
    @atry_and_log("Ошибка удаления документа 'Покупка' или 'Платеж'")
    async def del_doc(self, doc_id, doc_type):
        """
        Удаляет документ покупки или платежа. \n
        Args:
            doc_id (int): идентификатор документа покупки purchase_docs.id
            doc_type (str): тип документа: 'purchase' или 'payment'
        """

        doc_type = doc_type.lower()
        with self.connection.cursor():
            query = (f"SELECT {'purchaser' if doc_type == 'purchase' else 'payer'} as user, "
                     f"amount, comment, time, accounting_id as acc_id, accountings.name as acc_name "
                     f"FROM {doc_type}_docs JOIN accountings ON accountings.id = {doc_type}_docs.accounting_id "
                     f"WHERE {doc_type}_docs.id = %s")
            doc = result(self.execute(query, doc_id, fetchone=True))
            user_name = result(self.user_name(doc['user']))
            msg_data = {'acc_id': doc['acc_id'],
                        'acc_name': doc['acc_name'],
                        'user_name': user_name,
                        'doc_type': 'покупку' if doc_type == 'purchase' else 'платеж',
                        'doc_id': doc_id,
                        'doc_time': str(doc['time'])[:-3],
                        'amount': doc['amount'],
                        'comment': doc['comment']}

            query = f"SELECT accounting_id FROM {doc_type}_docs WHERE id = %s"
            acc_id = result(self.execute(query, doc_id, fetchone=True))['accounting_id']
            balance1 = result(self.user_wallet_balance(acc_id))
            if doc_type == 'purchase':
                result(self.post_purchase_doc(acc_id, doc_id, reject=True))
            elif doc_type == 'payment':
                result(self.post_payment_doc(acc_id, doc_id, reject=True))
            query = f"DELETE FROM  {doc_type}_docs WHERE id = %s"
            result(self.execute(query, doc_id, commit=True))
            balance2 = result(self.user_wallet_balance(acc_id))
        users = list(balance2)
        for i in range(len(balance1)):
            if abs(balance1[i]['balance'] - balance2[i]['balance']) < 1 or balance1[i]['user_id'] == doc['user']:
                users.remove(balance2[i])
        result(await self.notice_del_doc(users, msg_data))

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
            users = result(self.execute(query, document['bnfcr_group'], fetchall=True))
            for user in users:
                query = "SELECT balance FROM user_balance WHERE user_id = %s AND accounting_id = %s"
                cursor.execute(query, [user['user_id'], acc_id])
                user['balance'] = round(cursor.fetchone()['balance'] - sign * document['amount'] / len(users), 2)
                if user['user_id'] == document['purchaser']:
                    user['balance'] += sign * document['amount']
                query = "UPDATE user_balance SET balance = %s WHERE user_id = %s AND accounting_id = %s"
                cursor.execute(query, [user['balance'], user['user_id'], acc_id])
            cursor.execute("UPDATE purchase_docs SET posted = %s WHERE id = %s", [not reject, doc_id])
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
                self.logger.info(f"Отменено проведение документа пплатежа {doc_id}")
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

    ######################################################################
    #                   Методы для получения отчетов                     #
    ######################################################################

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
            query = ("SELECT DISTINCT wallet_users.wallet, wallets.name, wallets.balance  "
                     "FROM wallet_users JOIN wallets ON wallet_users.wallet = wallets.id "
                     "WHERE accounting_id = %s")
            cursor.execute(query, acc_id)
            wallets = cursor.fetchall()
            file_name = (f"rpt_total_{res['name']}_"
                         f"{datetime.now().year}{datetime.now().month:02}{datetime.now().day:02}_"
                         f"{datetime.now().hour:02}{datetime.now().minute:02}{datetime.now().second:02}"
                         f"{(datetime.now().microsecond//10000):02}.txt").replace(' ', '_')
            with open(f"Reports/{file_name}", 'w', encoding='utf-8') as report:
                report.write(f'Отчет по расчету "{res["name"]}" \n')
                report.write(f'время начала: {res["start_time"]} \n')
                report.write(
                    f'время окончания: {res["end_time"] if res["end_time"] is not None else "-" } \n')
                report.write(f"\nПОКУПКИ\n")
                for wallet in wallets:
                    wallet_sum = 0
                    query = ("SELECT users.id, users.user_nic FROM wallet_users "
                             "JOIN users ON users.id = wallet_users.user_id "
                             "WHERE wallet = %s")
                    cursor.execute(query, wallet['wallet'])
                    users = cursor.fetchall()
                    for user in users:
                        query = ("SELECT id, time, comment, amount FROM purchase_docs "
                                 "WHERE accounting_id = %s AND purchaser = %s")
                        cursor.execute(query, (acc_id, user['id']))
                        docs = cursor.fetchall()
                        if len(docs) == 0:
                            continue
                        report.write(f"  Покупки {user['user_nic']} \n")
                        for doc in docs:
                            report.write(
                                f"    {doc['id']:06} от {str(doc['time'])[:-3]} \n"
                                f"{' '*10}{doc['comment']}:   {doc['amount']} \n")
                        query = ("SELECT SUM(amount) as user_sum FROM purchase_docs "
                                 "WHERE purchaser = %s AND accounting_id = %s")
                        cursor.execute(query, (user['id'], acc_id))
                        user_sum = cursor.fetchone()['user_sum']
                        wallet_sum += user_sum
                        report.write(f"    ИТОГО ({user['user_nic']}):   {user_sum} \n")
                    report.write(f"    ИТОГО ({wallet['name']}):   {wallet_sum} \n")
                report.write(f"\nПЛАТЕЖИ\n")
                for wallet in wallets:
                    query = ("SELECT users.id, users.user_nic FROM wallet_users "
                             "JOIN users ON users.id = wallet_users.user_id "
                             "WHERE wallet = %s")
                    cursor.execute(query, wallet['wallet'])
                    users = cursor.fetchall()
                    for user in users:
                        query = ("SELECT payment_docs.id, time, users.user_nic AS recipient, comment, amount "
                                 "FROM payment_docs "
                                 "JOIN users ON users.id = recipient "
                                 "WHERE accounting_id = %s AND payer = %s "
                                 "ORDER BY recipient")
                        cursor.execute(query, (acc_id, user['id']))
                        docs = cursor.fetchall()
                        if len(docs) == 0:
                            continue
                        report.write(f"  Платежи {user['user_nic']} \n")
                        for doc in docs:
                            report.write(f"   {doc['id']:06} от {str(doc['time'])[:-3]} -> {doc['recipient']} \n"
                                         f"{' '*10}{doc['comment']}:   {doc['amount']} \n")
                report.write(f"\nБАЛАНС\n")
                for wallet in wallets:
                    report.write(
                        f"  {wallet['name']}  -  {wallet['balance']} \n")
                self.logger.info(f"Отчет по расчету {acc_id} сохранен в файле {file_name}")
            return file_name

    ######################################################################
    #                   Методы для отправки сообщний                     #
    ######################################################################

    @atry_and_log("Ошибка отправки уведомления о покупке")
    async def notice_purchase(self, doc_id):
        if self.msg_cbs is None:
            return
        query = ("SELECT purchaser, amount, comment, time, bnfcr_group, accounting_id, accountings.name as acc_name "
                 "FROM purchase_docs JOIN accountings ON accountings.id = purchase_docs.accounting_id "
                 "WHERE purchase_docs.id = %s")
        doc = result(self.execute(query, doc_id, fetchone=True))

        msg = (f"Расчет '{doc['acc_name']}'\n"
               f"{result(self.user_name(doc['purchaser']))} совершил покупку\n"
               f"{doc['comment']},\n"
               f"на сумму {doc['amount']}\n"
               f"документ №{doc_id} от {str(doc['time'])[:-3]}\n")

        query = "SELECT user_id FROM beneficiaries WHERE bnfcr_group = %s AND user_id != %s"
        res = result(self.execute(query, (doc['bnfcr_group'], doc['purchaser']), fetchall=True))
        bnfcrs = [user['user_id']
                  for user in res]
        msg_tasks = []
        for user in bnfcrs:
            wallet = result(self.my_wallet(doc['accounting_id'], user))
            query = "SELECT balance FROM wallets WHERE id = %s"
            balance = result(self.execute(query, wallet, fetchone=True))
            msg_tasks.append(asyncio.create_task(self.msg_cbs(user, msg + f"Ваш баланс: {balance['balance']}")))
            self.logger.info(f"Пользователю {user} отправлено уведомление о покупке {doc_id}")

        await asyncio.gather(*msg_tasks)

    @atry_and_log("Ошибка отправки уведомления о платеже")
    async def notice_payment(self, doc_id):
        if self.msg_cbs is None:
            return
        query = ("SELECT payer, recipient, amount, comment, time, accounting_id, accountings.name as acc_name "
                 "FROM payment_docs JOIN accountings ON accountings.id = payment_docs.accounting_id "
                 "WHERE payment_docs.id = %s")
        doc = result(self.execute(query, doc_id, fetchone=True))

        wallet = result(self.my_wallet(doc['accounting_id'], doc['recipient']))
        query = "SELECT balance FROM wallets WHERE id = %s"
        balance = result(self.execute(query, wallet, fetchone=True))

        msg = (f"Расчет '{doc['acc_name']}',\n"
               f"платеж от {result(self.user_name(doc['payer']))},\n"
               f"сумма: {doc['amount']},\n"
               f"комментарий: {doc['comment']}\n"
               f"документ №{doc_id} от {str(doc['time'])[:-3]}.\n"
               f"Ваш баланс: {balance['balance']}")

        self.logger.info(f"Пользователю {doc['recipient']} отправлено уведомление о платеже {doc_id}")
        await self.msg_cbs(doc['recipient'], msg)

    @atry_and_log("Ошибка отправки сообщения о платеже")
    async def notice_del_doc(self, users, msg_data):
        msg = (f"Расчет №{msg_data['acc_id']} '{msg_data['acc_name']}',\n"
               f"{msg_data['user_name']} отменил(а) {msg_data['doc_type']}\n"
               f"документ №{msg_data['doc_id']} от  {msg_data['doc_time']}\n"
               f"сумма: {msg_data['amount']},\n"
               f"комментарий: {msg_data['comment']}\n")

        msg_tasks = []
        for user in users:
            msg_tasks.append(asyncio.create_task(self.msg_cbs(user['user_id'],
                                                              msg + f"Ваш баланс: {user['balance']}")))
            self.logger.info(f"Пользователю {user['user_id']} отправлено уведомление об отмене {msg_data['doc_id']}")

        await asyncio.gather(*msg_tasks)

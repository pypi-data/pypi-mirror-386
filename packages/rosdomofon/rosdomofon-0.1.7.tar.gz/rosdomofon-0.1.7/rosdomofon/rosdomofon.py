"""
Клиент для работы с API РосДомофон
"""
from typing import List, Optional, Union
import requests
import time
from loguru import logger
from pprint import pprint
from .models import (
    AuthResponse, Account, CreateAccountRequest, CreateAccountResponse,
    CreateFlatRequest, CreateFlatResponse, Service, CreateConnectionRequest,
    CreateConnectionResponse, Connection, SendMessageRequest, MessagesResponse,
    AbonentInfo, KafkaIncomingMessage, SignUpEvent, AccountInfo, EntrancesResponse,
    AbonentFlat
)
from .kafka_client import RosDomofonKafkaClient


class RosDomofonAPI:
    """Клиент для работы с API РосДомофон"""
    
    BASE_URL = "https://rdba.rosdomofon.com"
    
    def __init__(self, 
                 username: str, 
                 password: str,
                 kafka_bootstrap_servers: Optional[str] = None,
                 company_short_name: Optional[str] = None,
                 kafka_group_id: Optional[str] = None,
                 kafka_username: Optional[str] = None,
                 kafka_password: Optional[str] = None,
                 kafka_ssl_ca_cert_path: Optional[str] = None):
        self.username = username
        self.password = password
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        self.session = requests.Session()
        
        # Kafka клиент (опционально)
        self.kafka_client: Optional[RosDomofonKafkaClient] = None
        if kafka_bootstrap_servers and company_short_name:
            self.kafka_client = RosDomofonKafkaClient(
                bootstrap_servers=kafka_bootstrap_servers,
                company_short_name=company_short_name,
                group_id=kafka_group_id,
                username=kafka_username,
                password=kafka_password,
                ssl_ca_cert_path=kafka_ssl_ca_cert_path
            )
        
        logger.info("Инициализация клиента РосДомофон API")
        if self.kafka_client:
            logger.info("Kafka клиент инициализирован")
    
    def _get_headers(self, auth_required: bool = True) -> dict:
        """Получить заголовки для запроса"""
        headers = {"Content-Type": "application/json"}
        if auth_required and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    def _make_request(self, method: str, url: str, retry_auth: bool = True, **kwargs) -> requests.Response:
        """
        Выполнить HTTP запрос с обработкой ошибок
        
        Args:
            method (str): HTTP метод
            url (str): URL для запроса
            retry_auth (bool): Флаг для повторной попытки при 401 ошибке (предотвращает бесконечный цикл)
            **kwargs: Дополнительные параметры для requests
            
        Returns:
            requests.Response: Ответ сервера
        """
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            logger.debug(f"{method} {url} - статус: {response.status_code}")
            return response
        except requests.exceptions.HTTPError as e:
            # Перехватываем 401 (Unauthorized) и пытаемся переавторизоваться
            if e.response.status_code == 401 and retry_auth:
                logger.warning("Токен истек (401 Unauthorized), выполняется переавторизация...")
                # Переавторизуемся
                self.authenticate()
                # Обновляем заголовки с новым токеном
                if 'headers' in kwargs and 'Authorization' in kwargs.get('headers', {}):
                    kwargs['headers']['Authorization'] = f"Bearer {self.access_token}"
                # Повторяем запрос (retry_auth=False чтобы избежать бесконечного цикла)
                logger.info("Повторный запрос с новым токеном")
                return self._make_request(method, url, retry_auth=False, **kwargs)
            else:
                logger.error(f"Ошибка запроса {method} {url}: {e}")
                raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса {method} {url}: {e}")
            raise
    
    def authenticate(self) -> AuthResponse:
        """
        Авторизация в системе РосДомофон
        
        Returns:
            AuthResponse: Объект с токеном доступа и информацией об авторизации
            
        Example:
            >>> api = RosDomofonAPI("username", "password")
            >>> auth = api.authenticate()
            >>> print(auth.access_token)
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
            >>> print(auth.expires_in)
            3600
        """
        url = f"{self.BASE_URL}/authserver-service/oauth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        data = {
            "grant_type": "password",
            "client_id": "machine",
            "username": self.username,
            "password": self.password
        }
        
        logger.info("Выполнение авторизации")
        response = self._make_request("POST", url, headers=headers, data=data)
        auth_response = AuthResponse(**response.json())
        self.access_token = auth_response.access_token
        # Сохраняем время истечения токена (текущее время + expires_in секунд)
        self.token_expires_at = time.time() + auth_response.expires_in
        logger.info(f"Авторизация успешна, токен действителен {auth_response.expires_in} секунд")
        return auth_response
    
    def get_accounts(self) -> List[Account]:
        """
        Получить все аккаунты пользователя
        
        Returns:
            List[Account]: Список всех аккаунтов абонентов
            
        Example:
            >>> accounts = api.get_accounts()
            >>> print(accounts[0].id)
            904154
            >>> print(accounts[0].owner.phone)
            79061343115
            >>> print(accounts[0].company.short_name)
            'Individualniy_predprinimatel_Trofimov_Dmitriy_Gennadevich'
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/accounts"
        headers = self._get_headers()
        
        logger.info("Получение списка аккаунтов")
        response = self._make_request("GET", url, headers=headers)
        accounts_data = response.json()
        # pprint(accounts_data)
        return [Account(**account) for account in accounts_data]

    def get_account_info(self, account_id: int) -> AccountInfo:
        """
        Получить детальную информацию об аккаунте (баланс, подключения, квартиры и т.д.)
        
        Args:
            account_id (int): ID аккаунта
            
        Returns:
            AccountInfo: Объект с детальной информацией об аккаунте
            
        Example:
            >>> account_info = api.get_account_info(904154)
            >>> print(account_info.balance.balance)
            1500.50
            >>> print(account_info.owner.phone)
            79061343115
            >>> print(account_info.company.name)
            'ООО "Домофон Сервис"'
            >>> for connection in account_info.connections:
            ...     print(f"Услуга: {connection.service.name}, Тариф: {connection.tariff}")
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/accounts/{account_id}"
        headers = self._get_headers()
        
        logger.info(f"Получение информации об аккаунте {account_id}")
        response = self._make_request("GET", url, headers=headers)
        return AccountInfo(**response.json())

    def get_account_by_phone(self, phone: int) -> Optional[Account]:
        """
        Получить аккаунт по номеру телефона

        Args:
            phone (int): Номер телефона в формате 79131234567 (без плюса, начинается с 7)
            
        Returns:
            Optional[Account]: Объект с аккаунтом или None если не найден
            
        Example:
            >>> account = api.get_account_by_phone(79308312222)
            >>> if account:
            ...     print(f"ID аккаунта: {account.id}")
            ...     print(f"Заблокирован: {account.blocked}")
        """
        accounts = self.get_accounts()
        for account in accounts:
            if account.owner.phone == phone:
                return account
        return None
        

    def create_account(self, number: str, phone: str) -> CreateAccountResponse:
        """
        Создать новый аккаунт абонента
        
        Args:
            number (str): Номер расчетного счета (должен совпадать с номером в биллинговой системе)
            phone (str): Номер телефона в формате 79131234567 (без плюса, начинается с 7)
            
        Returns:
            CreateAccountResponse: Объект с ID созданного аккаунта и информацией о владельце
            
        Example:
            >>> response = api.create_account("ACC123456", "79061234567")
            >>> print(response.id)
            904155
            >>> print(response.owner.phone)
            79061234567
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/accounts"
        headers = self._get_headers()
        
        request_data = CreateAccountRequest(number=number, phone=phone)
        
        logger.info(f"Создание аккаунта для телефона {phone}")
        response = self._make_request("POST", url, headers=headers, json=request_data.dict(by_alias=True))
        return CreateAccountResponse(**response.json())
    
    def create_flat(self, entrance_id: str, flat_number: str, abonent_id: Optional[int] = None, virtual: bool = False) -> CreateFlatResponse:
        """
        Создать квартиру в подъезде
        
        Args:
            entrance_id (str): Идентификатор подъезда
            flat_number (str): Номер квартиры
            abonent_id (Optional[int]): ID абонента (если известен номер телефона)
            virtual (bool): True если физическая трубка не установлена
            
        Returns:
            CreateFlatResponse: Полный объект квартиры с ID, адресом, владельцем и флагом виртуальности
            
        Example:
            >>> flat = api.create_flat("26959", "1", abonent_id=1574870)
            >>> print(flat.id)
            842554
            >>> print(flat.address.city)
            Чебоксары
            >>> print(flat.address.street.name)
            Филиппа Лукина
            >>> print(flat.owner.id)
            1574870
            >>> print(flat.virtual)
            False
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/flats"
        headers = self._get_headers()
        
        request_data = CreateFlatRequest(
            abonent_id=abonent_id,
            entrance_id=entrance_id,
            flat_number=flat_number,
            virtual=virtual
        )
        
        logger.info(f"Создание квартиры {flat_number} в подъезде {entrance_id}")
        response = self._make_request("POST", url, headers=headers, json=request_data.dict(by_alias=True, exclude_none=True))
        return CreateFlatResponse(**response.json())
    
    def get_entrance_services(self, entrance_id: str) -> List[Service]:
        """
        Получить список всех услуг, доступных для подъезда
        
        Args:
            entrance_id (str): Идентификатор подъезда
            
        Returns:
            List[Service]: Список услуг с их ID, названиями и типами
            
        Example:
            >>> services = api.get_entrance_services("entrance_123")
            >>> print(services[0].name)
            'Чат дома Державина 28'
            >>> print(services[0].type)
            'HouseChat'
            >>> print(services[1].type)
            'VideoSurveillance'
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/entrances/{entrance_id}/services"
        headers = self._get_headers()
        
        logger.info(f"Получение услуг подъезда {entrance_id}")
        response = self._make_request("GET", url, headers=headers)
        services_data = response.json()
        return [Service(**service) for service in services_data]
    
    def connect_service(self, service_id: int, flat_id: int | str, account_id: Optional[int] = None) -> CreateConnectionResponse:
        """
        Подключить услугу к квартире
        
        Args:
            service_id (int): ID услуги (получается из get_entrance_services)
            flat_id (int | str): ID квартиры (получается из create_flat), принимает как int так и str
            account_id (Optional[int]): ID аккаунта (если известен номер телефона)
            
        Returns:
            CreateConnectionResponse: Объект с ID подключения
            
        Example:
            >>> flat = api.create_flat("26959", "42", abonent_id=1480844)
            >>> response = api.connect_service(12345, flat.id, account_id=904154)
            >>> print(response.id)
            789
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/services/{service_id}/connections"
        headers = self._get_headers()
        
        request_data = CreateConnectionRequest(flat_id=flat_id, account_id=account_id)
        
        logger.info(f"Подключение услуги {service_id} к квартире {flat_id}")
        response = self._make_request("POST", url, headers=headers, json=request_data.dict(by_alias=True, exclude_none=True))
        return CreateConnectionResponse(**response.json())
    
    def get_account_connections(self, account_id: int) -> List[Connection]:
        """
        Получить все подключения услуг для аккаунта
        
        Args:
            account_id (int): ID аккаунта
            
        Returns:
            List[Connection]: Список подключений
            
        Example:
            >>> connections = api.get_account_connections(904154)
            >>> print(len(connections))
            3
            >>> print(connections[0].id)
            789
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/accounts/{account_id}/connections"
        headers = self._get_headers()
        
        logger.info(f"Получение подключений аккаунта {account_id}")
        response = self._make_request("GET", url, headers=headers)
        connections_data = response.json()
        return [Connection(**connection) for connection in connections_data]
    
    def get_service_connections(self, service_id: int) -> List[Connection]:
        """
        Получить все подключения для конкретной услуги
        
        Args:
            service_id (int): ID услуги
            
        Returns:
            List[Connection]: Список подключений к данной услуге
            
        Example:
            >>> connections = api.get_service_connections(12345)
            >>> print(len(connections))
            15
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/services/{service_id}/connections"
        headers = self._get_headers()
        
        logger.info(f"Получение подключений услуги {service_id}")
        response = self._make_request("GET", url, headers=headers)
        connections_data = response.json()
        return [Connection(**connection) for connection in connections_data]

    def get_abonent_flats(self, abonent_id: int) -> List[AbonentFlat]:
        """
        Получить все квартиры абонента
        
        Args:
            abonent_id (int): ID абонента
            
        Returns:
            List[AbonentFlat]: Список квартир с адресами
            
        Example:
            >>> flats = api.get_abonent_flats(1574870)
            >>> for flat in flats:
            ...     print(f"Квартира {flat.address.flat}, подъезд {flat.address.entrance.number}")
            ...     print(f"Адрес: {flat.address.city}, {flat.address.street.name} {flat.address.house.number}")
            ...     print(f"Виртуальная: {flat.virtual}")
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/abonents/{abonent_id}/flats"
        headers = self._get_headers()
        
        logger.info(f"Получение квартир абонента {abonent_id}")
        response = self._make_request("GET", url, headers=headers)
        flats_data = response.json()
        return [AbonentFlat(**flat) for flat in flats_data]

    def get_all_services(self) -> List[Service]:
        """
        Получить все услуги с портала РосДомофон
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/services"
        headers = self._get_headers()
        response = self._make_request("GET", url, headers=headers)
        services_data = response.json()
        pprint(services_data)
        # API возвращает объект с пагинацией, нужно взять content
        return [Service(**service) for service in services_data.get('content', [])]
    
    def get_entrances(self, address: Optional[str] = None, page: int = 0, size: int = 20, all: bool = False) -> EntrancesResponse:
        """
        Получить список подъездов с услугами компании
        
        Args:
            address (Optional[str]): Строка адреса для фильтрации подъездов
            page (int): Номер страницы результатов (начиная с 0), игнорируется если all=True
            size (int): Количество записей на странице
            all (bool): Если True, автоматически получит все данные со всех страниц (игнорирует параметр page)
            
        Returns:
            EntrancesResponse: Пагинированный ответ со списком подъездов и их услугами.
                               При all=True возвращает все данные в одном ответе с полным списком в content.
            
        Example:
            >>> # Получить первую страницу подъездов
            >>> entrances = api.get_entrances()
            >>> print(entrances.total_elements)
            25
            >>> 
            >>> # Поиск подъездов по адресу
            >>> entrances = api.get_entrances(address="Москва, Ленина", page=0, size=10)
            >>> for entrance in entrances.content:
            ...     print(f"Подъезд {entrance.id}: {entrance.address_string}")
            ...     for service in entrance.services:
            ...         print(f"  - Услуга: {service.name} ({service.type})")
            ...         print(f"    Камеры: {len(service.cameras)}")
            ...         print(f"    RDA устройства: {len(service.rdas)}")
            >>> 
            >>> # Получить все подъезды автоматически (с пагинацией)
            >>> all_entrances = api.get_entrances(all=True)
            >>> print(f"Получено {len(all_entrances.content)} подъездов из {all_entrances.total_elements}")
            >>> # Обработать все подъезды
            >>> for entrance in all_entrances.content:
            ...     print(f"Подъезд: {entrance.address_string}")
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/entrances"
        headers = self._get_headers()
        
        # Если нужны все данные, выполняем пагинацию автоматически
        if all:
            logger.info("Получение всех подъездов с автоматической пагинацией")
            all_content = []
            current_page = 0
            
            while True:
                params = {"page": current_page, "size": size}
                if address:
                    params["address"] = address
                
                logger.debug(f"Загрузка страницы {current_page + 1} (размер {size})")
                response = self._make_request("GET", url, headers=headers, params=params)
                page_data = EntrancesResponse(**response.json())
                
                all_content.extend(page_data.content)
                
                # Проверяем, есть ли еще страницы
                if page_data.last or len(page_data.content) == 0:
                    logger.info(f"Получено всего {len(all_content)} подъездов")
                    # Возвращаем объединенный результат
                    page_data.content = all_content
                    return page_data
                
                current_page += 1
        else:
            # Обычный запрос одной страницы
            params = {"page": page, "size": size}
            if address:
                params["address"] = address
            
            logger.info(f"Получение списка подъездов (страница {page}, размер {size})")
            response = self._make_request("GET", url, headers=headers, params=params)
            return EntrancesResponse(**response.json())

    def block_account(self, account_number: str) -> bool:
        """
        Заблокировать аккаунт абонента (ограничить доступ ко всем объектам)
        
        Args:
            account_number (str): Номер расчетного счета абонента
            
        Returns:
            bool: True если блокировка прошла успешно
            
        Example:
            >>> success = api.block_account("ACC123456")
            >>> print(success)
            True
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/accounts/{account_number}/block"
        headers = self._get_headers()
        
        logger.info(f"Блокировка аккаунта {account_number}")
        response = self._make_request("PUT", url, headers=headers)
        return response.status_code == 200
    
    def unblock_account(self, account_number: str) -> bool:
        """
        Разблокировать аккаунт абонента (восстановить доступ ко всем объектам)
        
        Args:
            account_number (str): Номер расчетного счета абонента
            
        Returns:
            bool: True если разблокировка прошла успешно
            
        Example:
            >>> success = api.unblock_account("ACC123456")
            >>> print(success)
            True
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/accounts/{account_number}/block"
        headers = self._get_headers()
        
        logger.info(f"Разблокировка аккаунта {account_number}")
        response = self._make_request("DELETE", url, headers=headers)
        return response.status_code == 200
    
    def block_connection(self, connection_id: int) -> bool:
        """
        Заблокировать отдельное подключение услуги
        
        Args:
            connection_id (int): ID подключения
            
        Returns:
            bool: True если блокировка прошла успешно
            
        Example:
            >>> success = api.block_connection(789)
            >>> print(success)
            True
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/services_connections/{connection_id}/block"
        headers = self._get_headers()
        
        logger.info(f"Блокировка подключения {connection_id}")
        response = self._make_request("PUT", url, headers=headers)
        return response.status_code == 200
    
    def unblock_connection(self, connection_id: int) -> bool:
        """
        Разблокировать отдельное подключение услуги
        
        Args:
            connection_id (int): ID подключения
            
        Returns:
            bool: True если разблокировка прошла успешно
            
        Example:
            >>> success = api.unblock_connection(789)
            >>> print(success)
            True
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/services_connections/{connection_id}/block"
        headers = self._get_headers()
        
        logger.info(f"Разблокировка подключения {connection_id}")
        response = self._make_request("DELETE", url, headers=headers)
        return response.status_code == 200
    
    def _send_message(self, to_abonents: List[Union[dict, int]], channel: str, message: str, broadcast: bool = False) -> bool:
        """
        Отправить push-уведомление абонентам
        
        Args:
            to_abonents (List[Union[dict, int]]): Список получателей - словари с полями 'id'/'phone' или просто ID абонентов
            channel (str): Канал сообщения ('support' - чат техподдержки, 'notification' - уведомления)
            message (str): Текст сообщения
            broadcast (bool): True для отправки всем абонентам компании (игнорирует to_abonents)
            
        Returns:
            bool: True если отправка прошла успешно
            
        Example:
            >>> # Отправка по словарям
            >>> recipients = [{'id': 1480844, 'phone': 79061343115}]
            >>> success = api.send_message(recipients, 'support', 'Добро пожаловать!')
            
            >>> # Отправка по ID абонентов
            >>> success = api.send_message([1574870, 1480844], 'support', 'Привет!')
            
            >>> # Broadcast сообщение всем
            >>> success = api.send_message([], 'notification', 'Техработы', broadcast=True)
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/messages"
        headers = self._get_headers()
        
        # Преобразуем входные данные в объекты AbonentInfo
        abonent_objects = []
        for abonent in to_abonents:
            if isinstance(abonent, dict):
                abonent_objects.append(AbonentInfo(**abonent))
            elif isinstance(abonent, int):
                # Если передан просто ID абонента
                abonent_objects.append(AbonentInfo(id=abonent, phone=0))
            else:
                abonent_objects.append(abonent)
        
        request_data = SendMessageRequest(
            to_abonents=abonent_objects,
            channel=channel,
            message=message,
            broadcast=broadcast
        )
        
        logger.info(f"Отправка сообщения в канал {channel}")
        response = self._make_request("POST", url, headers=headers, json=request_data.dict(by_alias=True))
        return response.status_code == 200
    
    def send_message_to_abonent(self, abonent_id: int, channel: str, message: str) -> bool:
        """
        Отправить сообщение конкретному абоненту по ID
        
        Args:
            abonent_id (int): ID абонента
            channel (str): Канал сообщения ('support' - чат техподдержки, 'notification' - уведомления)
            message (str): Текст сообщения
            
        Returns:
            bool: True если отправка прошла успешно
            
        Example:
            >>> success = api.send_message_to_abonent(1574870, 'support', 'Ответ на ваше сообщение')
            >>> print(success)
            True
        """
        recipients = [{'id': abonent_id, 'phone': 0}]
        return self.send_message(recipients, channel, message)
    
    def get_abonent_messages(self, abonent_id: int, channel: Optional[str] = None, page: int = 0, size: int = 20) -> MessagesResponse:
        """
        Получить переписку с абонентом
        
        Args:
            abonent_id (int): ID абонента
            channel (Optional[str]): Канал ('support' для чата техподдержки)
            page (int): Номер страницы (начиная с 0)
            size (int): Размер страницы (количество сообщений)
            
        Returns:
            MessagesResponse: Объект с сообщениями и информацией о пагинации
            
        Example:
            >>> messages = api.get_abonent_messages(1480844, channel='support', page=0, size=10)
            >>> print(messages.total_elements)
            25
            >>> print(messages.content[0].message)
            'Здравствуйте!'
            >>> print(messages.content[0].abonent.phone)
            79061343115
            >>> print(messages.content[0].incoming)
            True
        """
        url = f"{self.BASE_URL}/abonents-service/api/v1/abonents/{abonent_id}/messages"
        headers = self._get_headers()
        
        params = {"page": page, "size": size}
        if channel:
            params["channel"] = channel
        
        logger.info(f"Получение сообщений абонента {abonent_id}")
        response = self._make_request("GET", url, headers=headers, params=params)
        return MessagesResponse(**response.json())
    
    # Методы для работы с Kafka
    def set_kafka_message_handler(self, handler: callable):
        """
        Установить обработчик входящих сообщений из Kafka
        
        Args:
            handler (callable): Функция для обработки входящих сообщений KafkaIncomingMessage
            
        Example:
            >>> def handle_kafka_message(message: KafkaIncomingMessage):
            ...     print(f"Kafka сообщение от {message.from_abonent.phone}: {message.message}")
            ...     # Автоответ через REST API
            ...     api.send_message_to_abonent(
            ...         message.from_abonent.id, 
            ...         'support', 
            ...         f'Получено: {message.message}'
            ...     )
            >>> 
            >>> api.set_kafka_message_handler(handle_kafka_message)
        """
        if not self.kafka_client:
            raise ValueError("Kafka клиент не инициализирован. Укажите kafka_bootstrap_servers и company_short_name при создании API")
        
        self.kafka_client.set_message_handler(handler)
        logger.info("Установлен обработчик Kafka сообщений")
    
    def start_kafka_consumer(self):
        """
        Запустить потребление сообщений из Kafka
        
        Example:
            >>> api.start_kafka_consumer()
            >>> # Сообщения будут обрабатываться в фоне
        """
        if not self.kafka_client:
            raise ValueError("Kafka клиент не инициализирован")
        
        self.kafka_client.start_consuming()
        logger.info("Запущен Kafka consumer")
    
    def stop_kafka_consumer(self):
        """
        Остановить потребление сообщений из Kafka
        
        Example:
            >>> api.stop_kafka_consumer()
        """
        if not self.kafka_client:
            raise ValueError("Kafka клиент не инициализирован")
        
        self.kafka_client.stop_consuming()
        logger.info("Остановлен Kafka consumer")
    
    def set_signup_handler(self, handler: callable):
        """
        Установить обработчик событий регистрации из Kafka
        
        Args:
            handler (callable): Функция для обработки событий регистрации SignUpEvent
            
        Example:
            >>> def handle_signup(signup: SignUpEvent):
            ...     print(f"Новая регистрация абонента {signup.abonent.phone}")
            ...     print(f"Адрес: {signup.address.city}, {signup.address.street.name}")
            ...     print(f"Квартира: {signup.address.flat}")
            ...     # Отправить приветственное сообщение
            ...     api.send_message_to_abonent(
            ...         signup.abonent.id,
            ...         'support',
            ...         'Добро пожаловать в систему РосДомофон!'
            ...     )
            >>> 
            >>> api.set_signup_handler(handle_signup)
        """
        if not self.kafka_client:
            raise ValueError("Kafka клиент не инициализирован. Укажите kafka_bootstrap_servers и company_short_name при создании API")
        
        self.kafka_client.set_signup_handler(handler)
        logger.info("Установлен обработчик событий регистрации")
    
    def start_signup_consumer(self):
        """
        Запустить потребление событий регистрации из Kafka
        
        Example:
            >>> api.start_signup_consumer()
            >>> # События регистрации будут обрабатываться в фоне
        """
        if not self.kafka_client:
            raise ValueError("Kafka клиент не инициализирован")
        
        self.kafka_client.start_signup_consuming()
        logger.info("Запущен Kafka consumer для событий регистрации")
    
    def stop_signup_consumer(self):
        """
        Остановить потребление событий регистрации из Kafka
        
        Example:
            >>> api.stop_signup_consumer()
        """
        if not self.kafka_client:
            raise ValueError("Kafka клиент не инициализирован")
        
        self.kafka_client.stop_signup_consuming()
        logger.info("Остановлен Kafka consumer для событий регистрации")
    
    def set_company_signup_handler(self, handler: callable):
        """
        Установить обработчик событий регистрации из топика компании SIGN_UPS_<company_short_name>
        
        Args:
            handler (callable): Функция для обработки событий регистрации компании SignUpEvent
            
        Example:
            >>> def handle_company_signup(signup: SignUpEvent):
            ...     print(f"Новая регистрация компании: {signup.abonent.phone}")
            ...     print(f"Адрес: {signup.address.city}, {signup.address.street.name}")
            ...     # Отправить приветственное сообщение
            ...     api.send_message_to_abonent(
            ...         signup.abonent.id,
            ...         'support',
            ...         'Добро пожаловать в нашу компанию!'
            ...     )
            >>> 
            >>> api.set_company_signup_handler(handle_company_signup)
        """
        if not self.kafka_client:
            raise ValueError("Kafka клиент не инициализирован. Укажите kafka_bootstrap_servers и company_short_name при создании API")
        
        self.kafka_client.set_company_signup_handler(handler)
        logger.info("Установлен обработчик событий регистрации компании")
    
    def start_company_signup_consumer(self):
        """
        Запустить потребление событий регистрации компании из Kafka
        
        Example:
            >>> api.start_company_signup_consumer()
            >>> # События регистрации компании будут обрабатываться в фоне
        """
        if not self.kafka_client:
            raise ValueError("Kafka клиент не инициализирован")
        
        self.kafka_client.start_company_signup_consuming()
        logger.info("Запущен Kafka consumer для событий регистрации компании")
    
    def stop_company_signup_consumer(self):
        """
        Остановить потребление событий регистрации компании из Kafka
        
        Example:
            >>> api.stop_company_signup_consumer()
        """
        if not self.kafka_client:
            raise ValueError("Kafka клиент не инициализирован")
        
        self.kafka_client.stop_company_signup_consuming()
        logger.info("Остановлен Kafka consumer для событий регистрации компании")
    
    def send_kafka_message(self, 
                          to_abonent_id: int, 
                          to_abonent_phone: int,
                          message: str,
                          company_id: Optional[int] = None) -> bool:
        """
        Отправить сообщение через Kafka (альтернатива REST API)
        
        Args:
            to_abonent_id (int): ID получателя
            to_abonent_phone (int): Телефон получателя
            message (str): Текст сообщения
            company_id (int, optional): ID компании
            
        Returns:
            bool: True если сообщение отправлено успешно
            
        Example:
            >>> success = api.send_kafka_message(
            ...     to_abonent_id=1574870,
            ...     to_abonent_phone=79308316689,
            ...     message="Сообщение через Kafka"
            ... )
            >>> print(success)
            True
        """
        if not self.kafka_client:
            raise ValueError("Kafka клиент не инициализирован")
        
        return self.kafka_client.send_message(
            to_abonent_id=to_abonent_id,
            to_abonent_phone=to_abonent_phone,
            message=message,
            company_id=company_id,
            from_abonent_id=0,  # Системное сообщение
            from_abonent_phone=0
        )
    
    def send_kafka_message_to_multiple(self, 
                                     to_abonents: list,
                                     message: str) -> bool:
        """
        Отправить сообщение нескольким абонентам через Kafka
        
        Args:
            to_abonents (list): Список получателей [{"id": int, "phone": int}]
            message (str): Текст сообщения
            
        Returns:
            bool: True если сообщение отправлено успешно
            
        Example:
            >>> recipients = [
            ...     {"id": 1574870, "phone": 79308312222},
            ...     {"id": 1480844, "phone": 79061343115}
            ... ]
            >>> success = api.send_kafka_message_to_multiple(recipients, "Групповое сообщение")
        """
        if not self.kafka_client:
            raise ValueError("Kafka клиент не инициализирован")
        
        return self.kafka_client.send_message_to_multiple(
            to_abonents=to_abonents,
            message=message,
            from_abonent_id=0,  # Системное сообщение
            from_abonent_phone=0
        )
    
    def close(self):
        """
        Закрыть все соединения (включая Kafka)
        
        Example:
            >>> api.close()
        """
        if self.kafka_client:
            self.kafka_client.close()
        
        self.session.close()
        logger.info("API клиент закрыт")
    
    def __enter__(self):
        """Контекстный менеджер - вход"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход"""
        self.close()

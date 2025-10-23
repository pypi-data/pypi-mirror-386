import json
import random
from importlib import resources

DATA_PATH = 'data/browsers.json'

class UserAgent:
    """Генератор случайных User-Agent'ов с возможностью гибкой фильтрации.
    
    Пример использования:
    ua = UserAgent()
    print(ua.random) 
    print(ua.chrome) 
    print(ua.get_random(browser='Firefox', os='Windows'))
    """

    def __init__(self):
        # Хранит все JSON-объекты для фильтрации
        self._full_data = [] 
        # Инициализируем данные при создании экземпляра
        self._full_data = self._load_data() 
        
    def _load_data(self):
        """Загружает полный список JSON-объектов из встроенного файла."""
        try:
            # Чтение файла
            json_text = resources.read_text('fake_random_useragent', DATA_PATH)
            
            if not json_text:
                return []
                
            # Парсинг JSON
            data_list = json.loads(json_text)
            
            if not isinstance(data_list, list):
                 raise TypeError("JSON-файл должен содержать список объектов.")
                 
            return data_list
                
        except Exception as e:
            # В случае любой ошибки (JSONDecodeError, FileNotFoundError)
            # возвращаем пустой список, чтобы приложение не упало
            return []

    def get_random(self, **filters):
        """
        Возвращает случайный User-Agent, соответствующий заданным фильтрам.
        Фильтрация использует 'содержит' (in) для гибкого поиска.
        """
        # Заглушка, если данные не загружены
        if not self._full_data:
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) (FALLBACK)"

        # Если фильтры не заданы (вызов ua.random), выбираем из всего пула
        if not filters:
            return random.choice(self._full_data).get('useragent', self.get_random(browser='Chrome'))

        filtered_agents = []
        
        # 1. Применяем фильтрацию
        for item in self._full_data:
            is_match = True
            
            # Проверяем каждый переданный фильтр
            for key, expected_value in filters.items():
                
                # Пропускаем недопустимые ключи фильтрации (если они не из данных)
                # Допустимые ключи: browser, os, type, device_brand, os_version
                
                actual_value = item.get(key)
                
                if actual_value is None:
                    # Если ключ фильтра отсутствует в объекте, это не совпадение
                    is_match = False
                    break
                    
                actual_str = str(actual_value).lower()
                expected_str = str(expected_value).lower()
                
                # ГИБКОЕ СОВПАДЕНИЕ: Проверяем, содержится ли ожидаемое значение в фактическом
                if expected_str not in actual_str:
                    is_match = False
                    break

            if is_match and 'useragent' in item:
                filtered_agents.append(item['useragent'])

        # 2. Возвращаем случайный результат из отфильтрованного списка
        if filtered_agents:
            return random.choice(filtered_agents)
        
        # 3. Если ничего не найдено, возвращаем полностью случайный UA
        return self.random 
        
    # --------------------------------------------------------
    # ДИНАМИЧЕСКИЕ СВОЙСТВА (Для удобного доступа: ua.chrome, ua.desktop)
    # --------------------------------------------------------

    @property
    def random(self):
        """Возвращает полностью случайный User-Agent (для ua.random)"""
        return self.get_random()

    @property
    def desktop(self):
        """Случайный агент, где type='desktop'"""
        return self.get_random(type='desktop')

    @property
    def mobile(self):
        """Случайный агент, где type='mobile'"""
        return self.get_random(type='mobile')
        
    @property
    def chrome(self):
        """Случайный агент, где browser='Chrome' (включая Chrome Mobile)"""
        # Используем 'browser' для самого браузера и 'type' для исключения мобильных, если не нужно
        return self.get_random(browser='Chrome')

    @property
    def firefox(self):
        """Случайный агент, где browser='Firefox'"""
        return self.get_random(browser='Firefox')
    
    @property
    def yandex(self):
        """Случайный агент, где browser='Yandex'"""
        return self.get_random(browser='Yandex')
    
    @property
    def safari(self):
        """Случайный агент, где browser='Safari'"""
        return self.get_random(browser='Safari')
    
    @property
    def opera(self):
        """Случайный агент, где browser='Opera'"""
        return self.get_random(browser='Opera')
        
    @property
    def windows(self):
        """Случайный агент, где os='Windows'"""
        return self.get_random(os='Windows')

    @property
    def macos(self):
        """Случайный агент, где os='Mac OS X'"""
        return self.get_random(os='Mac OS X')
        
    # --------------------------------------------------------
    # ПЕРЕОПРЕДЕЛЕНИЕ СТАНДАРТНЫХ МЕТОДОВ (Для print(ua))
    # --------------------------------------------------------

    def __str__(self):
        """Вызывается при print(ua)"""
        return self.random

    def __repr__(self):
        """Отображение объекта"""
        return f"<UserAgent random={self.random[:50]}...>"
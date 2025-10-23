# 🎭 Fake-random-userAgent 🎭

[![PyPI Version](https://img.shields.io/pypi/v/fake-random-useragent.svg)](https://pypi.org/project/fake-random-useragent/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.6+-blue)](https://www.python.org/)

## RU: Случайный User-Agent Генератор для Python

### ✨ О проекте

`Fake-random-userAgent` — это **легковесная** и **эффективная** Python-библиотека для получения случайных, реалистичных строк **User-Agent**. Она разработана специально для нужд веб-скрейпинга, автоматизации и тестирования, помогая вашим HTTP-запросам **избежать блокировок** и выглядеть естественно.

- **Встроенная база данных:** Библиотека поставляется с обширным, встроенным набором данных (более 10 000 актуальных User-Agent), охватывающих все основные операционные системы и браузеры (Chrome, Firefox, Safari, iOS, Android и т.д.).
- **Простота:** Загрузка данных происходит один раз при инициализации класса.

#### 💾 Установка

Библиотека доступна через PyPI. Используйте pip для установки:

```bash
    pip install fake-random-useragent
```

#### 🚀 Использование (Быстрый старт)

Использовать библиотеку максимально просто. Импортируйте класс UserAgent и используйте его динамические свойства для получения нужного агента.

```python
    from fake_random_useragent import UserAgent
    import requests

    ua = UserAgent()

    # 1. Получение случайного агента (любого)
    print(f"Случайный агент (ua.random): {ua.random}")
    # Также работает: print(f"Случайный агент (print(ua)): {ua}")

    # 2. Получение агента по конкретному браузеру/типу (динамические свойства)
    print(f"Только Chrome: {ua.chrome}")
    print(f"Только Яндекс.Браузер: {ua.yandex}")
    print(f"Только Desktop: {ua.desktop}")

    # 3. Использование в HTTP-запросе (Пример с Requests)
    headers = {
        'User-Agent': ua.get_random(browser='yandex', os='win')
    }
    response = requests.get('https://httpbin.org/user-agent', headers=headers)
    print(f"\nUA, отправленный на сервер: {response.json()['user-agent']}")
```

#### ⚙️ Доступные фильтры и свойства

A. Свойства (Прямой доступ через `ua.имя`)

```
Свойство	|  Эквивалент get_random()
––––––––––––––––––––––––––––––––––––––––––––––––
ua.random	|  ua.get_random()
ua.desktop	|  ua.get_random(type='desktop')
ua.mobile	|  ua.get_random(type='mobile')
ua.chrome	|  ua.get_random(browser='chrome')
ua.firefox	|  ua.get_random(browser='firefox')
ua.safari	|  ua.get_random(browser='safari')
ua.yandex	|  ua.get_random(browser='yabrowser')
ua.windows	|  ua.get_random(os='windows')
ua.macos	|  ua.get_random(os='mac os x')
ua.android	|  ua.get_random(os='android')
```

B. Комбинированная фильтрация (ua.get_random())

Используйте метод get_random() для точной настройки по нескольким параметрам одновременно. Фильтрация использует гибкое совпадение (проверяет, что значение содержится в поле).

```
Параметр        | Описание
——————————————————————————————————————
browser         | Название браузера
os              | Операционная система
type            | Тип устройства
device_brand    | Бренд устройства
os_version      | Версия ОС
```

```python
# Пример: Chrome на Android 14
agent = ua.get_random(browser='Chrome', os='Android', os_version='14')

# Пример: Мобильный Firefox на iOS
agent = ua.get_random(browser='Firefox', os='iOS', type='mobile')
```

## EN: Random User-Agent Generator for Python

### ✨ About The Project

`Fake-random-userAgent` is a lightweight and flexible Python library for retrieving random, realistic User-Agent strings. It uses a comprehensive, built-in dataset to generate agents that help your HTTP requests avoid bot detection and appear legitimate.

With its flexible filtering system, you can easily retrieve an agent specific to a particular browser, operating system, or device type.

#### 💾 Installation

The library is available on PyPI. Use pip to install it into your virtual environment:

```bash
    pip install fake-random-useragent
```

#### 🚀 Usage (Quick Start)

Using the library is straightforward. Import the UserAgent class and use its dynamic properties to get the desired agent.

```python
    from fake_random_useragent import UserAgent
    import requests

    ua = UserAgent()

    # 1. Get a completely random agent
    print(f"Random Agent (ua.random): {ua.random}")
    # Also works: print(f"Random Agent (print(ua)): {ua}")

    # 2. Get an agent by specific browser/type (dynamic properties)
    print(f"Only Firefox: {ua.firefox}")
    print(f"Only Safari: {ua.safari}")
    print(f"Only Mobile: {ua.mobile}")

    # 3. Use in an HTTP Request Example (with Requests)
    headers = {
        'User-Agent': ua.get_random(browser='yandex', os='win')
    }
    response = requests.get('https://httpbin.org/user-agent', headers=headers)
    print(f"\nUA sent to server: {response.json()['user-agent']}")
```

#### ⚙️ Available Filters and Properties

A. Properties (Direct access via ua.name)

```
Property	|  Equivalent get_random()
––––––––––––––––––––––––––––––––––––––––––––––––
ua.random	|  ua.get_random()
ua.desktop	|  ua.get_random(type='desktop')
ua.mobile	|  ua.get_random(type='mobile')
ua.chrome	|  ua.get_random(browser='chrome')
ua.firefox	|  ua.get_random(browser='firefox')
ua.safari	|  ua.get_random(browser='safari')
ua.yandex	|  ua.get_random(browser='yabrowser')
ua.windows	|  ua.get_random(os='windows')
ua.macos	|  ua.get_random(os='mac os x')
ua.android	|  ua.get_random(os='android')
```

B. Combined Filtering (ua.get_random())

Use the get_random() method for precise targeting using multiple parameters simultaneously. Filtering uses soft matching (checks if the value is contained within the field).

```
Parameter	|   Description	Example
————————————————––––––––––––––––––––––––––––––––––––––––––––––––––––––––
browser         |   Browser name (Chrome, Firefox, YaBrowser, etc.)
os	        |   Operating System (Windows, iOS, Android, Mac OS X)
type	        |   Device type (desktop, mobile, tablet)
device_brand    |   Device manufacturer (Apple, Samsung, Huawei)
os_version	|   OS version (e.g., '14' for Android 14, '18' for iOS 18)
```

```python
    # Example: Yandex on Windows
    agent = ua.get_random(browser='Yandex', os='Windows')

    # Example: Mobile Chrome on Android 10
    agent = ua.get_random(browser='Chrome', os='Android', os_version='10', type='mobile')
```

#### 🤝 Contributing and License

We welcome contributions, bug reports, and feature suggestions!

License: Distributed under the MIT License. See LICENSE for more information.

    Project Link: https://github.com/RidersWeb/Fake-random-userAgent

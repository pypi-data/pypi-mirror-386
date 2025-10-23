<div align="center">

# quik_python  

[![PyPi Release](https://img.shields.io/pypi/v/quik_python?color=32a852&label=PyPi)](https://pypi.org/project/quik_python/)
[![Total downloads](https://img.shields.io/pepy/dt/quik_python?label=%E2%88%91&color=skyblue)](https://pypistats.org/packages/quik_python)
[![Made with Python](https://img.shields.io/badge/Python-3.11+-c7a002?logo=python&logoColor=white)](https://python.org "Go to Python homepage")
[![License](https://img.shields.io/github/license/Alex-Shur/quik_python?color=9c2400)](https://github.com/Alex-Shur/quik_python/blob/master/LICENSE)
</div>



**QUIK Python** представляет все функции и события, доступные в QLUA, 
в виде асинхронных функций Python и событий. 
Проект является портированием на Python библиотеки C# [QUIKSharp](https://github.com/finsight/QUIKSharp) .


Установка
================
```
pip install quik-python
```

Использование
================
Cкопировать содержимое папки **lua** c [GIT репозитария](https://github.com/Alex-Shur/quik_python) 
в отдельную папку, которая будет доступна приложению QUIK.

> ***ВНИМАНИЕ** Для корректной работы с получением свечных данных используйте обновлённые Lua скрипты из [QUIK Python](https://github.com/Alex-Shur/quik_python)
Данные Lua скрипты будут также корректно работать и с QUIKSharp клиентами.*

В терминале QUIK, через диалоговое окно работы со скриптами Lua, запустить "QuikSharp.lua" из скопированной ранее папки. [Подробнее о Lua скриптах](lua/USAGE.RU.md).
Возможно, перед запуском скрипта, для его нормальной работы, на компьютере с терминалом потребуется установить DLL библиотеки c сайта MS 
https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-supported-redistributable-version
для [CPU X64] https://aka.ms/vs/17/release/vc_redist.x64.exe

Для первичного ознакомпления с основными возможностями библиотеки и синтаксисом некоторых команд, 
можно использовать приложение "QuikPythonDemo" из папки \\Examples.
Все указанные демонстрационные приложения оттестированы и полностью работоспособны.

В случае возникновения проблем с работоспособностью демонстрационных приложений убедитесь что:
1. Терминал QUIK загружен и подключен к сереверу.
2. Скрипт QuikSharp.lua запущен и не выдает никаких ошибок в соответствующем диалоговом окне.
3. Никакие сторонние программы не используют для своих нужд порты 34130 и 34131. 
    Данные порты используются по умолчанию для связи библиотеки с терминалом.
4. Проверьте настройки что соединения не блокируются в Windows Firewall. 

```python
import logging
import asyncio
# from email import message
from quik_python import Quik, LuaException
from quik_python.data_structures import CandleInterval, Candle, InfoParams

CLASS_CODE = "TQBR"   
# CLASS_CODE = "QJSIM"  ## for Demo Quik Junior Connection


async def main():
    """
    Пример использования QuikPython API
    """
    
    # Создаем подключение к QUIK
    # async with Quik(host="192.168.10.128") as quik:
    async with Quik(host="localhost") as quik:
        try:
            await quik.initialize()
            # Работа с QUIK
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return

        try:
            # Проверяем подключение
            if not quik.is_service_alive():
                print("Не удалось подключиться к QUIK")
                return

            if not await quik.service.is_connected():
                print("Quik не подключен к торгам")


            print("Подключение к QUIK успешно!")

            await test_candle(quik=quik)



        except LuaException as e:
            print(f"QUIK Lua error: {e}")
        except Exception as e:
            print(f"Error: {e}")



### test candle
async def test_candle(quik:Quik):
    received_candles = []
    
    def on_new_candle(candle: Candle):
        """Callback for new candle events"""
        if (candle.sec_code == "SBER" and candle.interval == CandleInterval.M1):
            print(f"New candle - Sec:{candle.sec_code}, Open:{candle.open}, "
                  f"Close:{candle.close}, Volume:{candle.volume}")
            received_candles.append(candle)

    try:
        # Проверяем подключение
        if not await quik.service.is_connected():
            print("QUIK не подключен к торгам")
            return
        
        print("QUIK service is connected")

        v = await quik.candles.get_last_candles(CLASS_CODE, "SBER", CandleInterval.M1, 10)
        print(f"Last candles: {v}")


        # Subscribe to new candle events
        quik.candles.add_new_candle_handler(on_new_candle)
        
        # Check if already subscribed and unsubscribe if needed
        is_subscribed = await quik.candles.is_subscribed(CLASS_CODE, "SBER", CandleInterval.M1)
        print(f"Is subscribed: {is_subscribed}")
        if is_subscribed:
            await quik.candles.unsubscribe(CLASS_CODE, "SBER", CandleInterval.M1)

        # Subscribe to minute candles
        await quik.candles.subscribe(CLASS_CODE, "SBER", CandleInterval.M1)

        # Verify subscribed
        is_subscribed = await quik.candles.is_subscribed(CLASS_CODE, "SBER", CandleInterval.M1)
        print(f"Is subscribed: {is_subscribed}")
        
        # Wait a bit for potential candles (but don't wait too long in tests)
        await asyncio.sleep(120) ## wait 180sec
        
        # Unsubscribe
        await quik.candles.unsubscribe(CLASS_CODE, "SBER", CandleInterval.M1)

        print(f"Received {len(received_candles)} candles during test")

    except Exception as e:
        print(f"Candle test error: {e}")


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.DEBUG,  # Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат сообщений
        datefmt='%Y-%m-%d %H:%M:%S'  # Формат времени
    )

    
    print("QuikPython API Example")
    print("===========================")
    

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Main example error: {e}")
```



Решение проблем
---------------
В случае возникновения проблем ознакомьтесь напишите в [Проблемы](https://github.com/Alex-Shur/quik_python/issues)  или в [**Дискуссии**](https://github.com/Alex-Shur/quik_python/discussions) .
Постарайтесь описать проблему как можно подробнее, с деталями того, что
Вы конкретно делаете и что не работает или работает неправильно.


License
----------------------

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

This software is distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

# LiveTemplate

**LiveTemplate** — это инструмент для локальной разработки и тестирования Telegram-ботов, который упрощает работу с шаблонами сообщений и позволяет видеть результат изменений сразу, без перезапуска бота.

---

## 🚀 Основные преимущества
- **Локальное использование** — работает только в вашей тестовой среде, без отправки шаблонов в сторонние сервисы.
- **Простота** — лёгкая установка, быстрая интеграция и интуитивное использование.
- **Быстрая обратная связь** — изменения в шаблоне отображаются мгновенно в боте.

---

## 📦 Установка

```bash
pip install live-template[aiogram]
````

---

## ⚙️ Быстрый старт

```python
import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from live_template import AiogramRouter

async def main():
    from dotenv import load_dotenv

    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    lt_router = AiogramRouter("../templates", {})
    dp.include_router(lt_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🧩 Как это работает

1. Устанавливаете **LiveTemplate**.
2. Подключаете `lt_router` к вашему `Dispatcher`.
3. Запускаете бота в локальном окружении.
4. Получаете доступ к шаблонам сообщений прямо в боте.
5. Меняете шаблон — и сразу видите результат без перезапуска.

---

## ✨ Фичи

### 1. Always Retry

При включённой опции бот автоматически отправляет новое сообщение сразу после сохранения изменений в шаблоне или добавления нового.

### 2. Show All

Отправляет все сообщения по вашим шаблонам за один запрос.

---


## 🔄 Сравнение с классическим процессом

| Классический процесс                             | С LiveTemplate (Always Retry mode) |
| ------------------------------------------------ | ---------------------------------- |
| 1. Изменить шаблон                               | 1. Изменить шаблон                 |
| 2. Запустить бота                                | 2. Увидеть сообщение               |
| 3. Дойти до нужной команды, вызывающей сообщение | 3. Повторить                       |
| 4. Увидеть сообщение                             |                                    |
| 5. Остановить бота                               |                                    |
| 6. Повторить                                     |                                    |

---

## 📄 Лицензия

MIT License

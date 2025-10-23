"""
Valera Bot - Умный Telegram бот на Smart Bot Factory
"""

import asyncio
from smart_bot_factory.router import EventRouter
from smart_bot_factory.message import send_message_by_human
from smart_bot_factory.creation import BotBuilder

# Инициализация
event_router = EventRouter("valera")
bot_builder = BotBuilder("valera")

# =============================================================================
# ОБРАБОТЧИКИ СОБЫТИЙ
# =============================================================================

@event_router.event_handler("collect_contact", notify=True, once_only=True)
async def handle_contact(user_id: int, contact_data: str):
    """
    Обрабатывает получение контактных данных
    
    ИИ создает: {"тип": "collect_contact", "инфо": "+79001234567"}
    """
    await send_message_by_human(
        user_id=user_id,
        message_text=f"✅ Спасибо! Ваши данные сохранены: {contact_data}"
    )
    
    return {"status": "success", "contact": contact_data}

# =============================================================================
# ЗАПУСК
# =============================================================================

async def main():
    # ========== РЕГИСТРАЦИЯ РОУТЕРОВ ==========
    bot_builder.register_routers(event_router)
    
    # Можно добавить Telegram роутеры:
    # from aiogram import Router
    # telegram_router = Router(name="commands")
    # bot_builder.register_telegram_router(telegram_router)
    
    # ========== КАСТОМИЗАЦИЯ (до build) ==========
    # Установить кастомный PromptLoader:
    # from smart_bot_factory.utils import UserPromptLoader
    # custom_loader = UserPromptLoader("valera")
    # bot_builder.set_prompt_loader(custom_loader)
    
    # ========== СБОРКА И ЗАПУСК ==========
    await bot_builder.build()
    await bot_builder.start()

if __name__ == "__main__":
    asyncio.run(main())

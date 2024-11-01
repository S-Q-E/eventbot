import logging

logger = logging.getLogger(__name__)

import asyncio
from aiogram.types import BotCommand
# from middlewares.registration_middleware import RegistrationMiddleware
from config.config import load_config, Config
from aiogram import Bot, Dispatcher
# from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import (
    main_menu,
    reminder,
    my_events,
    join_event,
    events_list,
    start_command,
    create_event,
    registration,
    user_list,
    set_admin
)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s "
               "[%(asctime)s] - %(name)s - %(message)s",
    )

    logger.info("Starting bot")

    config: Config = load_config()

    # default_properties = DefaultBotProperties(parse_mode="HTML")

    bot: Bot = Bot(token=config.tg_bot.token)
    dp: Dispatcher = Dispatcher(storage=MemoryStorage())
    # dp.message.middleware(RegistrationMiddleware())
    # dp.callback_query.middleware(RegistrationMiddleware())

    dp.include_router(start_command.start_router)
    dp.include_router(main_menu.main_menu_router)
    dp.include_router(events_list.event_list_router)
    dp.include_router(create_event.create_event_router)
    dp.include_router(my_events.my_event_router)
    dp.include_router(reminder.reminder_router)
    dp.include_router(join_event.event_join_router)
    dp.include_router(registration.registration_router)
    dp.include_router(user_list.user_list_router)
    dp.include_router(set_admin.set_admin_router)

    commands = [
        BotCommand(command="main_menu", description="Главное меню"),
        BotCommand(command="events_list", description="Все события"),
        BotCommand(command="my_events", description="Мои записи"),
        BotCommand(command="start", description="Запустить бота"),
    ]

    await bot.set_my_commands(commands)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")

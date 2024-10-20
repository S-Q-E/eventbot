from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_commands():
    commands = [BotCommand(command='start', description='Старт'),
                BotCommand(command='profile', description='Мой профиль')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())
from dataclasses import dataclass

from dotenv import load_dotenv

from config.base import getenv


@dataclass
class TelegramBotConfig:
    token: str
    bot_username: str


@dataclass
class Config:
    tg_bot: TelegramBotConfig


def load_config() -> Config:
    load_dotenv()

    return Config(
        tg_bot=TelegramBotConfig(
            token=getenv("BOT_TOKEN"),
            bot_username=getenv("BOT_USERNAME")
        )
    )


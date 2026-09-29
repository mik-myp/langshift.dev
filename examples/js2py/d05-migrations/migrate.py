from pathlib import Path
from alembic.config import Config
from alembic import command
from safety import checked_url


def configuration(url=None):
    config = Config(str(Path(__file__).with_name("alembic.ini")))
    config.attributes["database_url"] = checked_url(url)
    return config


def upgrade(url=None, revision="head"):
    command.upgrade(configuration(url), revision)

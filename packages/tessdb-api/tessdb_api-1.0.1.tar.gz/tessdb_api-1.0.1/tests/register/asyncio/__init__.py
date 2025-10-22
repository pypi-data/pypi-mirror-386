from lica.sqlalchemy.asyncio.dbase import create_engine_sessionclass

engine, Session = create_engine_sessionclass(env_var="DATABASE_ASYNC_URL", tag="tessdb")

__all__ = ["engine", "Session"]

import sqlite3
import os
from datetime import datetime
from src.logger import Logger
from discord import Guild, Member

from src.db.bot_sql import TABLES, EVENT_TYPES

class Database(object):
    def __init__(self, logger: Logger):
        path = os.getenv("DB_PATH", "~/data/bot.db")
        self.connection = sqlite3.connect(path)
        self.logger = logger
        self.check_db()
        self.logger.info('DB Init completo')

    def check_db(self) -> bool:
        for tb in TABLES:
            if not self.check_table(tb):
                self.logger.info(f'Creating: {tb}')
                self.execute_sql(TABLES[tb])
                if tb == "TB_EVENT_TYPE":
                    query = "INSERT INTO TB_EVENT_TYPE(ID, NAME) VALUES"
                    values = []
                    for ev in EVENT_TYPES:
                        values.append(f"({ev.value},'{ev.name}')")
                    values = ','.join(values)
                    query += values
                    self.execute_sql(query)

    def check_table(self, tb_name: str) -> bool:
        query = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{tb_name}'"
        cursor = self.connection.cursor()
        cursor.execute(query.format(tb_name=tb_name))
        if cursor.fetchone()[0]==1:
            self.logger.info(f'{tb_name}: existe')
            cursor.close()
            return True
        else:
            self.logger.info(f'{tb_name}: nao existe')
            cursor.close()
            return False
    
    def execute_sql(self, query: str, args=None):
        try:
            cursor = self.connection.cursor()
            self.logger.info(f'Running query: {query}')
            if args:
                self.logger.info(f'Args: {args}')
                cursor.execute(query, args)
            else:
                cursor.execute(query)
            self.logger.info('Execucao completa.')
            self.connection.commit()
            self.logger.info('Transacao commitada.')
        except Exception as err:
            self.logger.error(err)
            self.connection.rollback()
        finally:
            cursor.close()

    def insert_event(self, user_id: int, event_type_id: int, guild_id:int, desc=None) -> bool:
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        query = f"""
        INSERT INTO TB_EVENTS(ID_USER, ID_EVENT_TYPE, ID_GUILD, DS_EVENT, DH_EVENT) 
        VALUES({user_id}, {event_type_id}, {guild_id}, '{desc}', '{timestamp}')
        """
        self.execute_sql(query)

    def check_guilds_and_users(self, guilds: list):
        for guild in guilds: 
            if len(self.fetch_result(f"SELECT ID FROM TB_GUILD WHERE ID=?", (guild.id,))) < 1:
                self.execute_sql(f"INSERT INTO TB_GUILD VALUES(?, ?)", (guild.id, guild.name))
            for member in guild.members:
                if len(self.fetch_result(f"SELECT ID FROM TB_USER WHERE ID=?", (member.id,))) < 1:
                    is_bot = 1 if member.bot else 0
                    self.execute_sql(f"INSERT INTO TB_USER VALUES(?,?,?)", (member.id, member.name, is_bot))

    def fetch_result(self, query:str, args=None) -> list:
        try:
            self.logger.info(f'Consultando query: {query}')
            cursor = self.connection.cursor()
            if args:
                self.logger.info(f'Args: {args}')
                cursor.execute(query, args)
            else:
                cursor.execute(query)
            res = cursor.fetchall()
            if res:
                self.logger.info(f"A consulta retornou '{len(res)}' linhas")
            else: 
                self.logger.info("A consulta não retornou resultados.")
            return res
        except Exception as err:
            self.logger.error(err)
        finally:
            cursor.close()

    def __del__(self):
        self.connection.close()
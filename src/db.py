import psycopg2
from psycopg2.extras import execute_values 
from typing import List, Optional
from .models import WebResourceConfig, ResultRecord


class DatabaseManagerException(Exception):
    pass

class DatabaseManager:
    def __init__(self, conn):
        self.conn = conn

    def init_database(self):
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS monitor_queue (
                        id SERIAL PRIMARY KEY,
                        url TEXT NOT NULL,
                        check_interval INTEGER NOT NULL,
                        pattern TEXT,
                        next_check TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS 
                        idx_monitor_queue_next_check 
                    ON monitor_queue (next_check)
                """)
                cur.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS 
                        idx_monitor_queue_url_interval
                    ON monitor_queue (url, check_interval)
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS monitor_metrics (
                        id SERIAL PRIMARY KEY,
                        url TEXT NOT NULL,
                        check_timestamp TIMESTAMP NOT NULL,
                        response_time FLOAT,
                        status_code INTEGER,
                        pattern_found BOOLEAN,
                        error_message TEXT
                    )
                """)

                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise DatabaseManagerException(f"Failed to initialize database: {e}")
        
    def insert_into_the_queue(self, config: WebResourceConfig):
        query = """INSERT INTO monitor_queue (url, check_interval, pattern, next_check) 
            VALUES (%s, %s, %s, NOW() + INTERVAL %s)"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (
                    config.url,
                    config.interval,
                    config.pattern,
                    f"{config.interval} seconds",
                ))
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise DatabaseManagerException(f"Failed to insert into the queue: {e}")
        
    def get_next_task(self) -> Optional[List[str]]:
        query = """
            WITH next_task AS (
                SELECT id, url, check_interval, pattern 
                FROM monitor_queue 
                WHERE next_check <= NOW()
                LIMIT 1 FOR UPDATE SKIP LOCKED
            ) 
            UPDATE monitor_queue set next_check = NOW() + (next_task.check_interval || ' seconds')::INTERVAL
            FROM next_task
            WHERE monitor_queue.id = next_task.id 
            RETURNING next_task.url, next_task.pattern;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                task = cur.fetchone()
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise DatabaseManagerException(f"Failed to get next task: {e}")
        finally:
            if task:
                return task

    def insert_records(self, records: List[ResultRecord]):
        values = [(
            result.url,
            result.timestamp,
            result.response_time,
            result.status_code,
            result.re_pattern_found,
            result.error_message
        ) for result in records]
        if not values:
            return
        query = """
            INSERT INTO monitor_metrics (url, check_timestamp, response_time, status_code, pattern_found, error_message)
            VALUES %s
        """
        template = "(%s, %s, %s, %s, %s, %s)"
        try:
            with self.conn.cursor() as cur:
                execute_values(cur, query, values, template)
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise DatabaseManagerException(f"Failed to insert records: {e}")

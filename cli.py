import psycopg2
from src.db import DatabaseManager
from src.models import WebResourceConfig
from click import group, option, pass_context, argument, BadArgumentUsage

@group()
@option("--host", help="Database host", type=str)
@option("--port", help="Database port" ,type=int)
@option("--user", help="Database user", type=str)
@option("--password", help="Database password", prompt=True, hide_input=True, type=str)
@option("--dbname", help="Database name", type=str)
@option("--secure", help="Use secure connection", is_flag=True, default=False)
@pass_context
def cli(ctx, host, port, user, password, dbname, secure):
    ctx.ensure_object(dict)
    ctx.obj["host"] = host
    ctx.obj["port"] = port
    ctx.obj["user"] = user
    ctx.obj["password"] = password
    ctx.obj["dbname"] = dbname
    ctx.obj["sslmode"] = 'disable'
    if secure:
        ctx.obj["sslmode"] = "require"

@cli.command("init-db")
@pass_context
def init_db(ctx):
    """Create database schema"""
    conn = psycopg2.connect(
        dbname=ctx.obj["dbname"],
        user=ctx.obj["user"],
        password=ctx.obj["password"],
        host=ctx.obj["host"],
        port=ctx.obj["port"],
        sslmode=ctx.obj["sslmode"]
    )
    DatabaseManager(conn).init_database()
    print("Database initialized successfully")

@cli.command("insert-resource")
@argument("url", type=str)
@argument("interval", type=int)
@argument("pattern", required=False, type=str)
@pass_context
def insert_resource(ctx, url, interval, pattern):
    """
    Add new resource for minitoring

    \b
    URL - name of http resource.
    INTERVAL - monitoring interval in seconds, from 5 till 300.
    PATTERN - regexp pattern to match text on resource, OPTIONAL.
    """
    if not WebResourceConfig.validate_interval(interval=interval):
        raise BadArgumentUsage("Interval should be in range between 5 and 300 seconds!")
    config = WebResourceConfig(url, interval, pattern)
    conn = psycopg2.connect(
        dbname=ctx.obj["dbname"],
        user=ctx.obj["user"],
        password=ctx.obj["password"],
        host=ctx.obj["host"],
        port=ctx.obj["port"],
        sslmode=ctx.obj["sslmode"]
    )
    db = DatabaseManager(conn)
    db.insert_into_the_queue(config)
    print("Resource added to the queue")

if __name__ == "__main__":
    cli(obj={})
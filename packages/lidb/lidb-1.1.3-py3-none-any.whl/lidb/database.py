# -*- coding: utf-8 -*-
"""
---------------------------------------------
Copyright (c) 2025 ZhangYundi
Licensed under the MIT License.
Created on 2024/7/1 09:44
Email: yundi.xxii@outlook.com
---------------------------------------------
"""
import re
from pathlib import Path
from .parse import extract_table_names_from_sql
from .init import DB_PATH, logger, get_settings
import urllib
import polars as pl

# ======================== 本地数据库 catdb ========================
def tb_path(tb_name: str) -> Path:
    """
    返回指定表名 完整的本地路径
    Parameters
    ----------
    tb_name: str
       表名，路径写法: a/b/c
    Returns
    -------
    pathlib.Path
        full_abs_path: pathlib.Path
        完整的本地绝对路径 $DB_PATH/a/b/c
    """
    return Path(DB_PATH, tb_name)


def put(df, tb_name: str, partitions: list[str] | None = None, abs_path: bool = False):
    """
    将一个DataFrame写入到指定名称的表格目录中，支持分区存储。

    该函数负责将给定的DataFrame（df）根据提供的表名（tb_name）写入到本地文件系统中。
    如果指定了分区（partitions），则会按照这些分区列将数据分割存储。此外，可以通过abs_path参数
    指定tb_name是否为绝对路径。如果目录不存在，会自动创建目录。

    Parameters
    ----------
    df: polars.DataFrame
    tb_name: str
        表的名称，用于确定存储数据的目录
    partitions: list[str] | None
        指定用于分区的列名列表。如果未提供，则不进行分区。
    abs_path: bool
        tb_name是否应被视为绝对路径。默认为False。

    Returns
    -------

    """
    if df is None:
        logger.warning(f"put failed: input data is None.")
        return
    if df.is_empty():
        logger.warning(f"put failed: input data is empty.")
        return
    if not abs_path:
        tbpath = tb_path(tb_name)
    else:
        tbpath = Path(tb_name)
    if not tbpath.exists():
        tbpath.mkdir(parents=True, exist_ok=True)
    if partitions is not None:
        df.write_parquet(tbpath, partition_by=partitions)
    else:
        df.write_parquet(tbpath / "data.parquet")

def has(tb_name: str) -> bool:
    """
    判定给定的表名是否存在
    Parameters
    ----------
    tb_name: str

    Returns
    -------

    """
    return tb_path(tb_name).exists()

def sql(query: str, abs_path: bool = False):
    """
    sql 查询，从本地paquet文件中查询数据

    Parameters
    ----------
    query: str
        sql查询语句
    abs_path: bool
        是否使用绝对路径作为表路径。默认为False
    Returns
    -------

    """
    import polars as pl

    tbs = extract_table_names_from_sql(query)
    convertor = dict()
    for tb in tbs:
        if not abs_path:
            db_path = tb_path(tb)
        else:
            db_path = tb
        format_tb = f"read_parquet('{db_path}/**/*.parquet')"
        convertor[tb] = format_tb
    pattern = re.compile("|".join(re.escape(k) for k in convertor.keys()))
    new_query = pattern.sub(lambda m: convertor[m.group(0)], query)
    return pl.sql(new_query)

def scan(tb: str, abs_path: bool = False) -> pl.LazyFrame:
    """polars.scan_parquet"""

    if not abs_path:
        tb = tb_path(tb)
    return pl.scan_parquet(tb)

def read_mysql(query: str, db_conf: str = "DATABASES.mysql"):
    """
    从MySQL数据库中读取数据。
    Parameters
    ----------
    query: str
        查询语句
    db_conf: str
        对应的配置 $DB_PATH/conf/settings.toml
    Returns
    -------
    polars.DataFrame
    """
    import polars as pl
    try:
        db_setting = get_settings().get(db_conf, {})
        required_keys = ['user', 'password', 'url', 'db']
        missing_keys = [key for key in required_keys if key not in db_setting]
        if missing_keys:
            raise KeyError(f"Missing required keys in database config: {missing_keys}")

        user = urllib.parse.quote_plus(db_setting['user'])
        password = urllib.parse.quote_plus(db_setting['password'])
        uri = f"mysql://{user}:{password}@{db_setting['url']}/{db_setting['db']}"
        return pl.read_database_uri(query, uri)

    except KeyError as e:
        raise RuntimeError("Database configuration error: missing required fields.") from e
    except Exception as e:
        raise RuntimeError(f"Failed to execute MySQL query: {e}") from e


def read_ck(query: str, db_conf: str = "DATABASES.ck"):
    """
    从Clickhouse集群读取数据。
    Parameters
    ----------
    query: str
        查询语句
    db_conf: str
        对应的配置 $DB_PATH/conf/settings.toml
    Returns
    -------
    polars.DataFrame
    """
    import clickhouse_df
    try:
        db_setting = get_settings().get(db_conf, {})
        required_keys = ['user', 'password', 'urls']
        missing_keys = [key for key in required_keys if key not in db_setting]
        if missing_keys:
            raise KeyError(f"Missing required keys in database config: {missing_keys}")

        user = urllib.parse.quote_plus(db_setting['user'])
        password = urllib.parse.quote_plus(db_setting['password'])

        with clickhouse_df.connect(db_setting['urls'], user=user, password=password):
            return clickhouse_df.to_polars(query)

    except KeyError as e:
        raise RuntimeError("Database configuration error: missing required fields.") from e
    except Exception as e:
        raise RuntimeError(f"Failed to execute ClickHouse query: {e}") from e
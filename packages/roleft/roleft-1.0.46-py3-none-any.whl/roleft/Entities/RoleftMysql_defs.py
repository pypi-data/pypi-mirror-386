from datetime import datetime
from decimal import Decimal
import sys, os, pymysql


sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "."))
from Extentions.xdatetime_defs import xdatetime
from Extentions.xfloat_defs import xfloat
from Extentions.xstr_defs import xstr
from Extentions.xdict_defs import xdict
from dacite import Config, from_dict

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dataclasses import dataclass
from typing import Any, Dict, Optional, Type, TypeVar, Union
from pymysql.connections import Connection
from pymysql.cursors import Cursor

from Extentions.xlist_defs import xlist

from abc import ABC
from dataclasses import dataclass
from Extentions.xdatetime_defs import xdatetime
from Extentions.xDecimal_def import xDecimal


# TNumUnn = TypeVar("TNumUnn", bound=Union[int, float])
TBaseTypes = TypeVar("TBaseTypes", int, float, str, Decimal)
T = TypeVar("T")


@dataclass
class MpnBase(ABC):
    Id: int
    CreateTime: xdatetime


_TYPE_MAP = {
    float: xfloat,
    datetime: xdatetime,
    str: xstr,
    Decimal: xDecimal,
}

# 【闻祖东 2025-10-24 110920】因为此处已经确保传入的dict是已经是x类型，所以可以指定不用再做类型检查
_config_no_check = Config(check_types=False)


def _cvt_to_x(input: Any) -> Any:
    if isinstance(input, (xfloat, xdatetime, xstr, xDecimal)):
        return input
    if isinstance(input, dict):
        return xdict({k: _cvt_to_x(v) for k, v in input.items()})
    if isinstance(input, (list, tuple)):
        return xlist(_cvt_to_x(i) for i in input)
    if type(input) in _TYPE_MAP:
        # 【闻祖东 2025-10-24 111226】标记为删除，确定无误就删除
        if isinstance(input, datetime):
            return xdatetime.x_from(input)
        else:
            return _TYPE_MAP[type(input)](input)
    else:
        return input


@dataclass
class DbConfig4Mysql:
    host: str
    port: int
    db: str
    user: str
    pwd: str


class QueryObject4Mysql:
    def __init__(self, cfg: DbConfig4Mysql) -> None:
        self._cfg = cfg

    def __get_conn(self) -> Connection:
        cfg = self._cfg
        return pymysql.connect(
            host=cfg.host,
            port=cfg.port,
            database=cfg.db,
            user=cfg.user,
            password=cfg.pwd,
        )

    # 【闻祖东 2025-10-13 104331】坚决不要使用 params: dict = {} 这样的 可变默认参数（Critical）
    def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> int:
        with self.__get_conn() as conn:
            try:
                cursor: Cursor
                with conn.cursor() as cursor:
                    return cursor.execute(sql, params)
            finally:
                conn.commit()

    def query_dicts(
        self, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> xlist[dict]:
        with self.__get_conn() as conn:
            try:
                cursor: Cursor = conn.cursor()
                cursor.execute(sql, params)
                names = xlist(cursor.description).x_map(lambda col: col[0])
                values_tuples = xlist(cursor.fetchall())

                return values_tuples.x_map(
                    lambda values: _cvt_to_x(dict(zip(names, values)))
                )
            finally:
                conn.commit()

    def query_mpns(
        self, data_class: Type[T], sql: str, params: Optional[Dict[str, Any]] = None
    ) -> xlist[T]:
        return self.query_dicts(sql, params).x_map(
            lambda dct: from_dict(data_class, dct, _config_no_check)
        )

    def query_mpn(
        self, data_class: Type[T], sql: str, params: Optional[Dict[str, Any]] = None
    ) -> T | None:
        mpns = self.query_mpns(data_class, sql, params)
        return mpns[0] if len(mpns) else None
        # return mpns.x_first()

    def query_tuple_values(
        self, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> xlist:
        """【闻祖东 2024-02-05 164459】将原始的信息返回回来, 一般用于调试。"""
        with self.__get_conn() as conn:
            try:
                cursor: Cursor = conn.cursor()
                cursor.execute(sql, params)
                return xlist(cursor.fetchall())
            finally:
                conn.commit()

    def query_base_types(
        self,
        data_class: Type[TBaseTypes],
        sql: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> xlist[TBaseTypes]:
        """【闻祖东 2024-02-05 164050】适用于返回单列的情况"""
        drafts = self.query_tuple_values(sql, params)
        return drafts.x_map(lambda x: x[0])


if __name__ == "__main__":
    dct = {
        "just_name": Decimal(34.3),
        "dt": datetime.now(),
        "flt": float(23.4),
        "xstrdd": str("abc"),
    }

    new = _cvt_to_x(dct)
    xstrdd: xstr = new["xstrdd"]
    isip = xstrdd.x_is_ipv4
    # dt = xdatetime.now()
    # dt = xdatetime(datetime.now())
    pass

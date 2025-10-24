from decimal import Decimal
from typing import Type, TypeVar, Union
from Extentions.xfloat_defs import xfloat

T = TypeVar("T", bound="xDecimal")


class xDecimal(Decimal):
    def __new__(cls: Type[T], value: Union[float, int, str, Decimal] = 0.0) -> T:
        """创建 xfloat 实例"""
        return super().__new__(cls, value)

    def x_to_percent(self, decimals: int = 2) -> str:
        return xfloat(self).x_to_percent(decimals)

    def x_to_percentCN(self, decimals: int = 2) -> str:
        return xfloat(self).x_to_percentCN(decimals)

    def x_intro_as_wan(self, decimals: int = 2) -> str:
        return xfloat(self).x_intro_as_wan(decimals)


if __name__ == "__main__":
    dcm = Decimal(23)
    x = xDecimal(dcm)
    wan = x.x_intro_as_wan()
    # dt = xdatetime.now()
    # dt = xdatetime(datetime.now())
    pass

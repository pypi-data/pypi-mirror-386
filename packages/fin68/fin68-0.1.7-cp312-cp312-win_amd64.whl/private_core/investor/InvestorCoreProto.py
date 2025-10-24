# private_core/investor/InvestorCoreProto.py
from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol, Sequence, Union, runtime_checkable
import pandas as pd

if TYPE_CHECKING:
    from private_core.http_core import HttpSession

InvestorGroup = Literal[
    "foreign",
    "proprietary",
    "local_institutional",
    "local_individual",
    "foreign_institutional",
    "foreign_individual",
    "all",
]
SymbolArg = Union[str, Sequence[str]]
Interval = Literal["1D", "1W", "1M"]  # đồng bộ với helper._ALLOWED_INTERVALS (EOD)

@runtime_checkable
class InvestorCoreProto(Protocol):
    """
    Contract mà private_core phải tuân theo cho investor.*.

    Core implementors must expose an HttpSession via `session` so they can call APIs directly.

    Parameters
    ----------
    namespace : {'stock','market','sector'}
    op        : {'flow','breakdown','foreign_room'}  (tùy namespace)
    params    : dict đã chuẩn hoá: {
                   'ids': list[str],
                   'group': InvestorGroup,
                   'start': 'YYYY-MM-DD',
                   'end':   'YYYY-MM-DD',
                   'interval': Interval,
                   ... (tham số mở rộng khác)
                }

    Returns
    -------
    pandas.DataFrame
        BẮT BUỘC trả DataFrame (client sẽ không tự convert).
    """
    session: "HttpSession"

    def fetch_df(self, namespace: str, op: str, params: dict) -> pd.DataFrame: ...

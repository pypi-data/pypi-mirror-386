from __future__ import annotations

"""
fin68.clients.eod.investor.SectorInvestor (stub)
===============================================

"""

from typing import TYPE_CHECKING
from .investor import _InvestorBase, InvestorGroup
from ..helper import DateStr, InterValInvestor
from ..icb_types import SectorArg

if TYPE_CHECKING:
    import pandas as pd


class SectorInvestor(_InvestorBase):
    """
    Namespace dữ liệu **nhà đầu tư** cho cấp độ **ngành (sector-level)**.

    Cung cấp các endpoint theo dõi hoạt động mua/bán ròng của từng nhóm nhà đầu tư
    trong các ngành/nhóm ngành theo chuẩn ICB.

    Notes
    -----
    - Chấp nhận tên ngành tiếng Việt (chuẩn hóa trước khi truy vấn).
    """

    _endpoint_root: str

    def flow(
        self,
        symbol: SectorArg,
        *,
        group: InvestorGroup = "foreign",
        start: DateStr = None,
        end: DateStr = None,
        interval: InterValInvestor = "1D",
    ) -> "pd.DataFrame": ...
    """
    Lấy dữ liệu **dòng tiền ròng (net buy/sell flow)** theo nhóm nhà đầu tư
    cho từng **ngành hoặc nhóm ngành** (ICB sector).

    Parameters
    ----------
    symbol : str or Sequence[str]
        Tên ngành hoặc mã ICB (có thể truyền nhiều).  
        Ví dụ: "Ngân hàng", "Dầu khí", hoặc ["Ngân hàng", "Công nghệ"].
    group : {"foreign", "proprietary"}, default "foreign"
        Nhóm nhà đầu tư cần lấy dữ liệu.
    start : str, optional
        Ngày bắt đầu, định dạng "YYYY-MM-DD". Nếu `None`, dùng mặc định hệ thống.
    end : str, optional
        Ngày kết thúc, định dạng "YYYY-MM-DD". Nếu `None`, mặc định là hôm nay.
    interval : {"1D", "1W", "1M"}, default "1D"
        Tần suất dữ liệu mong muốn:
        - "1D" — Theo ngày
        - "1W" — Theo tuần
        - "1M" — Theo tháng

    Returns
    -------
    pandas.DataFrame
        Bảng dữ liệu gồm các cột:
        - `symbol` : mã ngành (ICB code)
        - `Date` : ngày giao dịch
        - `net_value` : giá trị mua ròng (VNĐ)
        - `net_volume` : khối lượng mua ròng
        - Các cột khác (nếu có) như `buy_value`, `sell_value`, `buy_volume`, `sell_volume`.

    Raises
    ------
    ValueError
        Nếu `symbol` không ánh xạ được sang ICB code, hoặc `group`/`interval` không hợp lệ.
    RuntimeError
        Nếu truy vấn private_core thất bại.

    Notes
    -----
    - SDK sẽ chuẩn hóa tên ngành sang mã ICB.

    Examples
    --------
    from fin68 import client

    cli = client(api_key="sk_live_...")
    investor = cli.eod.sector.investor

    # Dòng tiền ròng của ngành Ngân hàng trong 6 tháng đầu 2024
    df = investor.flow("Ngân hàng", start="2024-01-01", end="2024-06-30")

    # Dòng tiền ròng theo tuần của Dầu khí và Công nghệ (group nước ngoài)
    df = investor.flow(["Dầu khí", "Công nghệ"], group="foreign", interval="1W")
    """

from __future__ import annotations

"""
fin68.clients.eod.investor.MarketInvestor (stub)
===============================================

Type stub cho lớp `MarketInvestor` — phục vụ autocomplete/typing trong IDE
và static type checker (mypy/pyright). Không thực thi logic.

Ghi chú
-------
- Giữ chuẩn NumPy style cho docstring.
- Phần ví dụ (Examples) không dùng dấu `>>>`.
- Thân hàm được thay bằng `...` (ellipsis) theo PEP 484.
"""

from typing import TYPE_CHECKING
from .investor import _InvestorBase, InvestorGroup
from ..helper import DateStr, InterValInvestor, MarketArg

if TYPE_CHECKING:
    import pandas as pd


class MarketInvestor(_InvestorBase):
    _endpoint_root: str

    def flow(
        self,
        symbol: MarketArg,
        *,
        group: InvestorGroup = "all",
        start: DateStr = None,
        end: DateStr = None,
        interval: InterValInvestor = "1D",
    ) -> "pd.DataFrame": ...
    """
    Lấy dữ liệu **dòng tiền ròng (net buy/sell flow)** theo nhóm nhà đầu tư
    cho các chỉ số thị trường (VNINDEX, VN30, HNX, UPCOM...).

    Parameters
    ----------
    symbol : str or Sequence[str]
        Mã chỉ số thị trường hoặc danh sách mã chỉ số
        (ví dụ: "VNINDEX", "VN30", "HNXINDEX", "UPINDEX").
    group : {"foreign", "proprietary", "local_institutional", "local_individual",
             "foreign_institutional", "foreign_individual"}, default "foreign"
        Nhóm nhà đầu tư cần lấy dữ liệu.
    start : str, optional
        Ngày bắt đầu, định dạng "YYYY-MM-DD".  
        Nếu không truyền, hệ thống tự động lấy theo khoảng mặc định.
    end : str, optional
        Ngày kết thúc, định dạng "YYYY-MM-DD".  
        Nếu không truyền, mặc định là ngày hiện tại.
    interval : {"1D", "1W", "1M"}, default "1D"
        Tần suất dữ liệu mong muốn:
        - "1D" — Theo ngày  
        - "1W" — Theo tuần  
        - "1M" — Theo tháng

    Returns
    -------
    pandas.DataFrame
        Bảng dữ liệu gồm các cột:
        - `symbol` : mã chỉ số thị trường  
        - `date` : ngày giao dịch  
        - `net_value` : giá trị mua ròng (VNĐ)  
        - `net_volume` : khối lượng mua ròng  
        - Các cột khác như `buy_value`, `sell_value`, `buy_volume`, `sell_volume`.

    Raises
    ------
    ValueError
        Nếu `group` hoặc `interval` không hợp lệ.
    RuntimeError
        Nếu truy vấn từ private_core thất bại.

    Notes
    -----
    - Wrapper của `private_core.investor.fetch_df(namespace="market", op="flow")`.
    - Dữ liệu được chuẩn hóa về `pandas.DataFrame`.
    - Thường dùng trong phân tích dòng vốn toàn thị trường, xác định xu hướng
      mua/bán ròng của nhà đầu tư nước ngoài hoặc tự doanh.

    Examples
    --------
    from fin68 import client

    cli = client(api_key="sk_live_...")
    investor = cli.eod.market.investor

    # Dòng tiền ròng của nhà đầu tư nước ngoài trên VNINDEX trong quý 1/2024
    df = investor.flow("VNINDEX", group="foreign", start="2024-01-01", end="2024-03-31")

    # Dòng tiền ròng tổng hợp theo tuần trên nhiều chỉ số
    df = investor.flow(["VNINDEX", "VN30", "HNXINDEX"], interval="1W")
    """

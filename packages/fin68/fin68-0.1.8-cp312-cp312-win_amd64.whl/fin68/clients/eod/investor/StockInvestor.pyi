from __future__ import annotations
from typing import TYPE_CHECKING
from .investor import _InvestorBase, InvestorGroup
from ..helper import DateStr, InterValInvestor, SymbolArg

if TYPE_CHECKING:
    import pandas as pd


class StockInvestor(_InvestorBase):
    """
    Namespace dữ liệu **nhà đầu tư** cho cấp độ cổ phiếu.

    Cung cấp các endpoint theo dõi hành vi giao dịch (mua/bán ròng, breakdown theo nhóm,
    room nước ngoài) cho từng mã cổ phiếu hoặc danh sách mã.

    Notes
    -----
    - `_endpoint_root = "stock"` để định tuyến private_core về không gian tên cổ phiếu.
    - Tất cả phương thức trả về `pandas.DataFrame` (trừ khi có ghi chú khác).
    """

    _endpoint_root: str

    def flow(
        self,
        symbol: SymbolArg,
        *,
        group: InvestorGroup = "foreign",
        start: DateStr = None,
        end: DateStr = None,
        interval: InterValInvestor = "1D",
    ) -> "pd.DataFrame": ...
    """
    Lấy dữ liệu **dòng tiền ròng (net buy/sell flow)** theo nhóm nhà đầu tư
    cho từng mã cổ phiếu hoặc danh sách mã.

    Parameters
    ----------
    symbol : str or Sequence[str]
        Mã cổ phiếu hoặc danh sách mã (ví dụ: "HPG" hoặc ["HPG", "VCB", "FPT"]).
    group : {"foreign", "proprietary", "local_institutional", "local_individual",
             "foreign_institutional", "foreign_individual"}, default "foreign"
        Nhóm nhà đầu tư cần lấy dữ liệu.
    start : str, optional
        Ngày bắt đầu, định dạng "YYYY-MM-DD". Nếu `None`, dùng mặc định hệ thống.
    end : str, optional
        Ngày kết thúc, định dạng "YYYY-MM-DD". Nếu `None`, mặc định là hôm nay.
    interval : {"1D", "1W", "1M"}, default "1D"
        Tần suất dữ liệu mong muốn.

    Returns
    -------
    pandas.DataFrame
        Gồm các cột cơ bản: `symbol`, `Date`, `net_value`, `net_volume`
        và có thể thêm các cột như `buy_value`, `sell_value`, `buy_volume`, `sell_volume`.

    Raises
    ------
    ValueError
        Nếu `group` hoặc `interval` không hợp lệ.
    RuntimeError
        Nếu truy vấn private_core thất bại.

    Notes
    -----
    - Dữ liệu được chuẩn hóa về `pandas.DataFrame`.

    Examples
    --------
    from fin68 import client

    cli = client(api_key="sk_live_...")
    investor = cli.eod.stock.investor

    # Dòng tiền ròng của HPG trong 6 tháng đầu 2024
    df = investor.flow("HPG", start="2024-01-01", end="2024-06-30", group="foreign", interval="1D")

    # Dòng tiền ròng của nhóm nước ngoài theo tuần cho nhiều mã
    df = investor.flow(["HPG", "VCB", "FPT"], group="foreign", interval="1W")
    """

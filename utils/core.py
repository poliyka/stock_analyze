# Calculate net profit and loss from selling records
from dataclasses import dataclass, field
from odoo.exceptions import ValidationError
import math
from typing import Callable


@dataclass
class AmountCache:
    buy_amount: int = field(default=0)
    sell_amount: int = field(default=0)
    buy_lots_minus: int = field(default=0)
    sell_lots_minus: int = field(default=0)
    current_lots: int = field(default=0)
    buy_index: int = field(default=0)
    sell_index: int = field(default=0)


@dataclass
class CalculateNetProfitAndLoss:
    """
    object 結構:
    current_price: int
    shares: int
    lots: int
    amount: int
    transaction_fee: int
    transaction_tax: int
    """

    # 必要欄位(買入紀錄、賣出紀錄)
    buy_records: list[object]
    sell_records: list[object]
    current_record: object

    # 遞迴函數，計算淨利損
    def recursive(
        self,
        buys: object,
        sells: object,
        buy: object | None,
        sell: object | None,
        amount_cache: AmountCache,
    ):
        """
        1. 如果沒有任何 sell 紀錄，計算 buy 紀錄的股數 (buy_lots = shares * 1000 + lots)，並與 current_record 的股數 current_lots 比較。
            net_profit_loss = 0
            IF buy_lots >= current_lots:
                計算淨利損
                net_profit_loss = (
                    current_amount
                    - amount_cache.buy_amount
                    - (buy.current_price * amount_cache.current_lots)
                    - current_transaction_fee
                    - current_transaction_tax
                )
                return net_profit_loss
            ELSE:
                1. current_lots 減去 buy_lots
                2. buy_amount 加上 buy.current_price * buy_lots
                3. buy_index 加 1
                4. return recursive(buys, sells, buys[buy_index], sell, amount_cache)

        2. 如果有 sell 紀錄，計算 buy 紀錄的股數 (buy_lots = shares * 1000 + lots)，並與 current_record 的股數 current_lots 比較。
        """
        if not buy:
            raise ValidationError("沒有可計算的 buy 紀錄，請確認是否有錯誤")

        # 沒有 sell 紀錄
        if not sell:
            return self.cal_without_sell(
                buys,
                sells,
                buy,
                sell,
                amount_cache,
            )

        # 有 sell 紀錄
        else:
            return self.cal_with_sell(
                buys,
                sells,
                buy,
                sell,
                amount_cache,
            )

    def cal_without_sell(
        self,
        buys: object,
        sells: object,
        buy: object | None,
        sell: object | None,
        amount_cache: AmountCache,
    ) -> int | Callable:
        net_profit_loss = 0
        buy_lots = (buy.shares * 1000 + buy.lots) - amount_cache.buy_lots_minus
        current_amount = self.current_record.amount
        current_transaction_fee = self.current_record.transaction_fee
        current_transaction_tax = self.current_record.transaction_tax

        if buy_lots >= amount_cache.current_lots:
            net_profit_loss = (
                current_amount
                - amount_cache.buy_amount
                - (buy.current_price * amount_cache.current_lots)
                - current_transaction_fee
                - current_transaction_tax
            )
            return net_profit_loss
        else:
            amount_cache.current_lots -= buy_lots
            amount_cache.buy_lots_minus = 0
            amount_cache.buy_amount += buy.current_price * buy_lots
            amount_cache.buy_index += 1
            return self.recursive(
                buys,
                sells,
                (
                    buys[amount_cache.buy_index]
                    if len(buys) > amount_cache.buy_index
                    else None
                ),
                sell,
                amount_cache,
            )

    def cal_with_sell(
        self,
        buys: object,
        sells: object,
        buy: object | None,
        sell: object | None,
        amount_cache: AmountCache,
    ) -> int | Callable:
        buy_lots = (buy.shares * 1000 + buy.lots) - amount_cache.buy_lots_minus
        sell_lots = (sell.shares * 1000 + sell.lots) - amount_cache.sell_lots_minus

        if buy_lots == sell_lots:
            amount_cache.buy_lots_minus = 0
            amount_cache.sell_lots_minus = 0
            amount_cache.buy_index += 1
            amount_cache.sell_index += 1
            return self.recursive(
                buys,
                sells,
                (
                    buys[amount_cache.buy_index]
                    if len(buys) > amount_cache.buy_index
                    else None
                ),
                (
                    sells[amount_cache.sell_index]
                    if len(sells) > amount_cache.sell_index
                    else None
                ),
                amount_cache,
            )

        elif buy_lots > sell_lots:
            amount_cache.buy_lots_minus += sell_lots
            amount_cache.sell_lots_minus = 0
            amount_cache.sell_index += 1
            return self.recursive(
                buys,
                sells,
                buy,
                (
                    sells[amount_cache.sell_index]
                    if len(sells) > amount_cache.sell_index
                    else None
                ),
                amount_cache,
            )
        else:
            amount_cache.buy_lots_minus = 0
            amount_cache.sell_lots_minus += buy_lots
            amount_cache.buy_index += 1
            return self.recursive(
                buys,
                sells,
                (
                    buys[amount_cache.buy_index]
                    if len(buys) > amount_cache.buy_index
                    else None
                ),
                sell,
                amount_cache,
            )

    def calculate(self) -> float:
        """
        計算淨損益，以下為假設範例:
        buy_records = [buy_obj, buy_obj, buy_obj]
        self_records = [sell_obj]
        在本筆紀錄之前有 3 筆 buy 紀錄，1 筆 sell 紀錄

        1. 如果沒有任何 sell 以及 buy 紀錄，回傳錯誤
            raise ValidationError("沒有可計算的 buy、sell 紀錄，請確認是否有錯誤")
        2. 如果有 sell 卻沒有 buy 紀錄，回傳錯誤。
            raise ValidationError("沒有可計算的 buy 紀錄，請確認是否有錯誤")
        """
        current_lots = self.current_record.shares * 1000 + self.current_record.lots

        if not self.buy_records and not self.sell_records:
            raise ValidationError("沒有可計算的 buy、sell 紀錄，請確認是否有錯誤")
        elif not self.buy_records:
            raise ValidationError("沒有可計算的 buy 紀錄，請確認是否有錯誤")

        net_profit_loss = self.recursive(
            self.buy_records,
            self.sell_records,
            self.buy_records[0] if self.buy_records else None,
            self.sell_records[0] if self.sell_records else None,
            AmountCache(current_lots=current_lots),
        )

        return net_profit_loss

import datetime
import json
import random

import twstock
from fp.fp import FreeProxy
from odoo import http
from twstock import BestFourPoint, Stock
from twstock.proxy import RoundRobinProxiesProvider, SingleProxyProvider, get_proxies


class StockControllers(http.Controller):
    @http.route(
        "/index/",
        auth="public",
        website=True,
        # csrf=False,
        # type="http", # http or json
        # type="json",  # http or json
        # methods=["POST"],
    )
    def index(self, **kw):
        proxy = FreeProxy(country_id=["TW"], rand=True).get()
        spr = SingleProxyProvider({proxy.split(":")[0]: proxy})
        twstock.proxy.configure_proxy_provider(spr)

        context = self.create_stock_data("2330", (2024, 1))

        return http.request.render("stock_analyze.index", context)

    def create_stock_data(self, code, fetch_from):
        stock_detail = twstock.codes[code]
        stock = Stock(code)
        bfp = BestFourPoint(stock)
        buy_point = bfp.best_four_point_to_buy()  # 判斷是否為四大買點
        sell_point = bfp.best_four_point_to_sell()  # 判斷是否為四大賣點
        analyze_point = bfp.best_four_point()  # 綜合判斷
        stock_datas = stock.fetch_from(*fetch_from)

        # (0, _ , {'field': value}) creates a new record and links it to this one.
        storages = []
        for stock in stock_datas:
            storages.append(
                (
                    0,
                    0,
                    {
                        "date": stock.date,
                        "capacity": stock.capacity,
                        "turnover": stock.turnover,
                        "open": stock.open,
                        "high": stock.high,
                        "low": stock.low,
                        "close": stock.close,
                        "change": stock.change,
                        "transaction": stock.transaction,
                    },
                )
            )

        stock_pt = http.request.env["stock"]
        stock_pt.create(
            {
                "type": stock_detail.type,
                "code": stock_detail.code,
                "name": stock_detail.name,
                "ISIN": stock_detail.ISIN,
                "start": stock_detail.start.replace("/", "-"),
                "market": stock_detail.market,
                "group": stock_detail.group,
                "CFI": stock_detail.CFI,
                "storage_ids": storages,
            }
        )

        context = {
            "stock_datas": stock_datas,
            "stock_detail": stock_detail,
            "buy_point": buy_point,
            "sell_point": sell_point,
            "analyze_point": analyze_point,
        }
        return context

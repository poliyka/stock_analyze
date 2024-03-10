from datetime import timedelta
import datetime
import json


from odoo import api, fields, models, _
from odoo.tools import date_utils
from odoo.exceptions import UserError, ValidationError


class Stock(models.Model):
    _name = "stock"
    _description = "股票基本資訊"

    type = fields.Char(string="股票類型")
    code = fields.Char(string="代號", unique=True)
    name = fields.Char(string="股名")
    ISIN = fields.Char(string="ISIN")
    start = fields.Date(string="上市日期")
    market = fields.Char(string="市場")
    group = fields.Char(string="產業類型")
    CFI = fields.Char(string="CFI")

    storage_ids = fields.One2many(
        "stock.storage",
        "stock_id",
        string="歷史資訊",
    )

class StockStorage(models.Model):
    _name = "stock.storage"
    _description = "股票歷史資訊"
    _rec_name = "date"

    date = fields.Date(string="日期", required=True)
    capacity = fields.Integer(string="容量", default=0)
    turnover = fields.Integer(string="轉換", default=0)
    open = fields.Float(string="開市", digits=(4,2))
    high = fields.Float(string="高點", digits=(4,2))
    low = fields.Float(string="低點", digits=(4,2))
    close = fields.Float(string="關市", digits=(4,2))
    change = fields.Float(string="成交率", digits=(4,2))
    transaction = fields.Integer(string="交易次數", default=0)

    stock_id = fields.Many2one(
        "stock",
        string="股票",
        required=True,
        ondelete="cascade",
    )

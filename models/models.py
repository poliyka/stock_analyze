from odoo import api, fields, models


class Stock(models.Model):
    _name = "stock"
    _description = "股票基本資訊"
    _rec_name = "name"

    type = fields.Char(string="股票類型")
    code = fields.Char(string="代號", unique=True)
    name = fields.Char(string="股名")
    ISIN = fields.Char(string="ISIN")
    start = fields.Date(string="上市日期")
    market = fields.Char(string="市場")
    group = fields.Char(string="產業類型")
    CFI = fields.Char(string="CFI")


class StockUser(models.Model):
    _name = "stock.user"
    _description = "投資人"
    _rec_name = "name"

    invest_ids = fields.One2many(
        "stock.invest",
        "user_id",
        string="投資清單",
    )

    name = fields.Selection(
        string="投資人名稱",
        selection=[
            ("少逸", "少逸"),
            ("竹恩", "竹恩"),
            ("黑貓", "黑貓"),
        ],
        default="黑貓",
    )


class StockBank(models.Model):
    _name = "stock.bank"
    _description = "帳戶"
    _rec_name = "name"

    invest_ids = fields.One2many(
        "stock.invest",
        "bank_id",
        string="投資清單",
    )

    name = fields.Char(string="帳戶名稱", nullable=False)
    code = fields.Char(string="銀行代號")
    account = fields.Char(string="銀行帳號")
    deposit = fields.Integer(
        string="現有資金",
        default=0,
        nullable=False,
        readonly=True,
        compute="_compute_deposit",
    )
    assets = fields.Integer(
        string="投資資產",
        default=0,
        nullable=False,
        readonly=True,
    )

    @api.depends("invest_ids.payment")
    def _compute_deposit(self):
        for record in self:
            record.deposit = sum(record.invest_ids.mapped("payment"))


class StockInvest(models.Model):
    _name = "stock.invest"
    _description = "入帳紀錄"
    _rec_name = "date"

    user_id = fields.Many2one(
        "stock.user",
        string="投資人",
        nullable=False,
    )

    bank_id = fields.Many2one(
        "stock.bank",
        string="帳戶",
        nullable=False,
    )

    date = fields.Date(string="日期", default=fields.Date.today())
    payment = fields.Integer(string="投資金額", nullable=False)

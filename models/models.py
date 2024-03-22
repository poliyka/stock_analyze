import math
from odoo import api, fields, models


class Stock(models.Model):
    _name = "stock"
    _description = "股票基本資訊"
    _rec_name = "_c_name"

    _sql_constraints = [("unique_code", "unique(code)", "代號已存在")]

    type = fields.Char(string="股票類型")
    code = fields.Char(string="代號")
    name = fields.Char(string="股名")
    _c_name = fields.Char(string="股票名稱", compute="_compute_name", store=True)
    ISIN = fields.Char(string="ISIN")
    start = fields.Date(string="上市日期")
    market = fields.Char(string="市場")
    group = fields.Char(string="產業類型")
    CFI = fields.Char(string="CFI")

    @api.depends("name", "code")
    def _compute_name(self):
        for record in self:
            record._c_name = f"({record.code}) {record.name}"

    @api.model
    def _name_search(
        self,
        name="",
        domain=None,
        operator="ilike",
        limit=15,
        order=None,
    ):
        domain = list(domain or [])
        if not name:
            return super(Stock, self)._name_search(
                name,
                domain,
                operator,
                limit,
                order="market",
            )
        else:
            domain += [
                "|",
                ("code", operator, name),
                ("name", operator, name),
            ]
            return self._search(domain, limit=limit, order="market")


class StockUserInherit(models.Model):
    _inherit = ["res.users"]

    invest_ids = fields.One2many(
        "stock.invest",
        "user_id",
        string="投資清單",
    )


class StockUser(models.Model):
    """
    Deprecated model
    """

    _name = "stock.user"
    _description = "投資人"


class StockBank(models.Model):
    _name = "stock.bank"
    _description = "帳戶"
    _rec_name = "name"

    invest_ids = fields.One2many(
        "stock.invest",
        "bank_id",
        string="投資清單",
    )

    invest_history_ids = fields.One2many(
        "stock.invest.history",
        "bank_id",
        string="投資紀錄",
    )

    name = fields.Char(string="帳戶名稱")
    code = fields.Char(string="銀行代號")
    account = fields.Char(string="銀行帳號")
    deposit = fields.Integer(
        string="現有資金",
        default=0,
        readonly=True,
        compute="_compute_deposit",
    )
    assets = fields.Integer(
        string="投資資產",
        default=0,
        readonly=True,
        compute="_compute_assets",
    )

    @api.depends("invest_ids.payment")
    def _compute_deposit(self):
        for record in self:
            record.deposit = sum(record.invest_ids.mapped("payment"))

    @api.depends("invest_history_ids.net_profit_loss")
    def _compute_assets(self):
        for record in self:
            record.assets = sum(record.invest_history_ids.mapped("net_profit_loss"))


class StockInvest(models.Model):
    _name = "stock.invest"
    _description = "入帳紀錄"
    _rec_name = "date"

    user_id = fields.Many2one(
        "res.users",
        string="投資人",
        required=True,
        ondelete="restrict",
    )

    bank_id = fields.Many2one(
        "stock.bank",
        string="帳戶",
        required=True,
        ondelete="restrict",
    )

    date = fields.Date(string="日期", default=fields.Date.today())
    payment = fields.Integer(string="投資金額", required=True)


class StockInvestHistory(models.Model):
    _name = "stock.invest.history"
    _description = "投資紀錄"
    _rec_name = "date"

    bank_id = fields.Many2one(
        "stock.bank",
        string="帳戶",
        ondelete="set null",
    )
    bank_name = fields.Char(related="bank_id.name", string="帳戶名稱", store=True)

    stock_id = fields.Many2one(
        "stock",
        string="股票",
        ondelete="set null",
    )

    stock_name = fields.Char(related="stock_id.name", string="股票名稱", store=True)
    stock_code = fields.Char(related="stock_id.code", string="股票代號", store=True)
    stock_type = fields.Char(related="stock_id.type", string="股票類型", store=True)
    stock_market = fields.Char(related="stock_id.market", string="市場", store=True)

    date = fields.Date(string="日期", default=fields.Date.today(), required=True)
    current_price = fields.Float(string="目前價格", required=True)
    shares = fields.Integer(string="張數", default=0, required=True)
    lots = fields.Integer(string="股數", default=0, required=True)
    amount = fields.Integer(
        string="金額",
        default=0,
        compute="_compute_amount",
        store=True,
    )
    net_payment_receipt = fields.Integer(
        string="淨收付金額(已扣手續、交易稅)",
        default=0,
        compute="_compute_net_payment_receipt",
        store=True,
    )
    transaction_fee = fields.Integer(
        string="交易手續費",
        default=0,
        compute="_compute_transaction_fee",
        store=True,
    )
    transaction_tax = fields.Integer(
        string="交易稅",
        default=0,
        required=True,
        compute="_compute_transaction_tax",
        store=True,
    )
    payment_type = fields.Selection(
        string="交易類型",
        selection=[
            ("buy", "買入"),
            ("sell", "賣出"),
            ("subscription", "申購"),
            ("redemption", "申退"),
            ("rights", "認購"),
        ],
        default="buy",
        required=True,
    )
    net_profit_loss = fields.Integer(string="淨損益", default=0)
    note = fields.Text(string="備註")

    @api.depends("current_price", "shares", "lots", "payment_type")
    def _compute_amount(self):
        """
        計算金額 = 目前價格 * (張數 * 1000 + 股數)
        """
        for record in self:
            if record.payment_type in ["buy", "subscription", "rights"]:
                record.amount = -math.ceil(
                    record.current_price * (record.shares * 1000 + record.lots)
                )
            elif record.payment_type in ["sell", "redemption"]:
                record.amount = math.ceil(
                    record.current_price * (record.shares * 1000 + record.lots)
                )
            else:
                record.amount = 0

    @api.depends("payment_type", "amount", "transaction_fee", "transaction_tax")
    def _compute_net_payment_receipt(self):
        """
        計算淨收付金額 = 金額 - 交易手續費 - 交易稅
        """
        for record in self:
            if record.payment_type in ["buy", "subscription", "rights"]:
                record.net_payment_receipt = -record.transaction_fee
            elif record.payment_type in ["sell"]:
                record.net_payment_receipt = (
                    record.amount - record.transaction_fee - record.transaction_tax
                )
            else:
                record.net_payment_receipt = 0

    @api.depends("payment_type", "amount")
    def _compute_transaction_fee(self):
        default_fee = 20
        for record in self:
            if record.payment_type in ["buy", "sell"]:
                fee = record.amount * 0.001425
                if fee >= default_fee:
                    record.transaction_fee = fee
                else:
                    record.transaction_fee = default_fee
            elif record.payment_type == "subscription":
                record.transaction_fee = default_fee
            elif record.payment_type == "redemption":
                record.transaction_fee = -default_fee
            else:
                record.transaction_fee = 0

    @api.depends("payment_type", "amount")
    def _compute_transaction_tax(self):
        for record in self:
            if record.payment_type in ["sell"]:
                record.transaction_tax = record.amount * 0.003
            else:
                record.transaction_tax = 0

    def update_compute(self):
        for record in self:
            record._compute_amount()
            record._compute_net_payment_receipt()
            record._compute_transaction_fee()
            record._compute_transaction_tax()

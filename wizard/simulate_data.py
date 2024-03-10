from odoo import models
from odoo.exceptions import ValidationError

import twstock
from fp.fp import FreeProxy
from odoo import http
from twstock.proxy import  SingleProxyProvider


class InjectStocksData(models.TransientModel):
    _name = "inject.stocks.data"
    _description = "建立所有 Stock 資料"

    def simulate(self):
        proxy = FreeProxy(country_id=["TW"], rand=True).get()
        spr = SingleProxyProvider({proxy.split(":")[0]: proxy})
        twstock.proxy.configure_proxy_provider(spr)

        for record in self:
            record.with_context(context_data=True)._force_clean_simulate()
            record.with_context(context_data=True)._simulate_inject_stocks()
        raise ValidationError("done")

    def _force_clean_simulate(self):
        self.env["stock"].search([]).unlink()
        self.env.cr.commit()

    def _simulate_inject_stocks(self):
        pt = http.request.env["stock"]
        stocks= twstock.codes
        for _, stock in stocks.items():
            pt.create(
                {
                    "type": stock.type,
                    "code": stock.code,
                    "name": stock.name,
                    "ISIN": stock.ISIN,
                    "start": stock.start.replace("/", "-"),
                    "market": stock.market,
                    "group": stock.group,
                    "CFI": stock.CFI,
                }
            )

        self.env.cr.commit()


class SMTPInjection(models.TransientModel):
    _name = "inject.outgoing.server"
    _description = "建立 Email Outgoing Server"

    def simulate(self):
        for record in self:
            record.with_context(context_data=True)._force_clean_simulate()
            record.with_context(context_data=True)._set_outgoing()
        raise ValidationError("done")

    def _force_clean_simulate(self):
        self.env["ir.mail_server"].search([]).unlink()
        self.env.cr.commit()

    def _set_outgoing(self):
        pt = self.env["ir.mail_server"]

        outgoings = [
            {
                "name": "Stock-Server",
                "smtp_user": "dwqd853@gmail.com",
                "smtp_pass": "siffxzyxustfspze",
            },
        ]

        temp_data = {
            "sequence": 5,
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 465,
            "smtp_encryption": "ssl",
        }

        for i, outgoing in enumerate(outgoings):
            data = temp_data.copy()
            server = pt.create({**data, **outgoing})
            try:
                server.test_smtp_connection()
            except:
                raise ValidationError(f"{outgoing['name']}: 測試授權失敗")

        self.env.cr.commit()

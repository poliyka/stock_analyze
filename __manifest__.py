{
    "name": "Stock Analyze",
    "summary": """
        Stock Analyze
    """,
    "description": """
        Stock Analyze
    """,
    "author": "Poliyka",
    "website": "http://example.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Extra Tools",
    "license": "AGPL-3",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": [],
    # always loaded
    "data": [
        "security/security.xml",
        "security/ir_rule.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/view_stock.xml",
        "views/view_bank.xml",
        "views/view_user.xml",
        "views/view_invest.xml",
        "templates/index.xml",
        "wizard/ir.model.access.csv",
        "wizard/simulate_data.xml",
    ],
}

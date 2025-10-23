# Copyright 2025 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "CRM Date Deadline Required",
    "summary": "Field date deadline required in the opportunity",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Sales/CRM",
    "website": "https://github.com/OCA/crm",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["EmilioPascual", "rafaelbn"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "crm",
    ],
    "data": [
        "views/crm_lead_view.xml",
    ],
}

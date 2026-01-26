{
    "name": "Univ Trans Customisation",
    "version": "1.0",
    "category": "CRM",
    "summary": "Adds Opportunity File ID with sequence",
    "description": "Adds a unique, persistent Opportunity File ID generated using Odoo sequence.",
    "author": "Univ Trans",
    "depends": ["crm", "sale", "account"],
    "data": [
        "data/sequence.xml",
        "data/documents_tag.xml",
        "views/crm_lead_view.xml",
        "views/sale_order_view.xml",
        "views/account_move_view.xml",
        "report/sale_order.xml",
    ],
    "installable": True,
    "application": False,
}

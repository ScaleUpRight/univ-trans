{
    "name": "Univ Trans Customisation",
    "version": "1.0",
    "category": "CRM",
    "summary": "Adds Opportunity File ID with sequence",
    "description": "Adds a unique, persistent Opportunity File ID generated using Odoo sequence.",
    "author": "Univ Trans",
    "depends": ["crm"],
    "data": [
        "data/sequence.xml",
        "views/crm_lead_view.xml",
    ],
    "installable": True,
    "application": False,
}

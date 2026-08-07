{
    'name': "Univ Trans: Portal Customisations",
    'version': '19.0.1.0.0',
    'summary': "Customisations to the customer portal",
    'description': """
Container module for Univ Trans customisations to the customer portal.

Currently provides
------------------
**All Confirmed Orders Viewer** — grants a portal user read-only visibility of
every confirmed sales order (state = 'sale') and the documents filed under each
order's Documents folder, without making them an internal user.

Quotations (draft/sent) stay invisible, and the access is read-only: the record
rules added here grant `read` only, so writes still fall through to Odoo's
restrictive stock portal rule.
    """,
    'category': 'Sales/Sales',
    'depends': ['sale', 'documents', 'univ_trans_customisation'],
    'data': [
        'security/security.xml',
        'views/portal_templates.xml',
    ],
    'license': 'LGPL-3',
}

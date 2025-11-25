# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Candidroot Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

{
    'name': "AI Batch Refresh Value",
    'version': '19.0.0.1',
    'summary': """ AI Batch Refresh Value in List and Form view """,
    'category': 'AI',
    'depends': ['ai_app', 'crm'],
    'data': [
        'views/batch_ai_refresh.xml',
        'data/ir_action.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

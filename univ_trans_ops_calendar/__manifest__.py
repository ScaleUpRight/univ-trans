{
    'name': 'Universe Transit - Operations Calendar',
    'version': '1.1',
    'category': 'Project',
    'summary': 'Shared operations calendar — generates per-activity jobs from confirmed sale orders',
    'author': 'Univ Trans',
    'depends': ['project', 'sale', 'mail', 'univ_trans_customisation'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/project_data.xml',
        'data/mail_template.xml',
        'views/project_task_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
}

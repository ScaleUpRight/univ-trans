# -*- coding: utf-8 -*-
###############################################################################
#
#    BeyonData Solutions Private Limited
#
#    Copyright (C) 2024-TODAY BeyonData Solutions Private Limited
#    Author: Anirudh kachela
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#
###############################################################################
{
    'name': "Camera Image Capture",
    'summary': "Camera Image Capture",

    'description': """
Long description of module's purpose
    """,
    'author': 'BeyonData Solutions Private Limited',
    'website': "https://www.beyondatagroup.com/",
   'live_test_url': 'https://www.beyondatagroup.com/contactus',
    "license": "OPL-1",
    'version': '1.0',
    # 'price': '27.78',
    'price': '13.89',
    'currency': 'EUR',
    'depends': ['base','product','stock','hr'],
    'assets': {
        'web.assets_backend': [
            'bd_camera_image_capture/static/src/xml/image_upload.xml',
            'bd_camera_image_capture/static/src/xml/contact_image.xml',
            'bd_camera_image_capture/static/src/js/image_upload.js',
            'bd_camera_image_capture/static/src/xml/camera_dialog.xml',
            'bd_camera_image_capture/static/src/js/camera_dialog.js'
        ]
    },
    # "images": ["static/description/banner.gif"],
    "images": ["static/description/banner_50%.gif"],

    'installable': True,
    'auto_install': True,
}


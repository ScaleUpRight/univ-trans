from odoo import api, fields, models


class Contents(models.Model):
    _name = "contents"

    content_id = fields.Integer(required=True, string="Content ID")
    name = fields.Char(required=True)
    cube = fields.Float(required=True)
    category_id = fields.Many2one("product.category", string="Category", required=True)

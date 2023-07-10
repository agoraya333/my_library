from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = 'name'

    published_book_ids = fields.One2many(
        'library.book', 'publisher_id',
        string='Published Books')
    # authored_book_ids = fields.Many2many('library.book', string='Authored Books', coloumn1='abc_ids', coloumn2='xyz_ids')
    count_books = fields.Integer('Name of Authored Books', compute='_compute_count_books')

# Class Inheritance of a method using computed fields
    @api.depends('authored_book_ids')
    def _compute_count_books(self):
        for r in self:
            r.count_books = len(r.authored_book_ids)

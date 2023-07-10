from odoo import models, fields


class LibraryBookCopy(models.Model):
    _name = "library.book.prototype"
    _inherit = "library.book"
    _description = "Library Book's Copy"


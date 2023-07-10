from odoo import models, fields, api


class LibraryRentWizard(models.TransientModel):
    _name = 'library.rent.wizard'

    borrower_id = fields.Many2one('res.partner', string='Borrower')
    book_ids = fields.Many2many('library.book', string='Books')

    def add_book_rents(self):
        self.ensure_one()
        rentModel = self.env['library.book.rent']
        for book in self.book_ids:
            rentModel.create({
                'borrower_id': self.borrower_id.id,
                'book_id': book.id
            })

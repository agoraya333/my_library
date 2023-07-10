from odoo import models, fields, api


class LibraryMember(models.Model):
    _name = 'library.member'

    partner_id = fields.Many2one('res.partner', ondelete='cascade', delegate=True)
    date_start = fields.Date('Member Since')
    date_end = fields.Date('Termination Date')
    member_number = fields.Char()
    date_of_birth = fields.Date('Date of Birth')

    def create_record(self):
        new_record = self.create({
            'partner_id': '45'
        })

# this copies and return the current recordset
    def copy_record(self):
        new_record = self.copy()
        return new_record

# this updates the end date of the member to the current date
    def cancel_membership(self):
        self.ensure_one()
        update_status = self.write({
            'date_end': fields.Date.today()
        })
        return update_status

    def first_member(self):
        first = self.browse([1])
        print(first)

    def delete_members(self):
        self.unlink()

    def check_existance(self):
        if self.exists():
            print("hello")
        else:
            raise Exception("The record has been deleted")

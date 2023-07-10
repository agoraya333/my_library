from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import UserError
from odoo.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class BaseArchive(models.AbstractModel):
    _name = 'base.archive'
    _description = 'Abstract Archive'

    active = fields.Boolean(default=True)

    def do_archive(self):
        for record in self:
            record.active = not record.active


class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Library Book'
    _order = 'date_release desc, name'
    _rec_name = 'short_name'
    _inherit = ['base.archive', 'mail.activity.mixin', 'mail.thread']

    name = fields.Char('Title', required=True, tracking=True)
    isbn = fields.Char('ISBN')
    short_name = fields.Char('Short Title', required=True, translate=True, index=True, tracking=True)
    date_release = fields.Date('Release Date')
    author_ids = fields.Many2many('res.partner', string='Authors')
    notes = fields.Text('Internal Notes')
    state = fields.Selection(
        [('draft', 'Not Available'),
         ('available', 'Available'),
         ('borrowed', 'Borrowed'),
         ('lost', 'Lost')],
        'State', default="draft", tracking=True)
    description = fields.Html('Description', sanitize=True)
    cover = fields.Binary('Book Cover')
    out_of_print = fields.Boolean('Out of Print?')
    date_updated = fields.Datetime('Last Updated')
    pages = fields.Integer('Number of Pages',
                           groups='base.group_user',
                           states={'lost': [('readonly', True)]},
                           help='Total book page count', company_dependent=False)
    reader_rating = fields.Float(
        'Reader Average Rating',
        digits=(14, 4)
    )
    cost_price = fields.Float('Book Cost', digits='Book Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    currency_symbol = fields.Char('Currency Symbol', related='currency_id.symbol', readonly=True, related_sudo=True)
    retail_price = fields.Monetary(
        'Retail Price',
        currency_field='currency_id',
    )
    publisher_id = fields.Many2one('res.partner', string='Publisher')
    category_id = fields.Many2one('library.book.category')
    age_days = fields.Float(
        string='Days Since Release',
        compute='_compute_age',
        inverse='_inverse_age',
        search='_search_age',
        store=False,
        compute_sudo=True
    )
    ref_doc_id = fields.Reference(selection='_referencable_models', string='Reference Document')
    manager_remarks = fields.Text('Manager Remarks')
    old_edition = fields.Many2one('library.book', string='Old Edition')

    #######   Methods for the fields.   #######

# We use name_get() to rewrite the model attribute _rec_name
    def name_get(self):
        result = []
        for book in self:
            authors = book.author_ids.mapped('name')
            name = '%s (%s)' % (book.name, ', '.join(authors))
            result.append((book.id, name))
        return result

# These are the conventional SQL Constraints
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)', 'Book title must be unique.'),
        ('positive_page', 'CHECK(pages>0)', 'No of pages must be positive')
    ]

# These are the advanced Python Constraints
    @api.constrains('date_release')
    def _check_release_date(self):
        for record in self:
            if record.date_release and record.date_release > fields.Date.today():
                raise models.ValidationError('Release date must be in the past')

# Method for a computed field to calculate the days left in the book release
    @api.depends('date_release')
    # @api.depends_context('company_id')
    def _compute_age(self):
        today = fields.Date.today()
        # company_id = self.env.context.get('company_id')
        for book in self:
            if book.date_release:
                delta = today - book.date_release
                book.age_days = delta.days
            else:
                book.age_days = 0

# inverse method in a computed field
    def _inverse_age(self):
        today = fields.Date.today()
        for book in self.filtered('date_release'):
            d = today - timedelta(days=book.age_days)
            book.date_release = d

# Search method in computed field
    def _search_age(self, operator, value):
        today = fields.Date.today()
        value_days = timedelta(days=value)
        value_date = today - value_days
        operator_map = {
            '>': '<', '>=': '<=',
            '<': '>', '<=': '>=',
        }
        new_op = operator_map.get(operator, operator)
        return [('date_release', new_op, value_date)]

# Method used to write Dynamic Reference methods
    @api.model
    def _referencable_models(self):
        models = self.env['ir.model'].search([('field_id.name', '=', 'message_ids')])
        return [(x.model, x.name) for x in models]

    @api.model
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('draft', 'available'),
                   ('available', 'borrowed'),
                   ('borrowed', 'available'),
                   ('available', 'lost'),
                   ('borrowed', 'lost'),
                   ('lost', 'available'),
                   ('available', 'draft')]
        return (old_state, new_state) in allowed

    def change_state(self, new_state):
        for book in self:
            if book.is_allowed_transition(book.state, new_state):
                book.state = new_state
            else:
                msg = _('Moving from %s to %s is not allowed') % (book.state, new_state)
                raise UserError(msg)

    def make_available(self):
        self.change_state('available')

    def make_borrowed(self):
        self.change_state('borrowed')

    def make_lost(self):
        self.ensure_one()
        self.state = 'lost'
        if not self.env.context.get('avoid_deactivate'):
            self.active = False

    def make_draft(self):
        self.change_state('draft')

    def log_all_library_members(self):
        library_member_model = self.env['library.member']

        all_members = library_member_model.search([])
        print("All Members:", all_members)
        return True

    def change_release_date(self):
        # self.ensure_one()
        self.date_release = fields.Date.today()

    def find_book(self):
        domain = [
                '|',
                '&', ('name', 'ilike', 'Book Name'),
                ('category_id.name', 'ilike', 'Category Name'),
                 '&', ('name', 'ilike', 'Book Name 2'),
                ('category_id.name', 'ilike', 'Category Name 2')
                 ]
        books = self.search(domain)
        print(books)

    def get_archives(self):
        archive = self.search_count([('active', '=', False)])
        print(archive)
        return archive

    def filter_records(self):
        filter = self.filtered(lambda r: r.pages >= 100)
        print(filter)

    def full_name(self):
        sum = self.mapped(lambda a: a.name + a.short_name)
        print(sum)

    def sort_records(self):
        recordset = self.env["library.book"].search([])
        for rec in recordset.sorted(lambda a: a.name, reverse=True):
            print(rec.name)

    def combining_recordsets(self):
        recordset1 = self.env["library.book"].browse([11])
        recordset2 = self.env["library.book"].browse([12])
        result = recordset1.pages | recordset2.pages
        print(result)

    def filtered_model(self):
        all_books = self.search([])
        filtered_books = self.books_with_multiple_authors(all_books)
        print(filtered_books)
        return filtered_books

    @api.model
    def books_with_multiple_authors(self, all_books):
        def predicate(book):
            if len(book.author_ids) > 1:
                return True
            return False
        return all_books.filtered(predicate)

    def mapped_model(self):
        books = self.search([])
        mapped_names = self.get_author_names(books)
        print(mapped_names)

    @api.model
    def get_author_names(self, books):
        return books.mapped('author_ids.name')

    def sorted_model(self):
        books = self.search([])
        sorted_books = self.sort_books_by_date(books)
        x = sorted_books.mapped('pages')
        print(x)
    @api.model
    def sort_books_by_date(self, books):
        return books.sorted(key='pages')

    @api.model
    def create(self, values):
        if not self.user_has_groups('my_library.access_book_librarian'):
            if 'manager_remarks' in values:
                raise UserError(
                    'You are not allowed to modify '
                    'manager_remarks'
                )
        return super(LibraryBook, self).create(values)

    def write(self, values):
        if not self.user_has_groups('my_library.access_book_librarian'):
            if 'manager_remarks' in values:
                raise UserError(
                    'You are not allowed to modify '
                    'manager_remarks'
                )
        return super(LibraryBook, self).write(values)

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100):
        args = [] if args is None else args.copy()
        if not (name == '' and operator == 'ilike'):
            args += ['|', '|',
                     ('name', operator, name),
                     ('isbn', operator, name),
                     ('author_ids.name', operator, name)
                     ]
        return super(LibraryBook, self)._name_search(name=name, args=args, operator=operator, limit=limit)

    def grouped_data(self):
        data = self._get_average_cost()
        print(data)

    @api.model
    def _get_average_cost(self):
        grouped_result = self.read_group(
            [('cost_price', "!=", False)],  # Domain
            ['category_id', 'cost_price:avg'],  # Fields
            ['category_id', 'name'],  # group_by
            lazy=True
        )
        return grouped_result

    def book_rent(self):
        self.ensure_one()
        if self.state != 'available':
            raise UserError(_('Book is not available for renting'))
        rent_as_superuser = self.env['library.book.rent'].sudo()
        rent_as_superuser.create({
            'book_id': self.id,
            'borrower_id': self.env.user.partner_id.id,
        })

    def average_book_occupation(self):
        self.flush()
        sql_query = """
        SELECT
        lb.name,
        avg((EXTRACT(epoch from age(return_date, rent_date)) / 86400))::int
        FROM
        library_book_rent AS lbr
        JOIN
        library_book as lb ON lb.id = lbr.book_id
        WHERE lbr.state = 'returned'
        GROUP BY lb.name;
        """
        self.env.cr.execute(sql_query)
        result = self.env.cr.fetchall()
        _logger.info("Average book occupation: %s", result)

    def return_all_books(self):
        self.ensure_one()
        wizard = self.env['library.return.wizard']
        wizard.create({
            'borrower_id': self.env.user.partner_id.id
        }).books_returns()


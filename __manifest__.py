{
    'name': "My library",
    'summary': "Manage books easily",

    'website': "http://www.example.com",
    'category': 'Uncategorized',
    'version': '13.0.1',
    'depends': ['mail'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/library_book.xml',
        'views/library_book_category.xml',
        'views/library_members.xml',
        'views/library_book_inherit.xml',
        'views/library_book_rent.xml',
        'views/custom_settings.xml',
        'wizard/library_rent_wizard.xml',
        'wizard/library_return_wizard.xml',
    ],
    'demo': [],
    'post_init_hook': 'add_book_hook',
}

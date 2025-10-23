import odooly
import os
import random
import string

odoo = odooly.Client(os.environ['ODOO_URL'], os.environ['ODOO_DB'], os.environ['ODOO_USER'], os.environ['ODOO_PASSWORD'])

def _generate_promotional_code():
    code = ''.join([random.choice(string.ascii_letters) for _ in range(6)]).upper()
    if odoo.env['res.partner'].search_count([('promotional_code', '=', code)]) > 0:
        return _generate_promotional_code()
    return code

odoo.env['res.partner'].search([('participant', '=', False)]).write({
    'promotional_code': False
})

for partner in odoo.env['res.partner'].search([('participant', '=', True)]):
    partner.write({'promotional_code': _generate_promotional_code()})
    print(partner.promotional_code)

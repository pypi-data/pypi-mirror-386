import odooly
import os
import csv

odoo = odooly.Client(os.environ['ODOO_URL'], os.environ['ODOO_DB'], os.environ['ODOO_USER'], os.environ['ODOO_PASSWORD'])

active_stage = odoo.env['contract.participation.stage'].search([('name', '=', 'Activo')])
email_blacklist = odoo.env['mail.blacklist'].search([]).email
blacklist = set(odoo.env['res.partner'].search([('email', 'in', email_blacklist)]).id)

coop_plants = odoo.env['photovoltaic.power.station'].search([
    ('facility_owner', 'ilike', 'COOP')
])
active_contracts = odoo.env['contract.participation'].search([
    ('photovoltaic_power_station_id', 'in', coop_plants.id),
    ('stage_id', 'in', active_stage.id),
])
participants_coop = set(active_contracts.partner_id.id)

sl_plants = odoo.env['photovoltaic.power.station'].search([
    ('facility_owner', 'ilike', 'revoluci')
])
products_comunero = odoo.env['product.template'].search([
    ('name', 'ilike', 'comunero')
])
participants_sl = set(odoo.env['contract.participation'].search([
    ('photovoltaic_power_station_id', 'in', sl_plants.id),
    ('stage_id', 'in', active_stage.id),
    ('product_id', 'not in', products_comunero.id)
]).partner_id.id)

not_promotions = set(odoo.env['res.partner'].search([('promotions', '=', False)]).id)

partner_ids = (participants_coop | (participants_sl - not_promotions)) - blacklist

fields = ['id', 'name', 'email', 'contract_count']
with open('emails.csv', 'w+') as f:
    writer = csv.DictWriter(f, fields)
    writer.writeheader()
    writer.writerows(odoo.env['res.partner'].browse(partner_ids).read(fields))

# for id in partner_ids:
#     odoo.env['mail.template'].browse(ID).send_mail(id)

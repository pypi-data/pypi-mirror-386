{
    'name': "Photovoltaic Management Extended",
    'version': '16.0.1.1.1',
    'depends': [
        'photovoltaic_mgmt',
        'photovoltaic_participant_liquidations',
        'photovoltaic_participant_activities',
        'stock'
    ],
    'author': "Librecoop",
    'license': 'LGPL-3',
    'category': 'Sales',
    'description': """
    This module extendes the functionality of the Photovoltaic Management module
    """,
    "installable": True,
    "auto_install": True,
    "data": [
        "security/ir.model.access.csv",
        "views/contract_participation.xml",
        "views/photovoltaic_power_station.xml",
        "wizard/account_allocation_state_update_wizard_view.xml",
        "views/account_allocation.xml",
        "views/res_partner.xml",
        "views/res_partner_friend.xml",
        "views/res_partner_interest.xml"
    ],
}

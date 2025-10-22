# Copyright 2020 Camptocamp
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Stock Release Channels",
    "summary": "Manage workload in WMS with release channels",
    "version": "18.0.1.2.0",
    "development_status": "Beta",
    "license": "AGPL-3",
    "author": "Camptocamp, BCIM, ACSONE SA/NV, Odoo Community Association (OCA)",
    "maintainers": ["sebalix", "jbaudoux", "mt-software-de"],
    "website": "https://github.com/OCA/stock-logistics-release-channel",
    "depends": [
        "web",
        "stock_available_to_promise_release",  # OCA/stock-logistics-reservation
        "queue_job",  # OCA/queue
    ],
    "data": [
        "security/stock_release_channel.xml",
        "views/res_partner.xml",
        "views/stock_release_channel_views.xml",
        "views/stock_picking_views.xml",
        "views/res_config_settings.xml",
        "data/queue_job_data.xml",
        "data/ir_cron_data.xml",
    ],
    "demo": [
        "demo/stock_release_channel.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "stock_release_channel/static/src/scss/stock_release_channel.scss",
            "stock_release_channel/static/src/js/progressbar_fractional_widget.esm.js",
        ],
    },
    "installable": True,
}

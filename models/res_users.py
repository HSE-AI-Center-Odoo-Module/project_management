"""User Model Extension
Sets default home action for users from configuration.
"""
from odoo import models, api


class ResUsers(models.Model):
    """Extended user model"""
    _inherit = 'res.users'

    @api.model
    def default_get(self, fields):
        """Set default home action from system parameter"""
        # Get standard Odoo defaults
        defaults = super(ResUsers, self).default_get(fields)

        # If action_id not already set
        if 'action_id' not in defaults:
            # Look for system parameter
            default_home_action_id = self.env['ir.config_parameter'].sudo().get_param(
                'web.default_home_action_id'
            )

            # If valid numeric ID
            if default_home_action_id and default_home_action_id.isdigit():
                defaults['action_id'] = int(default_home_action_id)

        return defaults
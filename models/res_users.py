from odoo import models, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def default_get(self, fields):
        # Получаем стандартные значения Odoo
        defaults = super(ResUsers, self).default_get(fields)
        
        # Если action_id еще не задан (например, через контекст)
        if 'action_id' not in defaults:
            # Ищем наш системный параметр
            default_home_action_id = self.env['ir.config_parameter'].sudo().get_param('web.default_home_action_id')
            
            # Если параметр найден и он число (ID действия)
            if default_home_action_id and default_home_action_id.isdigit():
                defaults['action_id'] = int(default_home_action_id)
        
        return defaults
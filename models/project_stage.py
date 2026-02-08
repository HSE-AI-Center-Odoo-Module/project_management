from odoo import models, fields, api
from odoo.exceptions import ValidationError

class UniversityProjectStage(models.Model):
    _name = 'university.project.stage'
    _description = 'Project Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence'

    name = fields.Char(string="Stage Name", required=True, tracking=True)
    project_id = fields.Many2one('project.project', string="Project", required=True, ondelete='cascade')
    
    # ПРИЗНАК МЕНЕДЖЕРА
    is_manager = fields.Boolean(related="project_id.is_manager", readonly=True)

    # СТАТУС
    status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed'),
        ('cancel', 'Cancelled')
    ], string="Status", default='draft', tracking=True)

    # ДАТЫ
    date_start = fields.Date(string="Start Date", tracking=True)
    date_end = fields.Date(string="End Date", tracking=True)
    
    # ВОТ ЭТОГО ПОЛЯ НЕ ХВАТАЛО:
    date_error_msg = fields.Char(compute="_compute_date_error_msg")

    description = fields.Html(string="Description")
    sequence = fields.Integer(default=10)

    # ДОКУМЕНТЫ (Убедитесь, что в модели university.project.document есть поле stage_id)
    # Если вы хотите использовать ту же модель, что и в проекте, 
    # в ней должно быть поле Many2one на эту модель.
    document_ids = fields.One2many("university.project.document", "stage_id", string="Documents")


    history_ids = fields.One2many(
        'university.project.stage.history', 
        'stage_id', 
        string="History Log"
    )

    @api.depends('date_start', 'date_end')
    def _compute_date_error_msg(self):
        for stage in self:
            if stage.date_start and stage.date_end and stage.date_end < stage.date_start:
                stage.date_error_msg = "Внимание: Дата окончания не может быть раньше даты начала!"
            else:
                stage.date_error_msg = False

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for stage in self:
            if stage.date_start and stage.date_end and stage.date_end < stage.date_start:
                raise ValidationError('End Date cannot be earlier than Start Date.')
            
    def action_view_tasks(self):
        self.ensure_one()
        # Если вы хотите видеть задачи ЭТОГО ЭТАПА, домен должен быть специфичным
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'res_model': 'project.task',
            'view_mode': 'kanban,form,list',
            'domain': [('project_id', '=', self.project_id.id)], # Здесь можно добавить фильтр по этапу, если он есть в задачах
            'context': {'default_project_id': self.project_id.id},
            'target': 'current',
        }

class UniversityProjectStageHistory(models.Model):
    _name = 'university.project.stage.history'
    _description = 'Project Stage History'
    _order = 'date desc'

    stage_id = fields.Many2one('university.project.stage', string="Stage", ondelete='cascade')
    name = fields.Char(string="Action", required=True)
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    date = fields.Datetime(string="Date", default=fields.Datetime.now)

    def write(self, vals):
        if 'status' in vals:
            for rec in self:
                self.env['university.project.stage.history'].create({
                    'stage_id': rec.id,
                    'name': f"Статус изменен с {rec.status} на {vals['status']}",
                })
        return super(UniversityProjectStage, self).write(vals)
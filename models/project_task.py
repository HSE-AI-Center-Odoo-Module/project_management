from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProjectTask(models.Model):
    _inherit = "project.task"

# Кастомное поле проекта
    projectID = fields.Many2one(
        'project.project',
        string="Проект",
        readonly=True,
        store=True,
        compute="_compute_project_id_custom",
        # Подтягиваем проект из контекста при создании
        default=lambda self: self.env.context.get('default_project_id'),
    )

    @api.depends('project_id')
    def _compute_project_id_custom(self):
        """Синхронизирует кастомное поле со стандартным полем Odoo"""
        for task in self:
            if task.project_id:
                task.projectID = task.project_id
            elif not task.projectID and self.env.context.get('default_project_id'):
                # Если задача еще не сохранена, берем из контекста
                task.projectID = self.env.context.get('default_project_id')

    # 2. Поля дат и стадия
    date_start = fields.Date(string="Дата начала")
    date_end = fields.Date(string="Дата конца")

    # 3. Документы (убедитесь, что в модели university.project.document есть поле task_id)
    document_ids = fields.One2many(
        "university.project.document",
        "task_id", # Поле обратной связи в модели документа
        string="Documents"
    )

    # Техническое поле для прав доступа (если оно используется в этапах)
    is_manager = fields.Boolean(compute="_compute_is_manager")

    @api.depends('project_id')
    def _compute_is_manager(self):
        # Проверяем, является ли пользователь глобальным администратором вашей системы
        is_admin = self.env.user.has_group('project_management.administrator')
        
        for rec in self:
            # Пользователь может редактировать, если:
            # 1. Он администратор системы
            # 2. Он является менеджером в этом конкретном проекте
            is_project_manager = False
            if rec.project_id:
                is_project_manager = self.env.user in rec.project_id.project_manager_id
            
            rec.is_manager = is_admin or is_project_manager

    # Валидация дат
    @api.constrains('date_end', 'university_stage_id')
    def _check_dates_against_stage(self):
        for task in self:
            if task.date_end and task.university_stage_id and task.university_stage_id.date_end:
                if task.date_end > task.university_stage_id.date_end:
                    raise ValidationError(
                        f"Дата конца задачи ({task.date_end}) не может быть позже "
                        f"даты конца этапа ({task.university_stage_id.date_end})"
                    )

    # 2. Поле для привязки к этапу университета
    university_stage_id = fields.Many2one(
        'university.project.stage', 
        string="Этап проекта",
        tracking=True
    )
    
        # Техническое поле для фильтрации исполнителей (вы уже его создали)
    project_member_user_ids = fields.Many2many(
        related="project_id.member_user_ids",
        string="Allowed Assignees",
        readonly=True
    )

    # Добавим приоритет (звездочки), если его нет
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], default='0', string="Priority")

    stage_id = fields.Many2one(
        'project.task.type', 
        string='Stage', 
        ondelete='restrict', 
        tracking=True, 
        index=True, 
        copy=False,
        group_expand='_read_group_stage_ids'
    )

    @api.model
    def _read_group_stage_ids(self, stages, domain, order=None, **kwargs):
        """
        Метод для Odoo 18, который возвращает стадии для канбана.
        """
        # Извлекаем ID текущего проекта из контекста
        project_id = self._context.get('default_project_id')
        
        if project_id:
            # Находим проект и берем стадии, которые к нему привязаны
            project = self.env['project.project'].browse(project_id)
            if project.exists() and project.type_ids:
                # Возвращаем именно те стадии, которые настроены для этого проекта
                return project.type_ids
        
        # Если мы не в контексте проекта, возвращаем стандартный набор стадий
        return stages
    
    @api.model_create_multi
    def create(self, vals_list):
        # Проверяем, является ли пользователь администратором системы
        if not self.env.user.has_group('base.group_system'):
            raise ValidationError("Создание новых фаз проекта вручную запрещено. "
                                 "Пожалуйста, используйте предустановленные этапы.")
        return super().create(vals_list)
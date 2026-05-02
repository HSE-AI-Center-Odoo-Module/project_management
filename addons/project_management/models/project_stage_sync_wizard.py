from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProjectStageSyncWizard(models.TransientModel):
    _name = "project.stage.sync.wizard"
    _description = "Project Task Stages Sync Wizard"

    scope = fields.Selection(
        [
            ("all", "All projects"),
            ("selected", "Selected projects"),
        ],
        string="Scope",
        required=True,
        default=lambda self: self._default_scope(),
    )
    dry_run = fields.Boolean(
        string="Preview only (do not write changes)",
        default=False,
    )
    move_tasks = fields.Boolean(
        string="Move existing tasks to new stages",
        default=True,
    )
    project_ids = fields.Many2many(
        "project.project",
        string="Selected projects",
    )
    project_count = fields.Integer(
        string="Projects to update",
        compute="_compute_project_count",
        readonly=True,
    )

    @api.model
    def _default_scope(self):
        if self.env.context.get("active_model") == "project.project" and self.env.context.get("active_ids"):
            return "selected"
        return "all"

    @api.model
    def default_get(self, field_list):
        values = super().default_get(field_list)
        if "project_ids" in field_list:
            if self.env.context.get("active_model") == "project.project":
                active_ids = self.env.context.get("active_ids") or []
                if active_ids:
                    values["project_ids"] = [(6, 0, active_ids)]
        return values

    def _get_target_projects(self):
        self.ensure_one()
        project_model = self.env["project.project"]
        if self.scope == "selected":
            if self.project_ids:
                return self.project_ids.with_context(active_test=False).exists()
            if self.env.context.get("active_model") == "project.project":
                active_ids = self.env.context.get("active_ids") or []
                if active_ids:
                    return project_model.with_context(active_test=False).browse(active_ids).exists()
            raise UserError(
                _(
                    "For selected scope, open from project list/form context "
                    "or choose projects manually in this wizard."
                )
            )
        return project_model.with_context(active_test=False).search([])

    @api.depends("scope", "project_ids")
    def _compute_project_count(self):
        for wizard in self:
            if wizard.scope == "all":
                wizard.project_count = self.env["project.project"].with_context(active_test=False).search_count([])
            elif wizard.project_ids:
                wizard.project_count = len(wizard.project_ids)
            elif (
                self.env.context.get("active_model") == "project.project"
                and self.env.context.get("active_ids")
            ):
                wizard.project_count = len(self.env.context.get("active_ids"))
            else:
                wizard.project_count = 0

    def action_apply(self):
        self.ensure_one()
        stage_xml_ids = [
            "project_management.phase_backlog",
            "project_management.phase_spec",
            "project_management.phase_dev",
            "project_management.phase_test",
            "project_management.phase_delivered",
            "project_management.phase_archive",
        ]

        ordered_templates = []
        for xml_id in stage_xml_ids:
            stage = self.env.ref(xml_id, raise_if_not_found=False)
            if stage:
                ordered_templates.append(stage)

        if not ordered_templates:
            raise UserError(_("No default stages found. Check project_task_phases_data.xml."))

        projects = self._get_target_projects()
        if not projects:
            raise UserError(_("No projects found for selected scope."))

        moved_tasks_count = 0

        if not self.dry_run:
            task_model = self.env["project.task"].with_context(active_test=False)
            # Create project-specific stage copies to avoid cross-project side effects.
            # Otherwise deleting a column in one project can affect others because of shared stages.
            for project in projects:
                task_stage_set = task_model.search(
                    [("project_id", "=", project.id)]
                ).mapped("stage_id").exists()
                # Include both configured project stages and stages currently used by project tasks.
                old_stages = (project.type_ids | task_stage_set).sorted(key=lambda s: (s.sequence, s.id))
                project_stage_ids = []
                new_stages = self.env["project.task.type"]
                for index, template_stage in enumerate(ordered_templates, start=1):
                    cloned_stage = template_stage.copy(
                        {
                            "name": template_stage.name,
                            # Enforce deterministic order exactly as in stage_xml_ids list.
                            "sequence": index * 10,
                            "project_ids": [(6, 0, [project.id])],
                        }
                    )
                    # Some Odoo versions still append "(copy)" in copy(); enforce original label.
                    if cloned_stage.name != template_stage.name:
                        cloned_stage.name = template_stage.name
                    project_stage_ids.append(cloned_stage.id)
                    new_stages |= cloned_stage
                project.type_ids = [(6, 0, project_stage_ids)]

                if self.move_tasks and old_stages:
                    new_stages_sorted = new_stages.sorted(key=lambda s: (s.sequence, s.id))
                    new_by_name = {}
                    for stage in new_stages_sorted:
                        if stage.name not in new_by_name:
                            new_by_name[stage.name] = stage

                    old_to_new = {}
                    for idx, old_stage in enumerate(old_stages):
                        target_stage = new_by_name.get(old_stage.name)
                        if not target_stage and idx < len(new_stages_sorted):
                            target_stage = new_stages_sorted[idx]
                        if target_stage:
                            old_to_new[old_stage.id] = target_stage.id

                    if old_to_new:
                        for old_stage_id, new_stage_id in old_to_new.items():
                            tasks_to_move = task_model.search(
                                [
                                    ("project_id", "=", project.id),
                                    ("stage_id", "=", old_stage_id),
                                ]
                            )
                            moved_tasks_count += len(tasks_to_move)
                            if tasks_to_move:
                                tasks_to_move.write({"stage_id": new_stage_id})
        elif self.move_tasks:
            # Dry run estimate for tasks that will be affected.
            moved_tasks_count = self.env["project.task"].with_context(active_test=False).search_count(
                [("project_id", "in", projects.ids)]
            )

        message = _(
            "Scope: %(scope)s. Projects: %(projects)s. Stage templates: %(stages)s. "
            "Project-specific copies created: %(copies)s. Tasks moved: %(tasks)s. Dry run: %(dry_run)s."
        ) % {
            "scope": self.scope,
            "projects": len(projects),
            "stages": len(ordered_templates),
            "copies": len(projects) * len(ordered_templates),
            "tasks": moved_tasks_count,
            "dry_run": "yes" if self.dry_run else "no",
        }
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Task stages sync completed"),
                "message": message,
                "type": "success",
                "sticky": False,
            },
        }

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProjectStatusMachine(TransactionCase):
    """Tests for project_status state machine on project.project."""

    def setUp(self):
        super().setUp()
        self.Users = self.env["res.users"].with_context(no_reset_password=True)

        self.group_employee = self.env.ref("project_management.employee")
        self.group_admin = self.env.ref("project_management.administrator")
        self.role_manager = self.env.ref("project_management.role_manager")

        self.user_admin = self.Users.create({
            "name": "Pipeline Admin",
            "login": "pipeline_admin",
            "email": "pipeline_admin@example.com",
            "groups_id": [(6, 0, [self.group_admin.id])],
        })
        self.user_pm = self.Users.create({
            "name": "Pipeline PM",
            "login": "pipeline_pm",
            "email": "pipeline_pm@example.com",
            "groups_id": [(6, 0, [self.group_employee.id])],
        })

        self.project = self.env["project.project"].with_user(self.user_admin).create({
            "name": "Pipeline Test Project",
        })
        self.env["university.project.member"].create({
            "project_id": self.project.id,
            "user_id": self.user_pm.id,
            "role_id": self.role_manager.id,
        })

    def _project_as(self, user):
        return self.project.with_user(user)

    # ------------------------------------------------------------------
    # Happy-path transitions
    # ------------------------------------------------------------------

    def test_pm_can_start_project(self):
        self._project_as(self.user_pm).action_start()
        self.assertEqual(self.project.project_status, "active")

    def test_pm_can_mark_done(self):
        self._project_as(self.user_pm).action_start()
        self._project_as(self.user_pm).action_done()
        self.assertEqual(self.project.project_status, "done")

    def test_pm_can_cancel_project(self):
        self._project_as(self.user_pm).action_start()
        self._project_as(self.user_pm).action_cancel()
        self.assertEqual(self.project.project_status, "cancel")

    def test_admin_can_resume_from_done(self):
        self._project_as(self.user_pm).action_start()
        self._project_as(self.user_pm).action_done()
        self._project_as(self.user_admin).action_resume()
        self.assertEqual(self.project.project_status, "active")

    def test_admin_can_resume_from_cancel(self):
        self._project_as(self.user_pm).action_start()
        self._project_as(self.user_pm).action_cancel()
        self._project_as(self.user_admin).action_resume()
        self.assertEqual(self.project.project_status, "active")

    # ------------------------------------------------------------------
    # Blocked transitions for PM
    # ------------------------------------------------------------------

    def test_pm_cannot_skip_draft_to_done(self):
        with self.assertRaises(UserError):
            self._project_as(self.user_pm).write({"project_status": "done"})

    def test_pm_cannot_skip_draft_to_cancel(self):
        with self.assertRaises(UserError):
            self._project_as(self.user_pm).write({"project_status": "cancel"})

    def test_pm_cannot_resume_from_done(self):
        self._project_as(self.user_pm).action_start()
        self._project_as(self.user_pm).action_done()
        with self.assertRaises(UserError):
            self._project_as(self.user_pm).action_resume()

    def test_pm_cannot_resume_from_cancel(self):
        self._project_as(self.user_pm).action_start()
        self._project_as(self.user_pm).action_cancel()
        with self.assertRaises(UserError):
            self._project_as(self.user_pm).action_resume()

    # ------------------------------------------------------------------
    # Admin bypasses all restrictions
    # ------------------------------------------------------------------

    def test_admin_can_set_any_status_directly(self):
        self._project_as(self.user_admin).write({"project_status": "done"})
        self.assertEqual(self.project.project_status, "done")
        self._project_as(self.user_admin).write({"project_status": "draft"})
        self.assertEqual(self.project.project_status, "draft")


@tagged("post_install", "-at_install")
class TestProjectStagePipeline(TransactionCase):
    """Tests for university.project.stage state machine and approval gate."""

    def setUp(self):
        super().setUp()
        self.Users = self.env["res.users"].with_context(no_reset_password=True)
        self.Stage = self.env["university.project.stage"]
        self.Task = self.env["project.task"]
        self.ApprovalItem = self.env["university.task.approval.item"]

        self.group_employee = self.env.ref("project_management.employee")
        self.group_admin = self.env.ref("project_management.administrator")
        self.role_manager = self.env.ref("project_management.role_manager")
        self.role_developer = self.env.ref("project_management.role_developer")

        self.user_admin = self.Users.create({
            "name": "Stage Admin",
            "login": "stage_admin",
            "email": "stage_admin@example.com",
            "groups_id": [(6, 0, [self.group_admin.id])],
        })
        self.user_pm = self.Users.create({
            "name": "Stage PM",
            "login": "stage_pm",
            "email": "stage_pm@example.com",
            "groups_id": [(6, 0, [self.group_employee.id])],
        })
        self.user_dev = self.Users.create({
            "name": "Stage Dev",
            "login": "stage_dev",
            "email": "stage_dev@example.com",
            "groups_id": [(6, 0, [self.group_employee.id])],
        })

        self.project = self.env["project.project"].with_user(self.user_admin).create({
            "name": "Stage Pipeline Project",
        })
        self.env["university.project.member"].create({
            "project_id": self.project.id,
            "user_id": self.user_pm.id,
            "role_id": self.role_manager.id,
        })
        self.env["university.project.member"].create({
            "project_id": self.project.id,
            "user_id": self.user_dev.id,
            "role_id": self.role_developer.id,
        })

        self.stage = self.Stage.with_user(self.user_admin).create({
            "name": "Alpha",
            "project_id": self.project.id,
        })

    def _stage_as(self, user):
        return self.stage.with_user(user)

    # ------------------------------------------------------------------
    # Happy-path stage transitions
    # ------------------------------------------------------------------

    def test_pm_can_start_stage(self):
        self._stage_as(self.user_pm).action_start()
        self.assertEqual(self.stage.status, "in_progress")

    def test_pm_can_complete_stage_without_tasks(self):
        self._stage_as(self.user_pm).action_start()
        self._stage_as(self.user_pm).action_done()
        self.assertEqual(self.stage.status, "done")

    def test_pm_can_cancel_stage_from_draft(self):
        self._stage_as(self.user_pm).action_cancel()
        self.assertEqual(self.stage.status, "cancel")

    def test_pm_can_reset_cancelled_stage_to_draft(self):
        self._stage_as(self.user_pm).action_cancel()
        self._stage_as(self.user_pm).action_reset_to_draft()
        self.assertEqual(self.stage.status, "draft")

    # ------------------------------------------------------------------
    # Blocked transitions for PM
    # ------------------------------------------------------------------

    def test_pm_cannot_go_draft_to_done_directly(self):
        with self.assertRaises(UserError):
            self._stage_as(self.user_pm).write({"status": "done"})

    def test_pm_cannot_go_in_progress_to_draft(self):
        self._stage_as(self.user_pm).action_start()
        with self.assertRaises(UserError):
            self._stage_as(self.user_pm).write({"status": "draft"})

    # ------------------------------------------------------------------
    # Approval gate: cannot complete stage when tasks have pending approvals
    # ------------------------------------------------------------------

    def test_stage_completion_blocked_by_unapproved_task(self):
        task = self.Task.with_user(self.user_admin).create({
            "name": "Gated Task",
            "project_id": self.project.id,
            "user_ids": [(6, 0, [self.user_dev.id])],
            "university_stage_id": self.stage.id,
        })
        self.ApprovalItem.with_user(self.user_pm).create({
            "name": "Review backend",
            "task_id": task.id,
            "responsible_id": self.user_dev.id,
        })
        self._stage_as(self.user_pm).action_start()
        with self.assertRaises(UserError):
            self._stage_as(self.user_pm).action_done()

    def test_stage_completion_allowed_when_all_approved(self):
        task = self.Task.with_user(self.user_admin).create({
            "name": "Approved Task",
            "project_id": self.project.id,
            "user_ids": [(6, 0, [self.user_dev.id])],
            "university_stage_id": self.stage.id,
        })
        item = self.ApprovalItem.with_user(self.user_pm).create({
            "name": "Review backend",
            "task_id": task.id,
            "responsible_id": self.user_dev.id,
        })
        item.with_user(self.user_dev).action_approve()
        self._stage_as(self.user_pm).action_start()
        self._stage_as(self.user_pm).action_done()
        self.assertEqual(self.stage.status, "done")

    def test_stage_completion_blocked_only_when_approval_items_exist(self):
        # Task without approval items should NOT block stage completion
        self.Task.with_user(self.user_admin).create({
            "name": "No Approval Task",
            "project_id": self.project.id,
            "user_ids": [(6, 0, [self.user_dev.id])],
            "university_stage_id": self.stage.id,
        })
        self._stage_as(self.user_pm).action_start()
        self._stage_as(self.user_pm).action_done()
        self.assertEqual(self.stage.status, "done")

    # ------------------------------------------------------------------
    # History logging
    # ------------------------------------------------------------------

    def test_status_change_logged_in_history(self):
        self._stage_as(self.user_pm).action_start()
        history = self.stage.history_ids
        self.assertTrue(history)
        self.assertIn("Status", history[0].name)

    def test_history_records_old_and_new_status(self):
        self._stage_as(self.user_pm).action_start()
        entry = self.stage.history_ids[0]
        self.assertIn("Draft", entry.name)
        self.assertIn("In Progress", entry.name)

    # ------------------------------------------------------------------
    # Date validation
    # ------------------------------------------------------------------

    def test_end_date_before_start_date_raises_validation(self):
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.stage.with_user(self.user_admin).write({
                "date_start": "2025-06-01",
                "date_end": "2025-05-01",
            })

    def test_valid_date_range_accepted(self):
        self.stage.with_user(self.user_admin).write({
            "date_start": "2025-05-01",
            "date_end": "2025-06-30",
        })
        self.assertEqual(str(self.stage.date_start), "2025-05-01")

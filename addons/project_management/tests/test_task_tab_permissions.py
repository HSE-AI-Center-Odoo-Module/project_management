from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTaskTabPermissions(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Users = self.env["res.users"].with_context(no_reset_password=True)
        self.Project = self.env["project.project"]
        self.Task = self.env["project.task"]
        self.Member = self.env["university.project.member"]
        self.TaskTab = self.env["university.task.tab"]
        self.ApprovalItem = self.env["university.task.approval.item"]
        self.TaskTabComment = self.env["university.task.tab.comment"]
        self.ApprovalComment = self.env["university.task.approval.comment"]

        self.group_employee = self.env.ref("project_management.employee")
        self.group_admin = self.env.ref("project_management.administrator")
        self.role_manager = self.env.ref("project_management.role_manager")
        self.role_developer = self.env.ref("project_management.role_developer")

        self.user_admin = self.Users.create(
            {
                "name": "Tabs Admin",
                "login": "tabs_admin",
                "email": "tabs_admin@example.com",
                "groups_id": [(6, 0, [self.group_admin.id])],
            }
        )
        self.user_pm = self.Users.create(
            {
                "name": "Tabs PM",
                "login": "tabs_pm",
                "email": "tabs_pm@example.com",
                "groups_id": [(6, 0, [self.group_employee.id])],
            }
        )
        self.user_responsible = self.Users.create(
            {
                "name": "Tabs Responsible",
                "login": "tabs_responsible",
                "email": "tabs_responsible@example.com",
                "groups_id": [(6, 0, [self.group_employee.id])],
            }
        )
        self.user_other_assignee = self.Users.create(
            {
                "name": "Tabs Other Assignee",
                "login": "tabs_other_assignee",
                "email": "tabs_other_assignee@example.com",
                "groups_id": [(6, 0, [self.group_employee.id])],
            }
        )
        self.user_not_assignee = self.Users.create(
            {
                "name": "Tabs Not Assignee",
                "login": "tabs_not_assignee",
                "email": "tabs_not_assignee@example.com",
                "groups_id": [(6, 0, [self.group_employee.id])],
            }
        )

        self.project = self.Project.with_user(self.user_admin).create({"name": "Tabs Project"})
        self.Member.create(
            {
                "project_id": self.project.id,
                "user_id": self.user_pm.id,
                "role_id": self.role_manager.id,
            }
        )
        self.Member.create(
            {
                "project_id": self.project.id,
                "user_id": self.user_responsible.id,
                "role_id": self.role_developer.id,
            }
        )
        self.Member.create(
            {
                "project_id": self.project.id,
                "user_id": self.user_other_assignee.id,
                "role_id": self.role_developer.id,
            }
        )

        self.task = self.Task.with_user(self.user_admin).create(
            {
                "name": "Task For Tabs",
                "project_id": self.project.id,
                "user_ids": [(6, 0, [self.user_responsible.id, self.user_other_assignee.id])],
            }
        )

    def test_tab_responsible_must_be_task_assignee(self):
        with self.assertRaises(ValidationError):
            self.TaskTab.with_user(self.user_pm).create(
                {
                    "name": "Spec",
                    "task_id": self.task.id,
                    "responsible_id": self.user_not_assignee.id,
                }
            )

    def test_only_responsible_manager_or_admin_can_edit_tab(self):
        tab = self.TaskTab.with_user(self.user_pm).create(
            {
                "name": "Spec",
                "task_id": self.task.id,
                "responsible_id": self.user_responsible.id,
                "content": "<p>Initial</p>",
            }
        )
        tab.with_user(self.user_responsible).write({"content": "<p>Updated by responsible</p>"})
        tab.with_user(self.user_pm).write({"name": "Spec Updated by PM"})
        tab.with_user(self.user_admin).write({"name": "Spec Updated by Admin"})
        with self.assertRaises(AccessError):
            tab.with_user(self.user_other_assignee).write({"name": "Illegal update"})

    def test_approval_item_permissions_follow_same_rule(self):
        item = self.ApprovalItem.with_user(self.user_pm).create(
            {
                "name": "Approve API contract",
                "task_id": self.task.id,
                "responsible_id": self.user_responsible.id,
            }
        )
        item.with_user(self.user_responsible).action_approve()
        self.assertTrue(item.is_approved)
        with self.assertRaises(AccessError):
            item.with_user(self.user_other_assignee).write({"is_approved": False})
        item.with_user(self.user_pm).action_revoke()
        self.assertFalse(item.is_approved)

    def test_task_tab_comments_allow_assignee_but_block_non_assignee(self):
        tab = self.TaskTab.with_user(self.user_pm).create(
            {
                "name": "Spec",
                "task_id": self.task.id,
                "responsible_id": self.user_responsible.id,
            }
        )
        comment = self.TaskTabComment.with_user(self.user_other_assignee).create(
            {
                "tab_id": tab.id,
                "message": "<p>Looks good</p>",
            }
        )
        self.assertEqual(comment.author_id, self.user_other_assignee)
        with self.assertRaises(AccessError):
            self.TaskTabComment.with_user(self.user_not_assignee).create(
                {
                    "tab_id": tab.id,
                    "message": "<p>Cannot comment</p>",
                }
            )

    def test_approval_comments_allow_assignee_but_block_non_assignee(self):
        item = self.ApprovalItem.with_user(self.user_pm).create(
            {
                "name": "Approve API contract",
                "task_id": self.task.id,
                "responsible_id": self.user_responsible.id,
            }
        )
        comment = self.ApprovalComment.with_user(self.user_other_assignee).create(
            {
                "approval_item_id": item.id,
                "message": "<p>Need one small fix</p>",
            }
        )
        self.assertEqual(comment.author_id, self.user_other_assignee)
        with self.assertRaises(AccessError):
            self.ApprovalComment.with_user(self.user_not_assignee).create(
                {
                    "approval_item_id": item.id,
                    "message": "<p>Cannot comment</p>",
                }
            )

    def test_approval_progress_computation(self):
        first = self.ApprovalItem.with_user(self.user_pm).create(
            {
                "name": "Approve Backend",
                "task_id": self.task.id,
                "responsible_id": self.user_responsible.id,
            }
        )
        self.ApprovalItem.with_user(self.user_pm).create(
            {
                "name": "Approve Frontend",
                "task_id": self.task.id,
                "responsible_id": self.user_other_assignee.id,
            }
        )
        self.task.invalidate_recordset(["approval_count", "approval_done_count", "approval_progress"])
        self.assertEqual(self.task.approval_count, 2)
        self.assertEqual(self.task.approval_done_count, 0)
        self.assertEqual(self.task.approval_progress, 0.0)

        first.with_user(self.user_responsible).action_approve()
        self.task.invalidate_recordset(["approval_count", "approval_done_count", "approval_progress"])
        self.assertEqual(self.task.approval_done_count, 1)
        self.assertEqual(self.task.approval_progress, 50.0)

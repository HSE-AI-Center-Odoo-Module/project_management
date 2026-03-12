from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTaskBoardAccess(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Users = self.env["res.users"].with_context(no_reset_password=True)
        self.Project = self.env["project.project"]
        self.Task = self.env["project.task"]
        self.Member = self.env["university.project.member"]

        self.group_employee = self.env.ref("project_management.employee")
        self.group_admin = self.env.ref("project_management.administrator")
        self.group_project_manager = self.env.ref("project.group_project_manager")
        self.role_manager = self.env.ref("project_management.role_manager")
        self.role_developer = self.env.ref("project_management.role_developer")

        self.user_employee = self.Users.create(
            {
                "name": "PM Test Employee",
                "login": "pm_test_employee",
                "email": "pm_test_employee@example.com",
                "groups_id": [(6, 0, [self.group_employee.id, self.group_project_manager.id])],
            }
        )
        self.user_pm = self.Users.create(
            {
                "name": "PM Test Manager",
                "login": "pm_test_manager",
                "email": "pm_test_manager@example.com",
                "groups_id": [(6, 0, [self.group_employee.id])],
            }
        )
        self.user_admin = self.Users.create(
            {
                "name": "PM Test Admin",
                "login": "pm_test_admin",
                "email": "pm_test_admin@example.com",
                "groups_id": [(6, 0, [self.group_admin.id])],
            }
        )
        self.user_other = self.Users.create(
            {
                "name": "PM Test Other",
                "login": "pm_test_other",
                "email": "pm_test_other@example.com",
                "groups_id": [(6, 0, [self.group_employee.id])],
            }
        )

        self.project = self.Project.with_user(self.user_admin).create(
            {
                "name": "Access Matrix Project",
            }
        )
        self.project_hidden = self.Project.with_user(self.user_admin).create(
            {
                "name": "Hidden Project",
            }
        )

        self.Member.create(
            {
                "project_id": self.project.id,
                "user_id": self.user_employee.id,
                "role_id": self.role_developer.id,
            }
        )
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
                "user_id": self.user_other.id,
                "role_id": self.role_developer.id,
            }
        )

        self.task_assigned = self.Task.with_user(self.user_admin).create(
            {
                "name": "Assigned to employee",
                "project_id": self.project.id,
                "user_ids": [(6, 0, [self.user_employee.id])],
            }
        )
        self.task_other = self.Task.with_user(self.user_admin).create(
            {
                "name": "Assigned to other",
                "project_id": self.project.id,
                "user_ids": [(6, 0, [self.user_other.id])],
            }
        )

    def _get_task_domain(self, user):
        action = self.project.with_user(user).action_view_tasks()
        return action.get("domain", [])

    def test_employee_task_board_domain_is_limited_to_assigned(self):
        domain = self._get_task_domain(self.user_employee)
        self.assertIn(("project_id", "=", self.project.id), domain)
        self.assertIn(("user_ids", "in", self.user_employee.id), domain)

    def test_project_manager_task_board_domain_has_no_assignee_filter(self):
        domain = self._get_task_domain(self.user_pm)
        self.assertIn(("project_id", "=", self.project.id), domain)
        self.assertNotIn(("user_ids", "in", self.user_pm.id), domain)

    def test_admin_task_board_domain_has_no_assignee_filter(self):
        domain = self._get_task_domain(self.user_admin)
        self.assertIn(("project_id", "=", self.project.id), domain)
        self.assertNotIn(("user_ids", "in", self.user_admin.id), domain)

    def test_employee_project_visibility_is_limited_to_team_membership(self):
        visible_projects = self.Project.with_user(self.user_employee).search([])
        self.assertIn(self.project, visible_projects)
        self.assertNotIn(self.project_hidden, visible_projects)

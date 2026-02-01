# -*- coding: utf-8 -*-
{
    "name": "Project Management",
    "summary": "Project Management System for AI Research Centre HSE University",
    "category": "Project",
    "version": "18.0.0.1.0",
    "author": "Dandamaev Gadji",
    "license": "LGPL-3",
    "depends": [
                "base",
                "project", 
                "mail", 
    ],
    "data": [
        # Security
        "security/security.xml",
        "security/ir.model.access.csv",

        # Data
        "data/project_role_data.xml",

        # Views
        "views/project_views.xml",
        #'views/project_actions.xml',
    ],
    "application": True,
    "installable": True,
}

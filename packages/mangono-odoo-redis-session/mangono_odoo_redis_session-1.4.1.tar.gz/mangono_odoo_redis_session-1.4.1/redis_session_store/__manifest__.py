{
    "name": "Redis Session Store",
    "version": "1.4.1",
    "depends": ["base"],
    "author": "NDP Systemes",
    "license": "AGPL-3",
    "description": """Use Redis Session instead of File system""",
    "summary": "",
    "website": "",
    "category": "Tools",
    "auto_install": False,
    "installable": True,
    "application": False,
    "post_load": "_post_load_module",
    "external_dependencies": {
        "python": ["redis"],
    },
}

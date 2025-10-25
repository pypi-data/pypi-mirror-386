from setuptools import setup, find_packages

setup(
    name="github-backup-supabase",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click",
        "requests",
        "supabase",
        "python-dotenv"
    ],
    entry_points={
        "console_scripts": [
            "github-backup=github_backup_supabase.cli:cli",
        ],
    },
)

from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="github-backup-supabase",
    version="1.0.3",
    packages=find_packages(),
    install_requires=[
        "click",
        "requests",
        "supabase",
        "python-dotenv"
    ],
    entry_points={
        "console_scripts": [
            "github-backup-supabase=github_backup_supabase.cli:cli",
        ],
    },
    author="Hussnain Ahmad",
    description="A CLI tool to back up your GitHub repositories and upload to Supabase storage.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/itspsychocoder/github-backup-supabase"
)

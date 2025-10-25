# GitHub Backup CLI

A simple command-line tool to back up all your GitHub repositories locally or to Supabase storage so you will never lose your code again.

## Quick description

This small Python CLI clones all repositories accessible to the provided GitHub token into a temporary directory and packages them into a ZIP file (`github_backup.zip`). There's an `--upload` flag planned for uploading the archive to Supabase, but it's not implemented in the current script.

Files of interest:
- `script.py` — the CLI entry point (uses `click`, `requests`, and `git` via the system shell).


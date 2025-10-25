# GitHub Backup CLI

A simple command-line tool to back up all your GitHub repositories locally or to Supabase storage so you will never lose your code again.

## Installation

```bash
pip install github-backup-supabase
```

## Usage

```bash
# Basic backup (requires username)
github-backup-supabase run --username your-github-username

# Backup with token (for private repos)
github-backup-supabase run --username your-username --token ghp_xxxxx

# Backup and upload to Supabase
github-backup-supabase run --username your-username --upload --url https://xxx.supabase.co --key your-supabase-key --bucket your-bucket-name
```


## Environment Variables

You can set these instead of passing flags:

```bash
GITHUB_USERNAME=your-username
GITHUB_TOKEN=ghp_xxxxx
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-key
BUCKET_NAME=your-bucket-name
```

## Options

- `--username` - GitHub username **(required)**
- `--token` - GitHub token (optional, for private repos)
- `--output` - Custom folder name (default: timestamped)
- `--upload` - Upload to Supabase after backup
- `--url` - Supabase project URL
- `--key` - Supabase key (anon or service key)
- `--bucket` - Supabase bucket name (default: `github-backups`)

## What it does

1. Fetches all repositories from the GitHub user
2. Clones each repo to a local folder
3. Creates a ZIP archive
4. (Optional) Uploads to Supabase Storage
5. Cleans up local files

---

**Author:** Psycho Coder  
**GitHub:** [@itspsychocoder](https://github.com/itspsychocoder)  
**Website:** [hussnainahmad.tech](https://hussnainahmad.tech/)
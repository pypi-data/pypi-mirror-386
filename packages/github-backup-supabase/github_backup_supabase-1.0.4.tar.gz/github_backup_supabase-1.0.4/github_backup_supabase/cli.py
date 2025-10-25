import click
import os
import requests
import shutil
import time
from datetime import datetime
from supabase import create_client, Client

current_date_time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

@click.group()
def cli():
    """GitHub Backup CLI"""
    pass


@cli.command()
@click.option('--token', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--upload', is_flag=True, help='Upload to Supabase after backup')
@click.option('--output', default=f'github_backups_{current_date_time}', help='Folder to save backups')
@click.option('--url', envvar='SUPABASE_URL', help='Supabase project URL')
@click.option('--username', envvar='GITHUB_USERNAME', help='GitHub username you want to take backup from')
@click.option('--key', envvar='SUPABASE_KEY', help='Supabase anon or service key')
@click.option('--bucket', envvar="BUCKET_NAME", default='github-backups', help='Supabase bucket name')
@click.option('--help', is_flag=True, help='Show this message and exit')
def run(token, upload, output, url, key, bucket, help, username):
    """Clone and backup all GitHub repos"""
    if help:
        click.echo(run.get_help(click.Context(run)))
        return

    print("🔍 Fetching repositories...")

    if not username:
        print("❌ Github username is required. Pass it with --username")
        return



    if token:
        headers = {
            "Authorization": f"token {token}"
        }
    else:
        headers = {}


    isEnd = False
    repos = []
    page = 1
    while not isEnd:        
        response = requests.get(f"https://api.github.com/users/{username}/repos?per_page=100&page={page}", headers=headers)
        returnedRepos = response.json()
        print(f"📄 Fetched {len(returnedRepos)} repositories from page {page}.")
        if returnedRepos.__len__() < 1:
            isEnd = True
        else:
            repos.extend(returnedRepos)
            page += 1


    print(f"✅ Found {len(repos)} repositories.\n")

    # Create output folder (relative to current directory)
    backup_dir = os.path.join(os.getcwd(), output)
    os.makedirs(backup_dir, exist_ok=True)

    print(f"📂 Backup folder: {backup_dir}\n")

    for repo in repos:
        name = repo['name']
        clone_url = repo['clone_url']
        repo_path = os.path.join(backup_dir, name)
        print(f"\n\n📦 Cloning {name} ...")

        # Clone only latest snapshot (faster)
        os.system(f"git clone {clone_url} {repo_path}")
        time.sleep(0.5)  # Give Git a moment to finish writing files


    # Create a zip of all repos
    zip_path = os.path.join(os.getcwd(), f"github_backups_{current_date_time}.zip")
    shutil.make_archive(f"github_backups_{current_date_time}", 'zip', backup_dir)
    print(f"\n✅ All repos saved to {zip_path}")

    if upload:

        print("\n🚀 Uploading to Supabase")

        if not url or not key:
            print("❌ Cannot upload because Supabase URL or Key not provided. Pass with --url and --key or set SUPABASE_URL and SUPABASE_KEY environment variables.")
            return

        if not bucket:
            print("❌ Cannot upload because Supabase bucket name not provided. Pass bucket name with --bucket.")
            return

        supabase = create_client(url, key)

        with open(zip_path, "rb") as f:
            try:
                res = supabase.storage.from_(bucket).upload(f"github_backups_{current_date_time}.zip", f)
                public_url = supabase.storage.from_(bucket).get_public_url(f"github_backups_{current_date_time}.zip")

                print("✅ Upload complete!")
                print("🌐 Public URL:", public_url)
            except Exception as e:
                print("❌ Upload failed:", str(e))
                return

    print("🧹 Cleaning up...")
    shutil.rmtree(backup_dir, ignore_errors=True)
    print("✅ Done!")


if __name__ == '__main__':
    cli()

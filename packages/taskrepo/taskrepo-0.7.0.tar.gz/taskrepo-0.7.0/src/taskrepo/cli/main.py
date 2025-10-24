"""Main CLI entry point for TaskRepo."""

import click
from prompt_toolkit.shortcuts import confirm

from taskrepo.__version__ import __version__
from taskrepo.cli.commands.add import add
from taskrepo.cli.commands.config import config_cmd
from taskrepo.cli.commands.delete import delete
from taskrepo.cli.commands.done import done
from taskrepo.cli.commands.edit import edit
from taskrepo.cli.commands.extend import ext
from taskrepo.cli.commands.info import info
from taskrepo.cli.commands.list import list_tasks
from taskrepo.cli.commands.search import search
from taskrepo.cli.commands.sync import sync
from taskrepo.core.config import Config
from taskrepo.utils.update_checker import check_and_notify_updates


class OrderedGroup(click.Group):
    """Custom Click Group that displays commands in sections."""

    def format_commands(self, ctx, formatter):
        """Format commands with section headers."""
        # Define command sections in desired order
        sections = [
            (
                "Setup & Configuration",
                ["init", "create-repo", "config", "config-show"],
            ),
            (
                "Viewing Tasks",
                ["list", "search", "info"],
            ),
            (
                "Managing Tasks",
                ["add", "edit", "ext", "done", "del"],
            ),
            (
                "Repository Operations",
                ["repos", "sync"],
            ),
        ]

        # Build command dict
        commands = {}
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None:
                continue
            if cmd.hidden:
                continue
            commands[subcommand] = cmd

        # Format each section
        for section_name, command_names in sections:
            # Filter commands that exist in this section
            section_commands = [(name, commands[name]) for name in command_names if name in commands]

            if section_commands:
                with formatter.section(section_name):
                    formatter.write_dl(
                        [(name, cmd.get_short_help_str(limit=formatter.width)) for name, cmd in section_commands]
                    )


@click.group(cls=OrderedGroup)
@click.version_option(version=__version__, prog_name="taskrepo")
@click.pass_context
def cli(ctx):
    """TaskRepo - TaskWarrior-inspired task management with git and markdown.

    Manage your tasks as markdown files in git repositories.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Load configuration
    ctx.obj["config"] = Config()


@cli.result_callback()
@click.pass_context
def process_result(ctx, result, **kwargs):
    """Process result after command execution.

    This runs after any command completes and checks for updates.
    """
    # Check for updates after command completes
    check_and_notify_updates()


# Register commands
cli.add_command(add)
cli.add_command(config_cmd)
cli.add_command(list_tasks)
cli.add_command(edit)
cli.add_command(done)
cli.add_command(delete, name="del")  # Register only as "del"
cli.add_command(ext)
cli.add_command(info)
cli.add_command(search)
cli.add_command(sync)


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize TaskRepo configuration."""
    config = ctx.obj["config"]

    click.echo(f"TaskRepo configuration file: {config.config_path}")
    click.echo(f"Parent directory: {config.parent_dir}")

    if not config.parent_dir.exists():
        if confirm(f"Create parent directory {config.parent_dir}?"):
            config.parent_dir.mkdir(parents=True, exist_ok=True)
            click.secho(f"✓ Created {config.parent_dir}", fg="green")
        else:
            click.echo("Skipped directory creation")

    click.secho("✓ TaskRepo initialized", fg="green")


@cli.command()
@click.option("--name", "-n", help="Repository name (will be prefixed with 'tasks-')")
@click.option("--github", is_flag=True, help="Create GitHub repository")
@click.option("-o", "--org", help="GitHub organization/owner (required with --github)")
@click.option("--interactive/--no-interactive", "-i/-I", default=True, help="Use interactive mode")
@click.pass_context
def create_repo(ctx, name, github, org, interactive):
    """Create a new task repository."""
    from taskrepo.core.repository import RepositoryManager
    from taskrepo.tui import prompts

    config = ctx.obj["config"]
    manager = RepositoryManager(config.parent_dir)

    # Interactive mode
    if interactive:
        click.echo("Creating a new task repository...\n")
        click.echo("Note: Repository names will be automatically prefixed with 'tasks-'")
        click.echo("(e.g., entering 'work' will create 'tasks-work')\n")

        # Get repository name
        if not name:
            # Get existing repo names for validation
            existing_repos = manager.discover_repositories()
            existing_names = [repo.name for repo in existing_repos]
            name = prompts.prompt_repo_name(existing_names=existing_names)
            if not name:
                click.echo("Cancelled.")
                ctx.exit(0)

        # Ask about GitHub integration
        if github is False:  # Only prompt if not explicitly set via flag
            github = prompts.prompt_github_enabled()

        # Handle GitHub integration
        visibility = None
        if github:
            # Get organization if not provided
            if not org:
                # Use default from config if available
                default_org = config.default_github_org
                # Get existing orgs from repos for autocomplete
                existing_orgs = manager.get_github_orgs()
                org = prompts.prompt_github_org(default=default_org, existing_orgs=existing_orgs)
                if not org:
                    click.echo("Cancelled.")
                    ctx.exit(0)

            # Get visibility
            visibility = prompts.prompt_visibility()

    else:
        # Non-interactive mode - validate required fields
        if not name:
            click.secho("Error: --name is required in non-interactive mode", fg="red", err=True)
            ctx.exit(1)

        # Handle GitHub integration
        visibility = None
        if github:
            # Use default GitHub org from config if not provided
            if not org:
                org = config.default_github_org
                if not org:
                    click.secho(
                        "Error: --org is required when --github is specified (or set default_github_org in config)",
                        fg="red",
                        err=True,
                    )
                    ctx.exit(1)
            visibility = "private"  # Default to private in non-interactive mode

    try:
        repo = manager.create_repository(name, github_enabled=github, github_org=org, visibility=visibility)
        click.echo()
        click.secho(f"✓ Created repository: {repo.name} at {repo.path}", fg="green")
        if github:
            click.secho(f"✓ GitHub repository created: https://github.com/{org}/tasks-{name}", fg="green")
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        ctx.exit(1)
    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        ctx.exit(1)


@cli.command()
@click.pass_context
def repos(ctx):
    """List all task repositories."""
    from taskrepo.core.repository import RepositoryManager

    config = ctx.obj["config"]
    manager = RepositoryManager(config.parent_dir)

    repositories = manager.discover_repositories()

    if not repositories:
        click.echo(f"No repositories found in {config.parent_dir}")
        click.echo("Create one with: taskrepo create-repo <name>")
        return

    click.echo(f"Repositories in {config.parent_dir}:\n")
    for repo in repositories:
        click.echo(f"  • {repo}")


@cli.command()
@click.pass_context
def config_show(ctx):
    """Show current configuration."""
    config = ctx.obj["config"]

    click.echo("TaskRepo Configuration:\n")
    click.echo(f"  Config file: {config.config_path}")
    click.echo(f"  Parent directory: {config.parent_dir}")
    click.echo(f"  Default priority: {config.default_priority}")
    click.echo(f"  Default status: {config.default_status}")
    default_assignee = config.default_assignee if config.default_assignee else "(none)"
    click.echo(f"  Default assignee: {default_assignee}")
    default_github_org = config.default_github_org if config.default_github_org else "(none)"
    click.echo(f"  Default GitHub org: {default_github_org}")
    sort_by = ", ".join(config.sort_by)
    click.echo(f"  Sort by: {sort_by}")
    cluster_status = "enabled" if config.cluster_due_dates else "disabled"
    click.echo(f"  Due date clustering: {cluster_status}")


if __name__ == "__main__":
    cli()

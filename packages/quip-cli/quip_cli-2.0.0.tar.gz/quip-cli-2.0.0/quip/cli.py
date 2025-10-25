#!/usr/bin/env python3
"""
Click-based CLI for quip tool.
Maintains all original command aliases while providing better UX.
"""

import click
import sys
import logging
from quip import __version__, set_quiet_mode, cprint, resolve_quiet_mode
from quip.quip import Quip


# Common options that apply to all commands
config_option = click.option(
    '--config', '-c',
    type=click.Path(exists=True),
    help='Path of the global config. Default is ~/.uip_config.yml'
)

debug_option = click.option(
    '--debug', '-v',
    is_flag=True,
    help='Show debug logs'
)

template_option = click.option(
    '--template', '-t',
    is_flag=True,
    help='Create template instead of extension'
)


class AliasedGroup(click.Group):
    """Custom Click Group that supports command aliases."""
    
    def get_command(self, ctx, cmd_name):
        # Try to get the command directly
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        
        # Search through all commands for aliases
        for name, command in self.commands.items():
            if hasattr(command, 'aliases') and cmd_name in command.aliases:
                return command
        
        return None
    
    def format_commands(self, ctx, formatter):
        """Format commands with their aliases."""
        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None:
                continue
            if cmd.hidden:
                continue
            
            # Show aliases if they exist
            if hasattr(cmd, 'aliases') and cmd.aliases:
                aliases = ', '.join(cmd.aliases)
                commands.append((f"{subcommand}, {aliases}", cmd.get_short_help_str(limit=50)))
            else:
                commands.append((subcommand, cmd.get_short_help_str(limit=60)))
        
        if commands:
            with formatter.section('Commands'):
                formatter.write_dl(commands)


@click.group(cls=AliasedGroup, invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version')
@config_option
@debug_option
@click.option(
    '--quiet', '-q', '--yes', '-y',
    is_flag=True,
    help='Quiet mode: skip prompts and use defaults (also via QUIP_QUIET env var; CLI flag overrides env, which overrides config)'
)
@click.pass_context
def cli(ctx, version, config, debug, quiet):
    """QUIP - Quick Universal Integration Packager
    
    A tool for creating and managing Universal Controller integrations.
    """
    # Ensure context exists
    ctx.ensure_object(dict)
    
    # Store options in context
    ctx.obj['config'] = config
    ctx.obj['debug'] = debug
    final_quiet = resolve_quiet_mode(quiet, config)
    ctx.obj['quiet'] = final_quiet
    set_quiet_mode(final_quiet)
    
    # Set logging level
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    if version:
        click.echo(f'quip {__version__}-BETA')
        ctx.exit()
    
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command('new')
@click.argument('name')
@template_option
@click.pass_context
def new_project(ctx, name, template):
    """Create new integration project."""
    from quip.quip import run_command
    run_command('new', name, ctx.obj['config'], ctx.obj['debug'], template=template)


@cli.command('update')
@click.argument('name', required=False)
@click.option('--uuid', '-u', is_flag=True, help='Update UUID of the template')
@click.option('--new-uuid', '-n', is_flag=True, help='Update only new_uuid with a valid UUID')
@template_option
@click.option('--rename-scripts', is_flag=True, help='Add .py extensions to script files')
@click.pass_context
def update_project(ctx, name, uuid, new_uuid, template, rename_scripts):
    """Update existing integration. Aliases: u, up"""
    from quip.quip import run_command
    run_command('update', name, ctx.obj['config'], ctx.obj['debug'],
                template=template, uuid=uuid, new_uuid=new_uuid, 
                rename_scripts=rename_scripts)


@cli.command('fields')
@click.argument('name', required=False)
@click.option('--update', '-u', is_flag=True, help='Update fields from fields.yml')
@click.option('--dump', '-d', is_flag=True, help='Dump fields to fields.yml')
@click.option('--code', is_flag=True, help='Give some code samples')
@click.option('--common', is_flag=True, help='Give code samples in ue-common format')
@click.pass_context
def fields_command(ctx, name, update, dump, code, common):
    """Update or dump template.json fields. Aliases: f, fi"""
    from quip.quip import run_command
    run_command('fields', name, ctx.obj['config'], ctx.obj['debug'],
                update=update, dump=dump, code=code, common=common)

fields_command.aliases = ['f']


@cli.command('delete')
@click.argument('name')
@click.pass_context
def delete_project(ctx, name):
    """Delete the integration folder. Aliases: d, del"""
    from quip.quip import run_command
    run_command('delete', name, ctx.obj['config'], ctx.obj['debug'])

delete_project.aliases = ['d', 'del']


@cli.command('clone')
@click.argument('name')
@click.argument('source')
@template_option
@click.pass_context
def clone_project(ctx, name, source, template):
    """Clone existing integration with a new name. Aliases: c, cl, copy"""
    from quip.quip import run_command
    run_command('clone', name, ctx.obj['config'], ctx.obj['debug'],
                source=source, template=template)

clone_project.aliases = ['copy']


@cli.command('bootstrap')
@click.argument('name', required=False)
@template_option
@click.option('--baseline', '-b', help='Path of the baseline project')
@click.pass_context
def bootstrap_project(ctx, name, template, baseline):
    """Bootstrap new integration from baseline project. Aliases: bs, boot, bst, baseline"""
    from quip.quip import run_command
    run_command('bootstrap', name, ctx.obj['config'], ctx.obj['debug'],
                template=template, baseline=baseline)

bootstrap_project.aliases = ['bs', 'baseline']


@cli.command('upload')
@click.argument('name', required=False)
@template_option
@click.pass_context
def upload_project(ctx, name, template):
    """Upload template to Universal Controller (Template Only). Aliases: push"""
    from quip.quip import run_command
    run_command('upload', name, ctx.obj['config'], ctx.obj['debug'], template=template)

upload_project.aliases = ['push']


@cli.command('download')
@click.argument('name', required=False)
@template_option
@click.pass_context
def download_project(ctx, name, template):
    """Download template from Universal Controller. Aliases: pull"""
    from quip.quip import run_command
    run_command('download', name, ctx.obj['config'], ctx.obj['debug'], template=template)

download_project.aliases = ['pull']


@cli.command('build')
@click.argument('name', required=False)
@template_option
@click.pass_context
def build_project(ctx, name, template):
    """Build a zip file to import to Universal Controller (Template Only). Aliases: b, dist, zip"""
    from quip.quip import run_command
    run_command('build', name, ctx.obj['config'], ctx.obj['debug'], template=template)

build_project.aliases = ['dist', 'zip']


@cli.command('icon')
@click.argument('name', required=False)
@click.option(
    '--generate', '-g', metavar='TEXT',
    help='Generate a new icon from TEXT (max 3 letters). If omitted, uses auto-generated initials.'
)
@click.pass_context
def icon_command(ctx, name, generate):
    """Resize images to 48x48 in src/templates/. Aliases: resize-icon, ri, resize"""
    # Validate TEXT length if provided
    if generate is not None:
        txt = str(generate).strip()
        if len(txt) == 0:
            generate = True  # treat as flag without text
        else:
            if len(txt) > 3:
                raise click.BadParameter('TEXT must be at most 3 characters for -g/--generate')
            generate = txt
    from quip.quip import run_command
    run_command('icon', name, ctx.obj['config'], ctx.obj['debug'], generate=generate)


@cli.command('clean')
@click.argument('name', required=False)
@click.option('--macfilesonly', '-m', is_flag=True, 
              help='Delete only MacOS hidden files like ._* or .DS_Store')
@click.pass_context
def clean_project(ctx, name, macfilesonly):
    """Clear the dist folders. Aliases: clear"""
    from quip.quip import run_command
    run_command('clean', name, ctx.obj['config'], ctx.obj['debug'], 
                macfilesonly=macfilesonly)

clean_project.aliases = ['clear']


@cli.command('setup')
@click.argument('name', required=False)
@click.pass_context
def setup_command(ctx, name):
    """Setup External Systems."""
    from quip.quip import run_command
    run_command('setup', name, ctx.obj['config'], ctx.obj['debug'])


@cli.command('launch')
@click.argument('task_name')
@click.pass_context
def launch_task(ctx, task_name):
    """Launch Task."""
    from quip.quip import run_command
    run_command('launch', task_name, ctx.obj['config'], ctx.obj['debug'])


@cli.command('version')
@click.argument('version_method', 
                type=click.Choice(['minor', 'major', 'release', 'beta', 'rc']),
                required=False)
@click.option('--force', 'forced_version', help='Force to change the version in all files')
@click.pass_context
def version_command(ctx, version_method, forced_version):
    """Show or update the version of the template/extension."""
    from quip.quip import run_command
    run_command('version', None, ctx.obj['config'], ctx.obj['debug'],
                version_method=version_method, forced_version=forced_version)


@cli.command('config')
@click.pass_context
def config_command(ctx):
    """Show the configuration."""
    from quip.quip import run_command
    run_command('config', None, ctx.obj['config'], ctx.obj['debug'])


@cli.command('generate')
@click.argument('spec')
@click.option('--baseline', '-b', help='Override baseline path. Defaults to config defaults.bootstrap.source')
@click.option('--dry-run', '-d', is_flag=True, help='Parse and print YAML output without creating project')
@click.pass_context
def generate_command(ctx, spec, baseline, dry_run):
    """Generate a new extension from SPEC (.yml/.yaml or .qsa). Baseline comes from config unless overridden with -b/--baseline. Aliases: gen, g"""
    from quip.quip import run_command
    # Name will be resolved from YAML inside argparse path; we pass None here
    run_command('generate', None, ctx.obj['config'], ctx.obj['debug'], spec=spec, baseline=baseline, dry_run=dry_run)

generate_command.aliases = ['gen', 'g']


def main():
    """Main entry point."""
    try:
        cli(obj={})
    except Exception as e:
        cprint(f"Error: {e}", "red")
        sys.exit(1)


if __name__ == '__main__':
    main()

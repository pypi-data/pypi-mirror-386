import click

from apkg import adistro
from apkg.cli import cli
from apkg.pkgstyle import call_pkgstyle_fun, get_pkgstyle_for_distro
from apkg.commands.get_archive import parse_archive_args
from apkg.util import common
from apkg.log import getLogger
from apkg.project import Project


log = getLogger(__name__)


@cli.command(name="test-dep", aliases=['testdep'])
@click.argument('inputs', nargs=-1)
@click.option('-l', '--list', 'list', is_flag=True,
              help="list test deps only, don't install")
@click.option('-u', '--upstream', is_flag=True,
              help="use upstream archive")
@click.option('-a', '--archive', is_flag=True,
              help="use test deps from archive")
@click.option('-d', '--distro',
              help="override target distro  [default: current]")
@click.option('-F', '--in-file', 'in_files', multiple=True,
              help="specify input file, '-' to read from stdin")
@click.option('--ask/--no-ask', 'interactive',
              default=False, show_default=True,
              help="enable/disable interactive mode")
@click.help_option('-h', '--help',
                   help="show this help message")
def cli_test_dep(*args, **kwargs):
    """
    install or list testing dependencies
    """
    kwargs['install'] = not kwargs.pop('list')
    deps = test_dep(*args, **kwargs)
    if not kwargs['install']:
        common.print_results(deps)


def test_dep(
        upstream=False,
        archive=False,
        inputs=None,
        in_files=None,
        install=True,
        distro=None,
        interactive=False,
        project=None):
    """
    parse and optionally install testing dependencies

    pass install=False to only get list of deps without install

    returns list of test deps
    """
    action = 'installing' if install else 'listing'
    log.bold('%s testing deps', action)

    proj = project or Project()
    distro = adistro.distro_arg(distro, proj)
    log.info("target distro: %s", distro)

    inputs = common.parse_inputs(inputs, in_files)
    archive, _ = parse_archive_args(
        proj, archive, upstream, inputs)

    tests = proj.get_tests_for_distro(distro)
    deps = tests.deps

    if install:
        n_deps = len(deps)
        if n_deps > 0:
            log.info("installing %s test deps...", n_deps)
            pkgstyle = get_pkgstyle_for_distro(distro)
            call_pkgstyle_fun(
                pkgstyle, 'install_build_deps',
                deps,
                distro=distro,
                interactive=interactive)
        else:
            log.info("no build deps to install")

    return deps


APKG_CLI_COMMANDS = [cli_test_dep]

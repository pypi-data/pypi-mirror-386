import click

from apkg import adistro
from apkg.commands.build import build
from apkg.commands.srcpkg import srcpkg as make_srcpkg
from apkg.commands.system_setup import system_setup
from apkg import ex
from apkg.log import getLogger
from apkg import pkgstyle
from apkg.util import common


log = getLogger(__name__)


@click.command(name="lint")
@click.argument('inputs', nargs=-1)
@click.option('-p', '--pedantic', is_flag=True,
              help="enable extra / all warnings and infos")
@click.option('-i', '--info', is_flag=True,
              help="give detailed info about warnings")
@click.option('-s', '--strict', is_flag=True,
              help="treat all messages as errors")
@click.option('-d', '--distro',
              help="override target distro  [default: current]")
@click.option('-L', '--lint-dep', is_flag=True,
              help="install linting dependencies on host"
                   " (apkg system-setup --lint)")
@click.option('--cache/--no-cache', default=True, show_default=True,
              help="enable/disable cache")
@click.option('-F', '--in-file', 'in_files', multiple=True,
              help="specify input file, '-' to read from stdin")
@click.help_option('-h', '--help',
                   help="show this help message")
def cli_lint(*args, **kwargs):
    """
    run native distro linter on packages

    Default: build packages from source and lint them

    You can supply files to lint as arguments or use --in-file.

    Use --pedantic to run extra / all checks.

    Use --info to get details explanations about individual messages.

    Use --strict to treat all messages as errors (useful for pedantic CI).

    To install linter packages on host system use --lint-dep which calls

        apkg system-setup --lint

    before linting.
    """
    r = lint(*args, **kwargs)
    if r != 0:
        raise ex.LintingFailed(
            fail=f"linter returned error code {r}")
    else:
        log.success("linting successful")
    return r


def lint(
        inputs=None,
        in_files=None,
        pedantic=False,
        info=False,
        strict=False,
        distro=None,
        lint_dep=False,
        cache=True):
    """
    run native distro linter on packages
    """
    log.bold("linting packages")

    distro = adistro.distro_arg(distro)
    log.info("target distro: %s", distro)

    ps = pkgstyle.get_pkgstyle_for_distro(distro)
    if not ps:
        raise ex.DistroNotSupported(distro=distro)
    log.info("target pkgstyle: %s", ps.name)

    if lint_dep:
        system_setup(lint=True)

    inputs = common.parse_inputs(inputs, in_files)

    if not inputs:
        # default: use srcpkg and build to get packages to lint
        inputs = make_srcpkg(
            distro=distro,
            cache=cache)
        inputs += build(
            distro=distro,
            cache=cache)

    try:
        result = pkgstyle.call_pkgstyle_fun(
            ps, 'lint',
            inputs,
            pedantic=pedantic,
            info=info,
            strict=strict,
            distro=distro)
    except ex.CommandNotFound as e:
        msg = str(e) + ("\n\nInstall lint deps:\n\n"
                        "    apkg system-setup --lint\n\n"
                        "or:\n\n"
                        "    apkg lint --lint-dep")
        raise ex.CommandNotFound(msg=msg)

    return result


APKG_CLI_COMMANDS = [cli_lint]

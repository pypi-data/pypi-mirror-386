from pathlib import Path
import shutil

import click

from apkg import adistro
from apkg.cache import file_checksum, path_checksum
from apkg import ex
from apkg.commands.build_dep import build_dep as cmd_build_dep
from apkg.commands.srcpkg import srcpkg as make_srcpkg
from apkg.log import getLogger
from apkg.project import Project
from apkg.util import common


log = getLogger(__name__)


@click.command(name="build")
@click.argument('inputs', nargs=-1)
@click.option('-s', '--srcpkg', is_flag=True,
              help="use source package")
@click.option('-a', '--archive', is_flag=True,
              help="use template (/build srcpkg) from archive")
@click.option('-u', '--upstream', is_flag=True,
              help="use upstream template / archive / srcpkg")
@click.option('-v', '--version',
              help=("upstream archive version to use"
                    ", implies --upstream"
                    ", exclusive with --srcpkg and --archive"))
@click.option('-r', '--release',
              help="set packagge release  [default: 1]")
@click.option('-d', '--distro',
              help="override target distro  [default: current]")
@click.option('-b', '--build-dep', is_flag=True,
              help="install build dependencies on host (apkg build-dep)")
@click.option('-O', '--result-dir',
              help=("put results into specified dir"
                    "  [default: pkg/srcpkg/DISTRO/NVR]"))
@click.option('--cache/--no-cache', default=True, show_default=True,
              help="enable/disable cache")
@click.option('-F', '--in-file', 'in_files', multiple=True,
              help="specify input file, '-' to read from stdin")
@click.option('-I', '--isolated', is_flag=True,
              help="use isolated builder (pbuilder, mock, ...)")
@click.option('-i', '--install-dep', 'build_dep', is_flag=True,
              help="[DEPRECATED] compat alias for --build-dep")
@click.help_option('-h', '--help',
                   help="show this help message")
def cli_build(*args, **kwargs):
    """
    build packages
    """
    results = build(*args, **kwargs)
    common.print_results(results)
    return results


def build(
        srcpkg=False,
        archive=False,
        upstream=False,
        inputs=None,
        in_files=None,
        version=None,
        release=None,
        distro=None,
        result_dir=None,
        build_dep=False,
        isolated=False,
        cache=True,
        project=None):
    """
    build packages
    """
    log.bold('building packages')

    proj = project or Project()
    distro = adistro.distro_arg(distro, proj)
    log.info("target distro: %s", distro)
    use_cache = proj.cache.enabled(
        'local', cmd='build', use_cache=cache)

    inputs = common.parse_inputs(inputs, in_files)

    if build_dep:
        if isolated:
            # doesn't make sense in isolated build
            log.warning("ignoring build-dep request in isolated build")
        else:
            # install build deps if requested
            try:
                cmd_build_dep(
                    srcpkg=srcpkg,
                    archive=archive,
                    upstream=upstream,
                    inputs=inputs,
                    distro=distro,
                    project=proj)
            except ex.DistroNotSupported as e:
                log.warning("SKIPPING build-dep due to error: %s", e)

    if srcpkg:
        if version:
            raise ex.InvalidInput(
                fail="--srcpkg and --version options are mutually exclusive")
    else:
        # make source package
        inputs = make_srcpkg(
            archive=archive,
            inputs=inputs,
            upstream=upstream,
            version=version,
            release=release,
            distro=distro,
            project=proj,
            cache=cache)

    common.ensure_inputs(inputs)
    srcpkg_path = inputs[0]
    if srcpkg:
        log.info("using existing source package: %s", srcpkg_path)

    # fetch pkgstyle (deb, rpm, arch, ...)
    template = proj.get_template_for_distro(distro)
    pkgstyle = template.pkgstyle

    # get needed paths
    nvr = pkgstyle.get_srcpkg_nvr(srcpkg_path)
    build_path = proj.path.package_build / distro.idver / nvr
    if result_dir:
        result_path = Path(result_dir)
    else:
        result_path = proj.path.package_out / distro.idver / nvr

    # check cache
    if use_cache:
        cache_key = 'pkg/%s/%s/' % (distro.idver, nvr)
        cache_key += '%s:%s' % (
            path_checksum(*inputs), file_checksum(*inputs))
        cached = common.get_cached_paths(proj, cache_key, result_dir)
        if cached:
            log.success("reuse %d cached packages", len(cached))
            return cached

    log.info("source package NVR: %s", nvr)
    log.info("build dir: %s", build_path)
    log.info("result dir: %s", result_path)
    # ensure build build doesn't exist
    if build_path.exists():
        log.info("removing existing build dir: %s", build_path)
        shutil.rmtree(build_path)
    # ensure result dir doesn't exist unless specified
    if not result_dir and result_path.exists():
        log.info("removing existing result dir: %s", result_path)
        shutil.rmtree(result_path)

    # build package using chosen distro packaging style
    pkgs = pkgstyle.build_packages(
        build_path,
        result_path,
        srcpkg_paths=inputs,
        isolated=isolated)

    if not pkgs:
        msg = ("package build reported success but there are "
               "no packages:\n\n%s" % result_path)
        raise ex.UnexpectedCommandOutput(msg=msg)
    log.success("built %s packages in: %s", len(pkgs), result_path)

    # sort output for determinism
    pkgs.sort()

    if use_cache and not upstream:
        unfiles = [p for p in pkgs if not p.is_file()]
        if not unfiles:
            # only cache regular files for now
            proj.cache.update(cache_key, pkgs)

    return pkgs


APKG_CLI_COMMANDS = [cli_build]

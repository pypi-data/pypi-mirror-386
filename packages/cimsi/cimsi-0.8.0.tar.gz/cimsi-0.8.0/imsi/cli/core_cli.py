
import click
from functools import wraps
import os
from pathlib import Path
import sys
import warnings


class CommandWithPassthroughEOO(click.Command):
    def format_usage(self, ctx, formatter):
        formatter.write_usage(ctx.command.name, "[OPTIONS] -- [PASSTHROUGH_ARGS]")


def passthrough_eoo_delimiter(ctx, param, value):
    # enforce requirement that end of options delimiter '--'
    # is entered before trailing args
    if value:
        try:
            delim_index = sys.argv.index('--')
            first_arg_index = sys.argv.index(value[0])
            if delim_index > first_arg_index:
                raise click.UsageError("Use '--' before passthrough arguments.")
        except ValueError:
            raise click.UsageError("Use '--' before the trailing arguments.")
    return value


def force_dirs(
    path: Path = Path("src"),
):
    user_in_path = path.exists()
    wrk_dir_env_set = os.getenv("WRK_DIR") is not None

    if user_in_path and wrk_dir_env_set and Path.cwd().resolve() == Path(os.getenv("WRK_DIR")).resolve():
        return

    if wrk_dir_env_set and user_in_path:
        warnings.warn(
            f"\n\n**WARNING**: Both WRK_DIR and {path} directory found. Defaulting to CWD {path} at {Path('.').resolve()}\n"
        )
        return

    if wrk_dir_env_set and not Path(os.getenv("WRK_DIR"), path).exists():
        raise ValueError(
            f"⚠️  $WRK_DIR = {os.getenv('WRK_DIR')} is not a valid imsi directory. Please check the path and try again."
        )

    if not any([user_in_path, wrk_dir_env_set]):
        raise ValueError(
            f"⚠️  {path} directory not found! Possibly because:\n"
            "1. You are not currently in your setup directory or one hasn't been created.\n"
            "    or \n"
            "2. The environment variable WRK_DIR is not set to the correct directory."
        )


def log_cli(func=None, logger_name='cli'):
    from imsi.utils.git_tools import is_repo_clean, git_add_commit
    import imsi.cli.core_tracking as ct

    # decorator for logging imsi cli click commands
    def decorator_func(func):
        # the actual decorator
        @wraps(func)
        def wrapper_func(*args, **kwargs):
            # the actual function being wrapped

            track = True

            # hack - required to make sure that:
            #  - this logging isn't possible for all imsi functions (eg setup)
            #  - logs aren't written to files when imsi cli commands are invoked
            #    from the wrong location
            force_dirs()     # success -> pwd == work dir
            path = Path.cwd()

            if args:
                if isinstance(args[0], click.core.Context):
                    # get the cli func name from the context rather than
                    # func.__name__ (because of how click invokes func names)
                    ctx = args[0]
                    func_name = ctx.info_name
            else:
                # FIXME TODO fallback
                func_name = func.__name__

            # init log
            imsi_logger = ct.get_imsi_logger(logger_name, path)
            ct.imsi_log_prelude(func_name, imsi_logger)

            if track:
                config_dir = path / 'config'
                ct.imsi_state_snapshot(path, logger=imsi_logger)

                # force a clean repo for /config
                if logger_name == 'cli':
                    clean_config, _ = is_repo_clean(config_dir)
                    if not clean_config:
                        # always force the config dir to be clean
                        msg = f"IMSI pre-run commit cli:{func_name}"
                        git_add_commit(msg=msg, path=config_dir)
                        imsi_logger.info(msg)

            # invoke the wrapped function
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                imsi_logger.error(f'ERROR {func_name} {type(e).__name__}')
                raise e
            ct.imsi_log_postlude(func_name, imsi_logger)
            return result
        return wrapper_func
    if func:
        # hack to handle decorator without kwargs (style)
        return decorator_func(func)
    return decorator_func


SETUP_EPILOG = """\b
More information:

    valid parameter values for --model, --exp, --machine, --seq, --flow,
    --postproc are composed within the repo's imsi-config Configuration Files.
"""
@click.command(
    short_help="Set up a run directory and obtain model source code.",
    epilog=SETUP_EPILOG
    )
@click.option(
    "--runid", type=str,
    default=None,
    required=True,
    help='A unique identifier (<20 char, alphanumeric incl. hyphen, mixed case)',
)
@click.option(
    "--repo",
    required=True,
    help="Git repository URL or file path.",
)
@click.option("--ver", type=str, default=None, help="Version of the code to clone (git only).")
@click.option("--exp", required=True, type=str, help="Experiment name.")
@click.option("--model", required=True, type=str, help="Model name.")
@click.option(
    "--fetch_method",
    default="clone", type=click.Choice(["clone", "clone-full", "link", "copy"]),
    help="Fetch method for source code.",
    show_default=True
)
@click.option("--seq", default=None, help='Sequencer to use, like "iss" or "maestro".')
@click.option("--machine", default=None, help="Machine to use.")
@click.option("--flow", default=None, help="Workflow to use.")
@click.option("--postproc", default=None, help="Postprocessing profile to use.")
@click.option("--no-src-storage", default=False, is_flag=True, help='Disables src_storage_dir if present in imsi-config')
@click.pass_context
def setup(ctx, **kwargs):
    """Create a run directory, obtain the model source code, and resolve the configuration files.

    https://imsi.readthedocs.io/en/latest/usage.html#setting-up-a-run
    """
    from imsi.user_interface.setup_manager import (
        setup_run,
        ValidatedSetupOptions,
        InvalidSetupConfig,
    )
    import imsi.cli.core_tracking as ct

    # separate the kwargs
    setup_run_params = ValidatedSetupOptions.model_fields.keys()
    setup_kwargs = {k: kwargs[k] for k in kwargs if k in setup_run_params}
    ctrl_kwargs = {k:kwargs[k] for k in kwargs if k not in setup_run_params}

    try:
        setup_args = ValidatedSetupOptions(**setup_kwargs)
    except InvalidSetupConfig as e:
        click.echo(e)
        raise e

    setup_run(setup_args, force=ctx.obj["FORCE"], **ctrl_kwargs)

    ct.log_setup(sys.argv, setup_args)


@click.command(
    short_help="Log the imsi state.",
    help="Log the imsi state to the .imsi-cli.log.",
    epilog="""\b
    Note:
        This is nominally an imsi utility function. In particular,
        model developers may use this in their run-time code.
    """)
@click.option('-m', '--msg', default=None, required=False,
              help='Message to include in the log.')
@click.option('-p', '--path', type=click.Path(exists=True), default='.',
              required=True,
              help='Path to run folder.')
def log_state(msg, path):
    import imsi.cli.core_tracking as ct

    path = Path(path).resolve()
    logger = ct.get_imsi_logger('runtime', path)
    ct.imsi_log_prelude('log-state', logger)
    ct.imsi_state_snapshot(path, logger=logger)
    if msg is not None:
        logger.info(f'MESSAGE: {msg}')
    ct.imsi_log_postlude('log-state', logger)


@click.command(
    short_help="Apply configuration from the resolved configuration file.",
    help="Apply configuration from the resolved configuration file."
)
@click.pass_context
@log_cli
def config(ctx):
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    uim.update_config_from_state(force=ctx.obj["FORCE"])


@click.command(
    short_help="Reload the imsi Configuration Files from the on-disk repo.",
    help="""Reload the imsi Configuration Files from the on-disk repo
    and update the run configuration.
    """
)
@click.pass_context
@log_cli
def reload(ctx):
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    uim.reload_config_from_source(force=ctx.obj["FORCE"])


@click.command(
    short_help="Set (apply) the configuration from selectors.",
    help="Set (apply) the configuration from selectors.",
    )
@click.option(
    "-s",
    "--selections",
    metavar="SETUP_PARAM=VALUE",
    multiple=True,
    help="""A key-value pair for a setup parameter and it's value.
    [Example: exp=exp_y]"""
)
@click.option(
    "-o",
    "--options",
    metavar="OPTION_BLOCK=VALUE",
    multiple=True,
    help="""A key-value pair for an option block and it's value, as
    stored in the *_options.yaml files of the imsi Configuration Files.
    [Example: block_a=option_1]""",
)
@click.pass_context
@log_cli
def set(ctx, selections, options):
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    if any([selections, options]):
        # tmp disabling parm_file -> None
        uim.set_selections(None, selections, options, force=ctx.obj["FORCE"])
    else:
        click.echo(
            "Error: Must provide at least one --selections or --options",
            err=True,
        )


@click.command(
    cls=CommandWithPassthroughEOO,
    context_settings=dict(ignore_unknown_options=True,),
    short_help="Compile model components.",
    help="Compile model components.",
    epilog="The script 'imsi-tmp-compile.sh' will be executed."
)
@click.option("--script-help", is_flag=True, help="Display the help message of the script.")
@click.argument("args", nargs=-1, callback=passthrough_eoo_delimiter)
@click.pass_context
@log_cli
def build(ctx, script_help, args):
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    args = ['-h'] if script_help else args
    click.echo("IMSI Build")
    uim.compile_model_execs(args, force=ctx.obj['FORCE'])


@click.command(help="Submit the simulation to the sequencer.")
@log_cli
def submit():
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    uim.submit_run()


@click.command(
    cls=CommandWithPassthroughEOO,
    context_settings=dict(ignore_unknown_options=True,),
    short_help="Save model restart files.",
    help="Save model restart files.",
    epilog="The script 'save_restart_files.sh' will be executed."
)
@click.option("--script-help", is_flag=True, help="Display the help message of the script.")
@click.argument("args", nargs=-1, callback=passthrough_eoo_delimiter)
@log_cli
def save_restarts(script_help, args):
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    args = ['-h'] if script_help else args
    uim.save_restarts(args)

@click.command(
    cls=CommandWithPassthroughEOO,
    context_settings=dict(ignore_unknown_options=True,),
    short_help="Retrieve the model restart files from tape",
    help="Retrieve the model restart files from long-term storage (tape)",
    epilog="The script 'tapeload_rs.sh' will be executed."
)
@click.option("--script-help", is_flag=True, help="Display the help message of the script.")
@click.argument("args", nargs=-1, callback=passthrough_eoo_delimiter)
@log_cli
def tapeload_rs(script_help, args):
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    args = ['-h'] if script_help else args
    click.echo("IMSI tapeload rs")
    uim.tapeload_rs(args)

@click.command(help="Get sequencer status information.")
def status():
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    uim.get_sequencer_status()

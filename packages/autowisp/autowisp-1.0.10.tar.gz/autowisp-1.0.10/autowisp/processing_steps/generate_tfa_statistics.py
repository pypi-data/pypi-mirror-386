#!/usr/bin/env python3

"""Generate a statistics file showing the performance after TFA."""

from functools import partial

from autowisp.multiprocessing_util import setup_process
from autowisp.file_utilities import find_lc_fnames
from autowisp.processing_steps.lc_detrending_argument_parser import (
    LCDetrendingArgumentParser,
)
from autowisp.processing_steps.lc_detrending import (
    calculate_detrending_performance,
)
from autowisp.processing_steps.manual_util import ignore_progress


def parse_command_line(*args):
    """Parse the commandline optinos to a dictionary."""

    return LCDetrendingArgumentParser(
        mode="TFAstat",
        description=__doc__,
        add_reconstructive=False,
        input_type=("" if args else "lc"),
    ).parse_args(*args)


generate_tfa_statistics = partial(
    calculate_detrending_performance, detrending_mode="tfa"
)


def main():
    """Run the step from the command line."""

    cmdline_config = parse_command_line()
    setup_process(
        project_home=cmdline_config["project_home"], task="main", **cmdline_config
    )

    generate_tfa_statistics(
        find_lc_fnames(cmdline_config.pop("lc_files")),
        0,
        cmdline_config,
        ignore_progress,
    )


if __name__ == "__main__":
    main()

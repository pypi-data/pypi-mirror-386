#!/usr/bin/env python3
#     The Certora Prover
#     Copyright (C) 2025  Certora Ltd.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.


import sys
import logging
from typing import List, Optional, Dict
from pathlib import Path

scripts_dir_path = Path(__file__).parent.resolve()  # containing directory
sys.path.insert(0, str(scripts_dir_path))


import CertoraProver.certoraApp as App
from CertoraProver.certoraBuildRust import build_rust_project
from Shared.proverCommon import (
    build_context,
    collect_and_dump_metadata,
    collect_and_dump_config_layout,
    ensure_version_compatibility,
    run_local,
    run_remote,
    CertoraRunResult,
    handle_exit,
    catch_exits,
)

# logger for issues regarding the general run flow.
# Also serves as the default logger for errors originating from unexpected places.
run_logger = logging.getLogger("run")


def run_solana_prover(args: List[str]) -> Optional[CertoraRunResult]:
    """
    The main function that is responsible for the general flow of the script.
    The general flow is:
    1. Parse program arguments
    2. Run the necessary steps (build/ cloud verification/ local verification)
    """
    context, logging_manager = build_context(args, App.SolanaApp)

    timings: Dict[str, float] = {}
    exit_code = 0  # The exit code of the script. 0 means success, any other number is an error.
    return_value = None

    # Collect and validate metadata
    collect_and_dump_metadata(context)
    collect_and_dump_config_layout(context)

    # Version validation
    ensure_version_compatibility(context)

    # Build Solana - If input file is .so or .o file, we skip building part
    build_rust_project(context, timings)

    if context.build_only:
        return return_value

    if context.local:
        additional_commands = []
        if context.solana_summaries:
            additional_commands += ["-solanaSummaries", ",".join(context.solana_summaries)]
        if context.solana_inlining:
            additional_commands += ["-solanaInlining", ",".join(context.solana_inlining)]
        # Run local verification
        exit_code = run_local(context, timings, additional_commands)
    else:
        logging_manager.remove_debug_logger()
        exit_code, return_value = run_remote(context, args, timings)

    # Handle exit codes and return
    return handle_exit(exit_code, return_value)


@catch_exits
def entry_point() -> None:
    """
    This function is the entry point of the certora_cli customer-facing package, as well as this script.
    It is important this function gets no arguments!
    """
    run_solana_prover(sys.argv[1:])


if __name__ == '__main__':
    entry_point()

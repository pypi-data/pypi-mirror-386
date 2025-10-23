# BSD 3-Clause License
#
# Copyright (c) 2025, Jean-Pierre Morard, THALES SIX GTS France SAS
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
# 3. Neither the name of Jean-Pierre Morard nor the names of its contributors, or THALES SIX GTS France SAS, may be used to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import sys
from pathlib import Path
import py7zr

from agi_env import AgiEnv


def _usage() -> None:
    print("Usage: python post_install.py <app> [destination]")


def _build_env(app_arg: Path) -> AgiEnv:
    """Instantiate :class:`AgiEnv` for the given app path.

    install_type is deprecated; heuristics inside AgiEnv determine flags
    like is_worker_env and is_source_env based on the provided paths.
    """

    return AgiEnv(apps_dir=app_arg.parent, active_app=app_arg.name)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) not in (1, 2):
        _usage()
        return 1
    if args[0][0]  != "/":
        app_arg = Path.home() / "wenv" / args[0]
    else:
        app_arg = Path(args[0]).expanduser()

    dest_arg = args[1] if len(args) == 2 else None

    env = _build_env(app_arg)
    archive = app_arg / "src" / app_arg.name.replace("project", "worker") / "dataset.7z"
    print("archive:", archive)

    if not archive.exists():
        print(
            f"[post_install] dataset archive not found at {archive}. "
            "Skipping extraction."
        )
        return 0

    print("destination", dest_arg)
    env.unzip_data(archive, dest_arg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

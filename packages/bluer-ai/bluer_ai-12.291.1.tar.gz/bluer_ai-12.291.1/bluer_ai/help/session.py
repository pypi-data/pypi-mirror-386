from typing import List

from bluer_options.terminal import show_usage, xtra


def help_start(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("plugin=<plugin-name>,~pull", mono=mono)

    return show_usage(
        [
            "@session",
            "start",
            f"[{options}]",
        ],
        "start a session.",
        mono=mono,
    )


help_functions = {
    "start": help_start,
}

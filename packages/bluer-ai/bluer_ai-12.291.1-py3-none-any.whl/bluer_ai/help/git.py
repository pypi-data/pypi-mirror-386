from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_ai.help.pypi import build_options as pypi_build_options


def help(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@git",
            "<repo_name>",
            "<command-line>",
        ],
        "run '@git <command-line>' in <repo_name>.",
        mono=mono,
    )


def help_browse(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "actions"

    return show_usage(
        [
            "@git",
            "browse",
            "[ . | - | <repo-name> ]",
            f"[{options}]",
        ],
        "browse <repo-name>.",
        mono=mono,
    )


def help_checkout(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("~fetch,~pull,", mono=mono),
            "rebuild",
        ]
    )

    return show_usage(
        [
            "@git",
            "checkout",
            "<branch-name>",
            f"[{options}]",
        ],
        "git checkout <branch-name>.",
        mono=mono,
    )


def help_clone(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("cd,~from_template,if_cloned,", mono=mono),
            "install",
            xtra(",object,pull,source=<username/repo_name>", mono=mono),
        ]
    )

    return show_usage(
        [
            "@git",
            "clone",
            "<repo-name>",
            f"[{options}]",
        ],
        "clone <repo-name>.",
        mono=mono,
    )


def help_create_branch(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~increment_version,offline,~push,~timestamp", mono=mono)

    return show_usage(
        [
            "@git",
            "create_branch",
            "<branch-name>",
            f"[{options}]",
        ],
        "create <branch-name> in the repo.",
        mono=mono,
    )


def help_create_pull_request(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@git",
            "create_pull_request",
        ],
        "create a pull request in the repo.",
        mono=mono,
    )


def help_get_branch(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@git",
            "get_branch",
        ],
        "get git branch name.",
        mono=mono,
    )


def help_get_repo_name(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@git",
            "get_repo_name",
        ],
        "get repo name.",
        mono=mono,
    )


def help_increment_version(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "diff"

    args = [
        "[--verbose 1]",
    ]

    return show_usage(
        [
            "@git",
            "++ | increment | increment_version",
            f"[{options}]",
        ]
        + args,
        "increment repo version.",
        mono=mono,
    )


def help_pull(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("~all,", mono=mono),
            "init",
        ]
    )

    return show_usage(
        [
            "@git",
            "pull",
            f"[{options}]",
        ],
        "pull.",
        mono=mono,
    )


def push_options(
    mono: bool,
    uses_actions: bool = True,
    uses_pull_request: bool = True,
    uses_workflows: bool = True,
) -> str:
    return "".join(
        (
            [
                xtra("~action,", mono=mono),
            ]
            if uses_actions
            else []
        )
        + [
            "browse",
        ]
        + (
            [
                xtra(",~create_pull_request,", mono=mono),
                "first",
            ]
            if uses_pull_request
            else []
        )
        + [
            xtra(",~increment_version,offline,~status", mono=mono),
        ]
        + (
            [
                ",~workflow",
            ]
            if uses_workflows
            else []
        )
    )


def help_push(
    tokens: List[str],
    mono: bool,
) -> str:
    options = push_options(mono=mono)

    build_options = f"build,{pypi_build_options}"

    return show_usage(
        [
            "@git",
            "push",
            "<message>",
            f"[{options}]",
            f"[{build_options}]",
        ],
        "push to the repo.",
        mono=mono,
    )


def help_recreate_ssh(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@git",
            "recreate_ssh",
        ],
        "recreate github ssh key.",
        mono=mono,
    )


def help_reset(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@git",
            "reset",
        ],
        "reset to the latest commit of the current branch.",
        mono=mono,
    )


def help_review(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@git",
            "review",
        ],
        "review the repo.",
        mono=mono,
    )


def help_rm(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@git",
            "rm",
            "<repo_name>",
        ],
        "rm <repo-name>.",
        mono=mono,
    )


def help_seed(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("screen", mono=mono)

    return show_usage(
        [
            "@git",
            "seed",
            f"[{options}]",
        ],
        "seed 🌱  git.",
        mono=mono,
    )


def help_set_remote(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("dryrun,", mono=mono),
            "https|ssh",
        ]
    )

    return show_usage(
        [
            "@git",
            "set_remote",
            f"[{options}]",
        ],
        "set repo remote.",
        mono=mono,
    )


def help_status(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "~all"

    return show_usage(
        [
            "@git",
            "status",
            f"[{options}]",
        ],
        "show git status.",
        mono=mono,
    )


def help_sync_fork(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@git",
            "sync_fork",
            "<branch-name>",
        ],
        "sync fork w/ upstream.",
        mono=mono,
    )


help_functions = {
    "": help,
    "browse": help_browse,
    "checkout": help_checkout,
    "clone": help_clone,
    "create_branch": help_create_branch,
    "create_pull_request": help_create_pull_request,
    "get_branch": help_get_branch,
    "get_repo_name": help_get_repo_name,
    "increment_version": help_increment_version,
    "pull": help_pull,
    "push": help_push,
    "recreate_ssh": help_recreate_ssh,
    "reset": help_reset,
    "review": help_review,
    "rm": help_rm,
    "seed": help_seed,
    "set_remote": help_set_remote,
    "status": help_status,
    "sync_fork": help_sync_fork,
}

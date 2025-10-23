from typing import List

from bluer_options.terminal import show_usage, xtra


def help_browse(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~public", mono=mono)

    return show_usage(
        [
            "@docker",
            "browse",
            f"[{options}]",
        ],
        "browse docker-hub.",
        mono=mono,
    )


def help_build(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("dryrun,no_cache,~push,run,verbose", mono=mono)

    return show_usage(
        [
            "@docker",
            "build",
            f"[{options}]",
        ],
        "build the docker image.",
        mono=mono,
    )


def help_clear(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@docker",
            "clear",
        ],
        "clear docker.",
        mono=mono,
    )


def help_eval(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("cat,dryrun,verbose", mono=mono)

    return show_usage(
        [
            "@docker",
            "eval",
            f"[{options}]",
            "<command-line>",
        ],
        "run <command-line> through the docker image.",
        mono=mono,
    )


def help_push(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@docker",
            "push",
        ],
        "push the docker image.",
        mono=mono,
    )


def help_run(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("dryrun", mono=mono)

    return show_usage(
        [
            "@docker",
            "run",
            f"[{options}]",
        ],
        "run the docker image.",
        mono=mono,
    )


def help_seed(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@docker",
            "seed",
        ],
        "seed docker 🌱 .",
        mono=mono,
    )


help_functions = {
    "browse": help_browse,
    "build": help_build,
    "clear": help_clear,
    "eval": help_eval,
    "push": help_push,
    "run": help_run,
    "seed": help_seed,
}

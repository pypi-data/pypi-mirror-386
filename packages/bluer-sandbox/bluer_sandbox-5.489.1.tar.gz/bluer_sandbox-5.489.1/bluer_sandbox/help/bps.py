from typing import List

from bluer_options.terminal import show_usage, xtra


def help_beacon(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~start_bluetooth", mono=mono)

    args = [
        "[--x <1.0>]",
        "[--y <2.0>]",
        "[--z <3.0>]",
        "[--sigma <4.0>]",
        "[--spacing <2.0>]",
        "[--timeout <10.0 | -1>]",
    ]

    return show_usage(
        [
            "@bps",
            "beacon",
            f"[{options}]",
        ]
        + args,
        "start beacon.",
        mono=mono,
    )


def help_install(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@bps",
            "install",
        ],
        "install bps.",
        mono=mono,
    )


def help_introspect(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("~start_bluetooth,", mono=mono),
            "unique_bus_name=<1:234>",
        ]
    )

    return show_usage(
        [
            "@bps",
            "introspect",
            f"[{options}]",
        ],
        "introspect <1:234>.",
        mono=mono,
    )


def help_receiver(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~start_bluetooth", mono=mono)

    args = [
        "[--grep <sparrow>]",
        "[--timeout <10>]",
    ]

    usage_1 = show_usage(
        [
            "@bps",
            "receiver",
            f"[{options}]",
        ]
        + args,
        "start receiver.",
        mono=mono,
    )

    # ---
    options = xtra("~python,~start_bluetooth", mono=mono)

    usage_2 = show_usage(
        [
            "@bps",
            "receiver",
            f"[{options}]",
        ],
        "start receiver.",
        mono=mono,
    )

    return "\n".join(
        [
            usage_1,
            usage_2,
        ]
    )


def help_start_bluetooth(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@bps",
            "start_bluetooth",
        ],
        "start bluetooth.",
        mono=mono,
    )


def help_test(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~start_bluetooth", mono=mono)

    return show_usage(
        [
            "@bps",
            "test",
            f"[{options}]",
        ],
        "d-bus ping test.",
        mono=mono,
    )


help_functions = {
    "beacon": help_beacon,
    "install": help_install,
    "introspect": help_introspect,
    "receiver": help_receiver,
    "start_bluetooth": help_start_bluetooth,
    "test": help_test,
}

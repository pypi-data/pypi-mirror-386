from typing import List, Tuple

import numpy as np
import platform

from blueness import module
from bluer_options import host, string
from bluer_options.logger import crash_report
from bluer_options.env import BLUER_AI_WIFI_SSID

from bluer_ai import NAME, fullname
from bluer_ai.logger import logger

NAME = module.name(__file__, NAME)


def lxde(_):
    return terraform(
        ["/etc/xdg/lxsession/LXDE/autostart"],
        [
            [
                "@bash /home/pi/git/bluer-ai/bluer_ai/.abcli/bluer_ai.sh - bluer_ai session start"
            ]
        ],
    )


def poster(filename: str) -> bool:
    from bluer_objects.graphics.text import render_text
    from bluer_objects.graphics.frame import add_frame
    from bluer_objects.graphics import screen
    from bluer_objects import file

    logger.debug("{}.poster({})".format(NAME, filename))

    image = add_frame(
        np.concatenate(
            [
                render_text(
                    centered=True,
                    image_width=screen.get_size()[1],
                    text=line,
                    thickness=4,
                )
                for line in signature()
            ],
            axis=0,
        ),
        32,
    )

    return image if filename is None else file.save_image(filename, image)


def mac(user):
    return terraform(
        ["/Users/{}/.bash_profile".format(user)],
        [
            ["source ~/git/bluer-ai/bluer_ai/.abcli/bluer_ai.sh"],
        ],
    )


# https://forums.raspberrypi.com/viewtopic.php?t=294014
def rpi(
    _,
    is_headless: bool = False,
) -> bool:
    success = terraform(
        ["/home/pi/.bashrc"],
        [
            [
                "source /home/pi/git/bluer-ai/bluer_ai/.abcli/bluer_ai.sh{}".format(
                    "  if_not_ssh,~terraform bluer_ai session start"
                    if is_headless
                    else ""
                )
            ]
        ],
    )

    if not is_headless:
        if not terraform(
            ["/etc/xdg/lxsession/LXDE-pi/autostart"],
            [
                [
                    "@sudo -E bash /home/pi/git/bluer-ai/bluer_ai/.abcli/bluer_ai.sh ~terraform bluer_ai session start",
                ]
            ],
        ):
            success = False

    return success


def load_text_file(
    filename: str,
) -> Tuple[bool, List[str]]:
    try:
        with open(filename, "r") as fp:
            text = fp.read()
        text = text.split("\n")

        return True, text
    except:
        return False, []


def save_text_file_if_different(
    filename: str,
    text: List[str],
) -> bool:
    _, current_text = load_text_file(filename)
    if "|".join([line for line in current_text if line]) == "|".join(
        [line for line in text if line]
    ):
        return True

    try:
        with open(filename, "w") as fp:
            fp.writelines([string + "\n" for string in text])

        logger.info(f"updated {filename} ...")
        return True
    except Exception as e:
        crash_report(e)
        return False


def terraform(
    list_of_filenames: List[str],
    list_of_commands: List[List[str]],
) -> bool:
    success = True
    for filename, commands in zip(list_of_filenames, list_of_commands):
        success_, content = load_text_file(filename)
        if not success_:
            success = False
            continue

        content_updated = [
            string for string in content if ("bluer-ai" not in string) and string
        ] + commands

        if not save_text_file_if_different(
            filename,
            content_updated,
        ):
            success = False

    return success


def signature() -> List[str]:
    return [
        fullname(),
        host.get_name(),
        " | ".join(
            host.tensor_processing_signature()
            + [
                f"Python {platform.python_version()}",
                f"{platform.system()} {platform.release()}",
            ]
        ),
        " | ".join(
            [
                string.pretty_date(include_time=False),
                string.pretty_date(
                    include_date=False,
                    include_zone=True,
                ),
            ]
            + ([BLUER_AI_WIFI_SSID] if BLUER_AI_WIFI_SSID else [])
        ),
    ]


def ubuntu(user):
    return terraform(
        ["/home/{}/.bashrc".format(user)],
        [
            ["source /home/{}/git/bluer-ai/bluer_ai/.abcli/bluer_ai.sh".format(user)],
        ],
    )

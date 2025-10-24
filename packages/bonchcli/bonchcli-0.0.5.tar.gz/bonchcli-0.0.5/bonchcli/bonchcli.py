#!/usr/bin/env python

import asyncio
import argparse
from getpass import getpass

from bonchapi import BonchAPI
from bonchapi.bonchapi import AuthError

from .config_manager import cm, Config
from . import formatting


def input_auth_data():
    mail = input("Your mail> ")
    password = getpass("Your password> ")
    config = Config(mail, password)
    cm.write_config(config)


async def main():
    if not cm.is_config_exists():
        cm.create_config_file()
        if not cm.check_validity_config():
            input_auth_data()
        config = cm.read_config()
    else:
        config = cm.read_config()

    parser = argparse.ArgumentParser(
                        prog="bonchcli",
                        epilog="Example: bonchcli -3"
                        )

    parser.add_argument('week_offset', nargs="?", type=int, default=0,
                        help="a positive or negative number")
    args = parser.parse_args()

    api = BonchAPI()
    await api.login(config.mail, config.password)
    rsp = await api.get_timetable(week_offset=args.week_offset)
    
    formatting.render_timetable(rsp)


def sync_main():
    """This func need for build pipx applicaion as entry point"""

    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())

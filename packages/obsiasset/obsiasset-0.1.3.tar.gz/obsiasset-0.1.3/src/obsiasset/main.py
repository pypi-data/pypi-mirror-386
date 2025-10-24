#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: bxwill.shi@gmail.com


import sys
from obsiasset.cli.appCli import AppParser
from obsiasset.cli.appApi import AppApi
from obsiasset.utils.appLogger import AppLogger


def main():
    app_cli_parser = AppParser()
    parser = app_cli_parser.parser

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    args_cmd = args.command.replace("-", "_")

    AppLogger.logo()
    app_cli = AppApi(app_args=args.__dict__)
    try:
        app_cmd = getattr(app_cli, args_cmd)
        app_cmd()
        return True
    except AttributeError as e:
        AppLogger.failure(e)
        AppLogger.failure("Oops, some failures during execute command [{}]".format(args_cmd))
        return False


if __name__ == "__main__":
    print("🚀 This is main script")

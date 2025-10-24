#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: bxwill.shi@gmail.com


import os
# import shutil
import sys
# import requests
# import yaml
# from tabulate import tabulate
from obsiasset.utils.appLogger import AppLogger
from obsiasset.utils.appConfig import AppConfig
from obsiasset.utils.appManager import AppManager
# from crontab import CronTab
# from crontab import CronItem


def print_tree(start_path, indent=""):
    if indent == "":
        print(os.path.basename(start_path))
    for idx, item in enumerate(os.listdir(start_path)) if os.path.isdir(start_path) else {}:
        path = os.path.join(start_path, item)
        connector = "├── " if idx < len(os.listdir(start_path)) - 1 else "└── "
        print(indent + connector + item)
        if os.path.isdir(path):
            new_indent = indent + ("│   " if idx < len(os.listdir(start_path)) - 1 else "    ")
            print_tree(path, new_indent)
    return True



class AppApi(object):
    def __init__(self, app_args):
        self.app_config = AppConfig()
        self.app_args = app_args
        self.app_logger = AppLogger()
        self.app_manager = AppManager()

    def show_version(self):
        pkg_version = self.app_config.get_version_from_package()
        version_str_install = "{} [{}] version: {}".format(
            self.app_config.cmd_name,
            self.app_config.pkg_name,
            pkg_version
        )
        version_str_python = "Python version: {}".format(sys.version)
        version_str_tag = "\u00AF" * max(
            len(version_str_install),
            len(version_str_python.split("\n")[0])
        )
        print("\n".join([
            version_str_install,
            version_str_tag,
            version_str_python,
            version_str_tag,
        ]))
        return True

    def show_variables(self):
        # opt_items = OptItems()
        # for k, v in opt_items.__dict__.items():
        #     if k == "config_overwrite":
        #         continue
        #     print("\t".join([
        #         self.app_config.env_prefix + k.upper(),
        #         "{} : {}".format(v.help, " | ".join(v.choices)) if v.choices else v.help
        #     ]))
        return True

    def show_config(self):
        for k, v in self.app_config.app_config_yaml.items():
            if "_token" in k or "_secret" in k:
                self.app_logger.tab_success("{}: ******".format(k))
            else:
                self.app_logger.tab_success("{}: {}".format(k, v))
        return True

    def config_cred(self):
        config_json = dict()
        for key, value in self.app_args.items():
            if key not in ["command", "overwrite"] and value:
                config_json[key] = value
        self.app_config.create_config_file(
            config_file_json=config_json,
            force=True
        )
        self.app_logger.success("Create/Update config file:")
        self.show_config()
        return True

    def init(self):
        # param_vault = str(self.app_args.get("vault")).lower()
        param_schema = str(self.app_args.get("schema")).lower()
        param_lang = str(self.app_args.get("lang")).lower()
        param_sample = self.app_args.get("import_sample")
        self.app_logger.launch("Start to init a vault folder structure by schema [{}] and language [{}]...".format(
            param_schema,
            param_lang
        ))

        # if param_vault is None or param_vault == "":
        #     param_vault = "."
        # vault_path = os.path.join(
        #     self.app_config.app_workdir,
        #     param_vault
        # )
        setup_result = self.app_manager.setup_schema(
            schema_name=param_schema,
            lang_code=param_lang,
            abs_vault_path=self.app_config.app_workdir,
            import_sample=param_sample
        )
        if setup_result:
            self.app_logger.success("Complete to init vault folder structure.")
        else:
            self.app_logger.failure("Fail to init vault folder structure.")
            return False
        # if param_sample:
        #     import_result = self.app_manager.import_sample_assets(
        #         # self.app_config.app_workdir
        #     )
        #     if import_result:
        #         self.app_logger.success("Complete to import sample assets.")
        #     else:
        #         self.app_logger.failure("Fail to import sample assets.")
        #         return False
        self.app_logger.success("🎉 All done!")
        return True

    def reorg(self):
        pass


if __name__ == "__main__":
    print("🚀 This is an API package")
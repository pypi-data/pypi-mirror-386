#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: bxwill.shi@gmail.com


import os
import yaml
import json
from urllib.parse import urlparse, urlunparse
import importlib.util
from importlib.metadata import version, PackageNotFoundError
from obsiasset.utils.appLogger import AppLogger


def clean_url(url):
    parsed = urlparse(url)
    netloc = parsed.netloc.split("@")[-1]
    return urlunparse((
        parsed.scheme,
        netloc,
        parsed.path.rstrip(".git"),
        "",
        "",
        ""
    ))


class AppConfig(object):
    def __init__(self):
        pkg_spec = importlib.util.find_spec("obsiasset")
        self.pkg_dir = os.path.dirname(pkg_spec.origin) if pkg_spec and pkg_spec.origin else None
        self.tmpl_dir = os.path.join(self.pkg_dir, "tmpl") if self.pkg_dir else None
        self.schema_dir = os.path.join(self.pkg_dir, "schema") if self.pkg_dir else None
        self.sample_dir = os.path.join(self.pkg_dir, "sample") if self.pkg_dir else None
        self.i18n_dir = os.path.join(self.pkg_dir, "i18n") if self.pkg_dir else None
        self.app_workdir = os.getcwd()
        self.app_workdir_name = os.path.basename(self.app_workdir)

        self.pkg_name = "obsiasset".replace("-", "_")
        self.cmd_name = "obsiasset"
        self.app_name = self.cmd_name.replace("-", "_")
        self.env_prefix = self.app_name.upper() + "_"

        # self.app_config_file = os.path.join(
        #     os.path.expanduser("~"),
        #     ".{}".format(self.app_name),
        #     "credential.conf"
        # )
        self.app_config_yaml = dict()
        # if os.path.exists(self.app_config_file):
        #     with open(self.app_config_file, "r", encoding="utf-8") as f:
        #         self.app_config_yaml = yaml.safe_load(f.read())
        #     if not self.app_config_yaml:
        #         self.app_config_yaml = dict()

        self.app_logger = AppLogger()

    # def create_config_file(self, config_file_json: dict, force=False):
    #     config_exists = os.path.exists(self.app_config_file)
    #     if config_exists and force:
    #         for config_key, config_value in config_file_json.items():
    #             self.app_config_yaml[config_key] = config_value
    #         with open(self.app_config_file, "w", encoding="utf-8") as f:
    #             f.write(yaml.dump(self.app_config_yaml))
    #     elif not config_exists:
    #         os.makedirs(os.path.join(os.path.expanduser("~"), ".{}".format(self.app_name)), exist_ok=True)
    #         self.app_config_yaml = config_file_json
    #         with open(self.app_config_file, "w", encoding="utf-8") as f:
    #             f.write(yaml.dump(self.app_config_yaml))

    def get_config_from_input_and_env(self, key: str, input_args):
        if input_args.get(key):
            return input_args.get(key)
        else:
            return self.get_config_from_env(key)

    def get_config_from_env(self, key: str):
        """
        input parameter > env variable > config file
        :param key:
        :return:
        """
        env_key = self.env_prefix + key.upper()
        yaml_lower_key = key.lower()
        yaml_upper_key = key.upper()
        if os.getenv(env_key):
            return os.getenv(env_key)
        elif self.app_config_yaml.get(yaml_upper_key):
            return self.app_config_yaml.get(yaml_upper_key)
        elif self.app_config_yaml.get(yaml_lower_key):
            return self.app_config_yaml.get(yaml_lower_key)
        else:
            return None

    def get_version_from_package(self):
        try:
            pkg_version = version(self.pkg_name)
        except PackageNotFoundError:
            pkg_version = "0.x"
        return pkg_version

    def get_data_from_yaml_string(self, yaml_string, default_content={}):
        try:
            return yaml.safe_load(yaml_string)
        except Exception as e:
            self.app_logger.tab_failure("Failed to read yaml string : {}".format(e))
            return default_content

    def get_data_from_yaml_file(self, yaml_file, default_content={}):
        if not os.path.exists(yaml_file):
            self.app_logger.tab_warning("{} not found".format(yaml_file))
            return default_content
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f.read())
        except Exception as e:
            self.app_logger.tab_failure("Failed to read {} : {}".format(yaml_file, e))
            return default_content

    def get_data_from_json_file(self, json_file, default_content={}):
        if not os.path.exists(json_file):
            self.app_logger.tab_warning("{} not found".format(json_file))
            return default_content
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.app_logger.tab_failure("Failed to read {} : {}".format(json_file, e))
            return default_content

    def write_data_to_yaml_file(self, file_path, file_content):
        file_dir = os.path.dirname(file_path)
        if file_dir and not os.path.exists(file_dir):
            os.makedirs(file_dir, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(yaml.dump(file_content))
        return True
    
    def copy_file(self, src_path, dest_path):
        if not os.path.exists(src_path):
            self.app_logger.tab_failure("Source file {} not found".format(src_path))
            return False
        dest_dir = os.path.dirname(dest_path)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
        with open(src_path, "r", encoding="utf-8") as f_src:
            with open(dest_path, "w", encoding="utf-8") as f_dest:
                f_dest.write(f_src.read())
        return True


if __name__ == "__main__":
    print("🚀 This is a config package")
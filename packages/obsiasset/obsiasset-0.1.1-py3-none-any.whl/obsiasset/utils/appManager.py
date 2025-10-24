#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: bxwill.shi@gmail.com


import os
from jinja2 import Environment as j2Environment
from jinja2 import FileSystemLoader as j2FileSystemLoader
# from urllib.parse import urlparse, urlunparse
# import importlib.util
# from importlib.metadata import version, PackageNotFoundError
from obsiasset.utils.appLogger import AppLogger
from obsiasset.utils.appConfig import AppConfig


class AppManager(object):
    def __init__(self):
        self.app_config = AppConfig()
        self.app_logger = AppLogger()
        self.j2env_schemas = j2Environment(loader=j2FileSystemLoader(self.app_config.schema_dir))
        self.j2env_templates = j2Environment(loader=j2FileSystemLoader(self.app_config.tmpl_dir))
        self.j2env_samples = j2Environment(loader=j2FileSystemLoader(self.app_config.sample_dir))

    def get_supported_schemas(self):
        app_schemas = list()
        for item in os.listdir(self.app_config.schema_dir):
            if item.endswith(".yaml.j2"):
                app_schemas.append(item.replace(".yaml.j2", ""))
                # app_schema_file = os.path.join(self.app_config.schema_dir, item)
                # app_schema_yaml = self.app_config.get_data_from_yaml_file(app_schema_file)
                # if app_schema_yaml.get("name"):
                #     app_schemas.append(app_schema_yaml.get("name"))
        return app_schemas
    
    def get_supported_languages(self):
        app_languages = list()
        for item in os.listdir(self.app_config.i18n_dir):
            if item.endswith(".yaml"):
                lang_code = item.replace(".yaml", "").split("_")[-1]
                app_languages.append(lang_code)
        return app_languages

    def get_i18n_by_name(self, schema_name: str, lang_code: str):
        i18n_file_path = os.path.join(self.app_config.i18n_dir, "{}_{}.yaml".format(schema_name, lang_code))
        if not os.path.exists(i18n_file_path):
            self.app_logger.tab_failure("Cannot find i18n file by schema [{}] and language [{}]".format(
                schema_name,
                lang_code
            ))
            return None
        self.app_logger.tab_success("Load i18n file: {}".format(os.path.basename(i18n_file_path)))
        return self.app_config.get_data_from_yaml_file(i18n_file_path)

    def get_template_by_path(self, template_path: list):
        tmpl_file_path = os.path.join(self.app_config.tmpl_dir, *template_path)
        if not os.path.exists(tmpl_file_path):
            return None
        return self.app_config.get_data_from_yaml_file(tmpl_file_path)
    
    def setup_schema(self, schema_name: str, lang_code: str, abs_vault_path: list, import_sample: bool = False):
        i18n_config = self.get_i18n_by_name(schema_name, lang_code)
        if i18n_config is None:
            return False
        schema_config_string = self.j2env_schemas.get_template("{}.yaml.j2".format(schema_name)).render(i18n_config)
        schema_config = self.app_config.get_data_from_yaml_string(schema_config_string)
        sample_config = i18n_config.get("sample", {})
        for item in schema_config.get("entities", []):
            asset_path = item.get("path", [])
            template_path = item.get("template", [])
            abs_asset_path = os.path.join(abs_vault_path, *asset_path)
            if len(template_path) > 0:
                self.app_logger.tab_launch("Create file: {}".format(abs_asset_path))
                tmpl_content = self.j2env_templates.get_template(os.path.join(*template_path)).render(i18n_config)
                with open(abs_asset_path, "w", encoding="utf-8") as f:
                    f.write(tmpl_content)
                self.app_logger.tab_success("Done")
            else:
                self.app_logger.tab_launch("Create folder: {}".format(abs_asset_path))
                os.makedirs(abs_asset_path, exist_ok=True)
                self.app_logger.tab_success("Done")
            # Check and import sample assets
            sample_path = item.get("sample", [])
            sample_key = item.get("sample_key")
            if import_sample and len(sample_path) > 0 and sample_key and sample_key != "":
                for sample_item in sample_config.get(sample_key, []):
                    i18n_config['sample'][sample_key] = sample_item 
                    sample_name = "{}.md".format(sample_item.get("name", "?"))
                    abs_sample_path = os.path.join(abs_asset_path, sample_name)
                    self.app_logger.tab_launch("Import sample asset: {}".format(abs_sample_path))
                    sample_content = self.j2env_samples.get_template(os.path.join(*sample_path)).render(i18n_config)
                    with open(abs_sample_path, "w", encoding="utf-8") as f:
                        f.write(sample_content)
                    self.app_logger.tab_success("Done")
        return True


if __name__ == "__main__":
    print("🚀 This is a manager package")
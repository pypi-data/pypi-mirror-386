from functools import lru_cache
from pathlib import Path
from typing import Union

import yaml
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from fastgenerateapi.settings.redis_settings import RedisSettings
from fastgenerateapi.settings.app_settings import AppSettings
from fastgenerateapi.settings.system_settings import SystemSettings


class SettingsModel(BaseModel):
    # 应用配置
    app_settings: AppSettings = AppSettings()
    # 系统配置
    system_settings: SystemSettings = SystemSettings()
    # 缓存配置
    redis_settings: RedisSettings = RedisSettings()

    @classmethod
    def generate_file(cls, path='./.env'):
        """
        生成配置文件
        .env 会增加前缀
        .yaml 忽略前缀
        :param path: 可选 .env / application.yaml
        :return:
        """
        content = ''
        setting_models = cls.model_fields.copy()
        if path.__contains__('.env'):
            for k, v in setting_models.items():
                if isinstance(v, FieldInfo):
                    content += f"[{v.annotation.__name__}]\n"
                    env_prefix = v.annotation.model_config.get("env_prefix", "")
                    fields = v.annotation.model_fields.copy()
                    for k, v in fields.items():
                        field_name = f'{env_prefix}{k}'
                        if v.description is None:
                            content += f"{field_name}={v.default}\n"
                        else:
                            content += f"# {v.description}\n{field_name}={v.default}\n"
                    content += "\n"
        elif path.__contains__('.yaml'):
            for k, v in setting_models.items():
                if isinstance(v, FieldInfo):
                    content += f"[{v.annotation.__name__}]\n"
                    env_prefix = v.annotation.model_config.get("env_prefix", "")
                    fields = v.annotation.model_fields.copy()
                    for k, v in fields.items():
                        field_name = f'{env_prefix}{k}'
                        content += f"  {field_name}: {v.default}"
                        if v.description is None:
                            content += f"\n"
                        else:
                            content += f"  # {v.description}\n"
                    content += "\n"
        with open(file=path, mode='w', encoding='utf-8') as f:
            f.writelines(content)

    @classmethod
    @lru_cache
    def get_global_settings(cls, path: Union[Path, str, None] = '.env'):
        """
        get global settings and set into cache
        :param path: 可选 .env / application.yaml
        :return:
        """
        setting_models = cls.model_fields.copy()

        setting_dict = {}
        if str(path).__contains__('.env'):
            for k, v in setting_models.items():
                if isinstance(v, FieldInfo):
                    setting_dict[k] = v.annotation(_env_file=str(path))
        elif str(path).__contains__('.yaml'):
            with open(path, 'r', encoding='utf-8') as file:
                data_dict = yaml.safe_load(file)
            for k, v in setting_models.items():
                if isinstance(v, FieldInfo):
                    setting_dict[k] = v.annotation(**data_dict.get(v.annotation.__name__, {}))

        setting_data = cls(**setting_dict)
        global settings
        settings.app_settings = setting_data.app_settings
        settings.system_settings = setting_data.system_settings
        settings.redis_settings = setting_data.redis_settings
        return setting_data


settings = SettingsModel()


if __name__ == '__main__':
    settings.generate_file()


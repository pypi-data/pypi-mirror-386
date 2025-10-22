import configparser
import datetime
import os
import pathlib
import traceback
import uuid
from abc import ABC, abstractmethod
from enum import Enum

from .rpa_logging import logger

__version__ = '0.0.7'


class Config:
    """
    配置类，读取配置文件
    """

    def __init__(self, process_name):
        config_file = pathlib.Path(os.path.expanduser('~'), '.rpa/config/config.ini')
        config_parser = configparser.ConfigParser()
        config_parser.read(config_file, encoding='utf-8')
        process_config = {k: pathlib.Path(v) if k.endswith('_dir') else v for k, v in config_parser['global'].items()}
        if process_name in config_parser:
            process_config.update(config_parser[process_name])
        self.__dict__.update(process_config)


class RunStatus(str, Enum):
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    STOPPED = 'STOPPED'


class BaseProcess(ABC):
    process_name: str
    version: str
    max_attempts: int = 3

    def __init_subclass__(cls, **kwargs):  # 子类必须定义process_name属性
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'process_name') or not isinstance(cls.process_name, str):
            raise TypeError(f"类 {cls.__name__} 必须定义一个'process_name'的类属性，类型为str")

    def __init__(self):
        self.config = Config(self.process_name)
        self.__run_info = {'task_id': '',
                           'process_name': self.process_name,
                           'version': self.version,
                           'robot_id': '',
                           'trigger_type': None,
                           'start_time': None,
                           'end_time': None,
                           'duration_s': None,
                           'run_status': RunStatus.SUCCESS,
                           'initiated_by': '',
                           'message': '',
                           'is_uploaded': False
                           }

    @staticmethod
    def _format_time_difference(seconds):
        seconds = int(seconds)
        if seconds == 0:
            return "0秒"

        time_units = []

        # 计算各个时间单位
        hours = seconds // 3600
        remaining_seconds = seconds % 3600
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60

        # 添加非零单位到列表中
        if hours > 0:
            time_units.append(f"{hours}小时")
        if minutes > 0:
            time_units.append(f"{minutes}分钟")
        if seconds > 0:
            time_units.append(f"{seconds}秒")

        # 如果所有单位都是0（理论上不会发生，因为开头有检查）
        if not time_units:
            return "0秒"

        # 用空字符串连接各个单位
        return "".join(time_units)

    def front_hook(self):
        pass

    def finally_hook(self):
        pass

    @abstractmethod
    def main_process(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        run_status = RunStatus.FAILED
        start_time = datetime.datetime.now()
        logger.info(f'开始运行流程：{self.process_name}')
        message = '运行成功'
        try:
            for attempt in range(1, self.max_attempts + 1):
                try:
                    self.front_hook()
                    self.main_process(*args, **kwargs)
                    run_status = RunStatus.SUCCESS
                    break
                except Exception as e:
                    logger.error(f"第{attempt}次运行失败：{e}")
                    if attempt == self.max_attempts:
                        raise e
                finally:
                    self.finally_hook()
        except Exception as e:
            traceback.print_exc()
            message = traceback.format_exc()
            logger.exception(f"流程运行失败：{e}")
        finally:
            end_time: datetime = datetime.datetime.now()
            self.__run_info.update(
                task_id=kwargs.get('task_id', str(uuid.uuid4())),
                initiated_by=kwargs.get('initiated_by', 'local user'),
                trigger_type=kwargs.get('trigger_type', ''),
                robot_id=kwargs.get('robot_id', 'robot ID'),
                run_status=run_status,
                message=message,
                start_time=start_time,
                end_time=end_time,
                duration_s=(end_time - start_time).total_seconds(),
            )
            logger.info(self.__run_info)
            logger.info(f"流程运行结束：{self._format_time_difference(self.__run_info['duration_s'])}")

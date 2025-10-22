import pkgutil
import inspect
import sys


class BaseCommand:
    """所有命令的基类"""
    name = None  # 命令名
    help = None  # 命令帮助信息

    @classmethod
    def register(cls, subparsers):
        """注册命令到 subparsers"""
        sp = subparsers.add_parser(cls.name, help=cls.help)
        cls.add_arguments(sp)

        # ⚡ 实例化命令，并把 handler 绑定进去
        instance = cls()
        sp.set_defaults(func=instance.handle)

    @staticmethod
    def add_arguments(subparser):
        """子类实现：定义命令行参数"""
        pass

    def handle(self, args):
        """子类实现：执行逻辑"""
        raise NotImplementedError("handle() 必须在子类实现")


def load_commands():
    """动态加载 commands 目录下的所有命令类"""
    commands = []
    package = sys.modules[__name__]

    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        if module_name == "base":  # 跳过基类
            continue
        module = __import__(f"{__name__}.{module_name}", fromlist=[module_name])

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseCommand) and obj is not BaseCommand:
                if obj.name:  # 必须定义 name 才算命令
                    commands.append(obj)
    return commands

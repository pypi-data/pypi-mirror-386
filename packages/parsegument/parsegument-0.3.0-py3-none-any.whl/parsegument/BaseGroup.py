from __future__ import annotations
from typing import Union, Callable, TYPE_CHECKING, Any
from inspect import signature
import functools
from .utils.convert_params import convert_param
from .Command import Command
from .Node import CommandNode

if TYPE_CHECKING:
    from .CommandGroup import CommandGroup


class BaseGroup(CommandNode):
    def __init__(self, name:str, help: str=""):
        super().__init__(name, help)
        self.children: dict[str, Union[Command, CommandGroup]] = {}

    @classmethod
    def _get_methods(cls) -> set[str]:
        return set([i for i in dir(cls) if i[0] != "_"])

    @property
    def _get_help_messages(self) -> str:
        max_len = max(len(key) for key, _ in self.children.items())
        return "\n".join(f"{key.ljust(max_len*2 + 2)}{value.help}" for key, value in self.children.items())

    def add_child(self, child: Union[Command, CommandGroup]) -> bool:
        """Add a Command or CommandGroup as a child"""
        if child.name in [i.name for i in self.children.values()]:
            return False
        self.children[child.name] = child
        return True

    def command(self, name:str=None, help: str=None) -> Callable:
        """A Decorator that automatically creates a command, and adds it as a child"""

        def command_wrapper(func):
            orig = getattr(func, "__wrapped__", func)
            params = signature(func).parameters
            func_name = func.__name__
            command_object = Command(name=func_name, executable=func, help=help)
            for key, param in params.items():
                converted = convert_param(param)
                command_object.add_parameter(converted)
            if name:
                command_object.name = name
            self.add_child(command_object)

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            new_params = getattr(func, "__parameters__", None) or getattr(orig, "__parameters__", None)
            if new_params:
                for arg in new_params["args"].values():
                    command_object.parameters["args"][arg.name] = arg
                for kwarg in new_params["kwargs"].values():
                    command_object.parameters["kwargs"][kwarg.name] = kwarg
            wrapper.command = command_object
            orig.command = command_object

            return wrapper

        return command_wrapper

    def forward(self, nodes: list[str]) -> Any:
        child = self.children.get(nodes[0])
        if nodes[0] == "-help":
            return f"[{self.__class__.__name__}]\n{self.name}: {self.help}\n\n[Children]\n{self._get_help_messages}"
        if not child:
            return None
        return child.forward(nodes[1:])



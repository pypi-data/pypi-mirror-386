from typing import Callable, Union, Any
from .Parameters import Argument, Operand, Flag
import inspect
from .types.ArgDict import ArgDict
from .utils.parser import node_type, parse_operand, convert_string_to_result
from .Node import Node, CommandNode

class Command(CommandNode):
    """
    Linked to a function via executable
    Call flags using -flag
    call operands using --operand=value
    """
    parameters: ArgDict

    def __init__(self, name: str, executable: Callable, help: str="") -> None:
        super().__init__(name, help)
        self.parameters = {"args": {}, "kwargs": {}}
        self.executable = executable

    @property
    def _get_help_messages(self) -> str:
        items = list(self.parameters["args"].items()) + list(self.parameters["kwargs"].items())
        max_len = max(len(key) for key, _ in items)
        return "\n".join(f"{key.ljust(max_len*2 + 2)}{value.help}" for key, value in items)

    def add_parameter(self, param: Union[Argument, Operand, Flag]) -> None:
        """defines an argument, operand, or flag to the command"""
        if type(param) == Argument:
            self.parameters["args"][param.name] = param
        else:
            self.parameters["kwargs"][param.name] = param

    def forward(self, nodes:list[str]) -> Any:
        """Converts all arguments in nodes into its defined types, and executes the linked executable"""
        if "-help" in nodes:
            return f"[Command]\n{self.name}: {self.help}\n\n[Parameters]\n{self._get_help_messages}"

        args_length = len(self.parameters["args"])
        args = nodes[:args_length]
        args = {name:args[idx] for idx, name in enumerate(self.parameters["args"].keys())}
        args = [convert_string_to_result(value, self.parameters["args"][key].param_type) for key, value in args.items()]
        kwargs_strings = nodes[args_length:]
        kwargs = {}
        for kwarg_string in kwargs_strings:
            type_of_node = node_type(kwarg_string)
            if type_of_node == "Flag":
                kwargs[kwarg_string[1:]] = True
                continue
            elif type_of_node == "Operand":
                name, value = parse_operand(kwarg_string)
                node_arguments = self.parameters["kwargs"][name]
                value = convert_string_to_result(value, node_arguments.param_type)
                kwargs[name] = value
                continue
        return self.executable(*args, **kwargs)

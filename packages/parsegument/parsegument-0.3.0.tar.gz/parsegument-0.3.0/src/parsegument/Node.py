from typing import Any


class Node:
    def __init__(self, name: str, help: str) -> None:
        self.name = name
        self.help = help

    @property
    def help_message(self) -> str:
        return f"{self.name}: {self.help}"

class CommandNode(Node):
    def __init__(self, name: str, help: str) -> None:
        super().__init__(name, help)

    def forward(self, nodes:list[str]) -> Any:
        raise NotImplementedError
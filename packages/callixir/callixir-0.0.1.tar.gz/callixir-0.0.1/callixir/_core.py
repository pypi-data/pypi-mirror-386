from typing import Callable, Dict, List, Any
from ._exceptions import CommandAlreadyReg
from ._fingerprint import Fingerprint
from ._command_meta import CommandMeta
from ._command import Command
from inspect import signature, Parameter
import functools
import abc

class BasicDispatcher(abc.ABC):

	def __init__(self):
		self.__commands: Dict[str, CommandMeta] = {}

	def __get_fingerprint(self, func: Callable) -> Fingerprint:
		sig = signature(func)
		param_types = {}
		has_varargs = False

		for param_name, param in sig.parameters.items():
			if param.kind == Parameter.VAR_POSITIONAL:
				has_varargs = True
			param_types[param_name] = param.annotation if param.annotation != param.empty else None

		return Fingerprint(
			signature=sig,
			param_types=param_types,
			has_varargs=has_varargs
		)

	def __register_command(self, name: str, func: Callable):
		if name in self.__commands: raise CommandAlreadyReg(f"Cannot register the same command twice: '{name}'")
		self.__commands[name] = CommandMeta(
			name=name,
			func=func,
			fingerprint=self.__get_fingerprint(func)
		)

	def register(self, name: str, func: Callable):
		self.__register_command(name=name, func=func)

	# Decorator
	def reg(self, name: str):

		def decorator(func: Callable):
			self.__register_command(name=name, func=func)
			return func

		return decorator

	@property
	def commands(self) -> List[CommandMeta]: return [cmd for cmd in self.__commands.values()]

	def execute(self, command_str: str) -> Command: pass

	def _convert_arg(self, value: str, param_type: Callable) -> Any: pass

	def _get_command(self, name: str) -> CommandMeta: return self.__commands.get(name)
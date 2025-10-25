from typing import Callable, Any
from callixir._core import BasicDispatcher
from callixir._exceptions import UnknownCommand, ConvertArg, ArgumentOverflow
from callixir._command import Command
import time
import shlex

class SyncDispatcher(BasicDispatcher):

	def __init__(self, arg_overflow: bool):
		self.__arg_overflow = arg_overflow
		super().__init__()

	def execute(self, command_str: str) -> Command:

		t1 = time.perf_counter_ns()

		command_name, *command_args = shlex.split(command_str)

		command = self._get_command(command_name)

		if not command:
			raise UnknownCommand(f"Command '{command_name}' not found.")

		converted_args = []
		additional_args = []

		param_names = list(command.fingerprint.param_types.keys())

		for i, arg in enumerate(command_args):
			if command.fingerprint.has_varargs and i >= len(param_names):
				additional_args.append(self._convert_arg(arg, command.fingerprint.param_types[param_names[-1]]))
			else:
				if (i == 0 and len(param_names) == 0) or (i >= len(param_names)):
					if not self.__arg_overflow:
						raise ArgumentOverflow(
							f"Command '{command_name}' is overflowing with unknown arguments: {", ".join(command_args)}")
				else:
					param_type = command.fingerprint.param_types[param_names[i]]
					converted_args.append(self._convert_arg(arg, param_type))


		bound_args = command.fingerprint.signature.bind_partial(*converted_args, *additional_args)
		bound_args.apply_defaults()

		t2 = time.perf_counter_ns()

		result = command.func(*bound_args.args, **bound_args.kwargs)

		t3 = time.perf_counter_ns()

		return Command(
			command_str=command_str,
			name=command.name,
			args=command_args,
			result=result,
			ppt=t2-t1,
			fet=t3-t2
		)

	def _convert_arg(self, value: str, param_type: Callable) -> Any:
		if param_type is None:
			return value
		try:
			return param_type(value)
		except (ValueError, TypeError):
			raise ConvertArg(f"Cannot convert '{value}' to {param_type.__name__}")

from typing import Callable, Any, Dict
from ._fingerprint import Fingerprint

class CommandMeta:

	def __init__(self, name: str, func: Callable, fingerprint: Fingerprint):
		self.name = name
		self.func = func
		self.fingerprint = fingerprint

	def __repr__(self):
		return f"CommandMeta(name={self.name})"

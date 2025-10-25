from typing import Dict
from inspect import Signature

class Fingerprint:

	def __init__(self, signature: Signature, param_types: Dict, has_varargs: bool):
		self.signature = signature
		self.param_types = param_types
		self.has_varargs = has_varargs
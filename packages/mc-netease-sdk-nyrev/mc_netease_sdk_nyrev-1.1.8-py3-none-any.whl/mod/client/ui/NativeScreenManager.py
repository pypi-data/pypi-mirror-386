# -*- coding: utf-8 -*-


if 0:
	from typing import List


class NativeScreenManager(object):
	def __init__(self):
		pass

	def RegisterCustomControl(self, nativeData, customControlName, proxyClassName):
		# type: (List[str, str], str, str) -> bool
		pass

	def UnRegisterCustomControl(self, nativeData, customControlName):
		# type: (List[str, str], str) -> None
		pass

	def RegisterScreenProxy(self, screenName, proxyClassName):
		# type: (str, str) -> bool
		pass

	def UnRegisterScreenProxy(self, screenName, proxyClassName):
		# type: (str, str) -> None
		pass

	_instance = None

	@classmethod
	def instance(cls):
		if not cls._instance:
			cls._instance = cls()
		return cls._instance

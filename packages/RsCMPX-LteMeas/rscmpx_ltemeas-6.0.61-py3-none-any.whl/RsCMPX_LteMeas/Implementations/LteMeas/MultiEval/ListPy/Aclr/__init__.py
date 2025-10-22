from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class AclrCls:
	"""Aclr commands group definition. 22 total commands, 4 Subgroups, 0 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("aclr", core, parent)

	@property
	def utra(self):
		"""utra commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_utra'):
			from .Utra import UtraCls
			self._utra = UtraCls(self._core, self._cmd_group)
		return self._utra

	@property
	def eutra(self):
		"""eutra commands group. 4 Sub-classes, 0 commands."""
		if not hasattr(self, '_eutra'):
			from .Eutra import EutraCls
			self._eutra = EutraCls(self._core, self._cmd_group)
		return self._eutra

	@property
	def dchType(self):
		"""dchType commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_dchType'):
			from .DchType import DchTypeCls
			self._dchType = DchTypeCls(self._core, self._cmd_group)
		return self._dchType

	@property
	def dallocation(self):
		"""dallocation commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_dallocation'):
			from .Dallocation import DallocationCls
			self._dallocation = DallocationCls(self._core, self._cmd_group)
		return self._dallocation

	def clone(self) -> 'AclrCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = AclrCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group

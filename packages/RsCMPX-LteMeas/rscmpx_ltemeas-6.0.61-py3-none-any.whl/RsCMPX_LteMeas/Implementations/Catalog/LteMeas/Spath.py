from typing import List

from ....Internal.Core import Core
from ....Internal.CommandsGroup import CommandsGroup
from ....Internal import Conversions
from ....Internal.RepeatedCapability import RepeatedCapability
from .... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SpathCls:
	"""Spath commands group definition. 1 total commands, 0 Subgroups, 1 group commands
	Repeated Capability: SignalPath, default value after init: SignalPath.Nr1"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("spath", core, parent)
		self._cmd_group.rep_cap = RepeatedCapability(self._cmd_group.group_name, 'repcap_signalPath_get', 'repcap_signalPath_set', repcap.SignalPath.Nr1)

	def repcap_signalPath_set(self, signalPath: repcap.SignalPath) -> None:
		"""Repeated Capability default value numeric suffix.
		This value is used, if you do not explicitely set it in the child set/get methods, or if you leave it to SignalPath.Default.
		Default value after init: SignalPath.Nr1"""
		self._cmd_group.set_repcap_enum_value(signalPath)

	def repcap_signalPath_get(self) -> repcap.SignalPath:
		"""Returns the current default repeated capability for the child set/get methods"""
		# noinspection PyTypeChecker
		return self._cmd_group.get_repcap_enum_value()

	def get(self, signalPath=repcap.SignalPath.Default) -> List[str]:
		"""CATalog:LTE:MEASurement<Instance>:SPATh<StreamNumber> \n
		Snippet: value: List[str] = driver.catalog.lteMeas.spath.get(signalPath = repcap.SignalPath.Default) \n
		Returns the names of the available RF connections. \n
			:param signalPath: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Spath')
			:return: name_signal_path: Comma-separated list of strings, one string per RF connection."""
		signalPath_cmd_val = self._cmd_group.get_repcap_cmd_value(signalPath, repcap.SignalPath)
		response = self._core.io.query_str(f'CATalog:LTE:MEASurement<Instance>:SPATh{signalPath_cmd_val}?')
		return Conversions.str_to_str_list(response)

	def clone(self) -> 'SpathCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = SpathCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group

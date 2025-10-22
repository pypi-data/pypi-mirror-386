from typing import List

from ....Internal.Core import Core
from ....Internal.CommandsGroup import CommandsGroup
from ....Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SpathCls:
	"""Spath commands group definition. 2 total commands, 0 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("spath", core, parent)

	def get_count(self) -> int:
		"""ROUTe:LTE:MEASurement<Instance>:SPATh:COUNt \n
		Snippet: value: int = driver.route.lteMeas.spath.get_count() \n
		No command help available \n
			:return: signal_path_count: No help available
		"""
		response = self._core.io.query_str('ROUTe:LTE:MEASurement<Instance>:SPATh:COUNt?')
		return Conversions.str_to_int(response)

	def get_value(self) -> List[str]:
		"""ROUTe:LTE:MEASurement<Instance>:SPATh \n
		Snippet: value: List[str] = driver.route.lteMeas.spath.get_value() \n
		Selects one or more RF connections (signal input paths) . The number of expected connections depends on other settings.
		Configure them before sending this command.
			INTRO_CMD_HELP: We distinguish the following situations: \n
			- List mode OFF: One connection is expected.
			- List mode ON and connector mode GLOBal: One connection is expected. It is used for all list mode segments.
			- List mode ON and connector mode LIST: The number of connections configured via method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.nconnections is expected. The order of the connections assigns them to an index (connection with index 1, index 2, index 3, ...) . The connections must use different RF connectors of the same connector bench.
			INTRO_CMD_HELP: Related commands: \n
			- Connector mode: method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.cmode
			- Connection index per segment: method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.Segment.Cidx.set
		For possible connection names, see method RsCMPX_LteMeas.Catalog.LteMeas.Spath.get_. \n
			:return: signal_path: Comma-separated list of strings, one string per RF connection.
		"""
		response = self._core.io.query_str('ROUTe:LTE:MEASurement<Instance>:SPATh?')
		return Conversions.str_to_str_list(response)

	def set_value(self, signal_path: List[str]) -> None:
		"""ROUTe:LTE:MEASurement<Instance>:SPATh \n
		Snippet: driver.route.lteMeas.spath.set_value(signal_path = ['abc1', 'abc2', 'abc3']) \n
		Selects one or more RF connections (signal input paths) . The number of expected connections depends on other settings.
		Configure them before sending this command.
			INTRO_CMD_HELP: We distinguish the following situations: \n
			- List mode OFF: One connection is expected.
			- List mode ON and connector mode GLOBal: One connection is expected. It is used for all list mode segments.
			- List mode ON and connector mode LIST: The number of connections configured via method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.nconnections is expected. The order of the connections assigns them to an index (connection with index 1, index 2, index 3, ...) . The connections must use different RF connectors of the same connector bench.
			INTRO_CMD_HELP: Related commands: \n
			- Connector mode: method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.cmode
			- Connection index per segment: method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.Segment.Cidx.set
		For possible connection names, see method RsCMPX_LteMeas.Catalog.LteMeas.Spath.get_. \n
			:param signal_path: Comma-separated list of strings, one string per RF connection.
		"""
		param = Conversions.list_to_csv_quoted_str(signal_path)
		self._core.io.write(f'ROUTe:LTE:MEASurement<Instance>:SPATh {param}')

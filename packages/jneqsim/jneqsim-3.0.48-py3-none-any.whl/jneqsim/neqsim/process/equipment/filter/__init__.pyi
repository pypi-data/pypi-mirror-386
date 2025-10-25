
import sys
if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

import java.lang
import java.util
import jneqsim.neqsim.process.equipment
import jneqsim.neqsim.process.equipment.stream
import typing



class Filter(jneqsim.neqsim.process.equipment.TwoPortEquipment):
    def __init__(self, string: typing.Union[java.lang.String, str], streamInterface: jneqsim.neqsim.process.equipment.stream.StreamInterface): ...
    def getCvFactor(self) -> float: ...
    def getDeltaP(self) -> float: ...
    @typing.overload
    def run(self) -> None: ...
    @typing.overload
    def run(self, uUID: java.util.UUID) -> None: ...
    def runConditionAnalysis(self, processEquipmentInterface: jneqsim.neqsim.process.equipment.ProcessEquipmentInterface) -> None: ...
    def setCvFactor(self, double: float) -> None: ...
    @typing.overload
    def setDeltaP(self, double: float) -> None: ...
    @typing.overload
    def setDeltaP(self, double: float, string: typing.Union[java.lang.String, str]) -> None: ...

class CharCoalFilter(Filter):
    def __init__(self, string: typing.Union[java.lang.String, str], streamInterface: jneqsim.neqsim.process.equipment.stream.StreamInterface): ...


class __module_protocol__(Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("jneqsim.neqsim.process.equipment.filter")``.

    CharCoalFilter: typing.Type[CharCoalFilter]
    Filter: typing.Type[Filter]

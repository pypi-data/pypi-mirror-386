
import sys
if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

import jneqsim.neqsim.thermo.phase
import typing



class NeqSimSpanWagner:
    @staticmethod
    def getProperties(double: float, double2: float, phaseType: jneqsim.neqsim.thermo.phase.PhaseType) -> typing.MutableSequence[float]: ...


class __module_protocol__(Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("jneqsim.neqsim.thermo.util.spanwagner")``.

    NeqSimSpanWagner: typing.Type[NeqSimSpanWagner]

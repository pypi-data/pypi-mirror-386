
import sys
if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

import java.io
import jneqsim.neqsim.chemicalreactions
import jneqsim.neqsim.thermo.phase
import typing



class Kinetics(java.io.Serializable):
    def __init__(self, chemicalReactionOperations: jneqsim.neqsim.chemicalreactions.ChemicalReactionOperations): ...
    def calcKinetics(self) -> None: ...
    def calcReacMatrix(self, phaseInterface: jneqsim.neqsim.thermo.phase.PhaseInterface, phaseInterface2: jneqsim.neqsim.thermo.phase.PhaseInterface, int: int) -> float: ...
    def getPhiInfinite(self) -> float: ...
    def getPseudoFirstOrderCoef(self, phaseInterface: jneqsim.neqsim.thermo.phase.PhaseInterface, phaseInterface2: jneqsim.neqsim.thermo.phase.PhaseInterface, int: int) -> float: ...
    def isIrreversible(self) -> bool: ...


class __module_protocol__(Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("jneqsim.neqsim.chemicalreactions.kinetics")``.

    Kinetics: typing.Type[Kinetics]


import sys
if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

import jneqsim.neqsim.pvtsimulation.modeltuning
import jneqsim.neqsim.pvtsimulation.reservoirproperties
import jneqsim.neqsim.pvtsimulation.simulation
import jneqsim.neqsim.pvtsimulation.util
import typing


class __module_protocol__(Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("jneqsim.neqsim.pvtsimulation")``.

    modeltuning: jneqsim.neqsim.pvtsimulation.modeltuning.__module_protocol__
    reservoirproperties: jneqsim.neqsim.pvtsimulation.reservoirproperties.__module_protocol__
    simulation: jneqsim.neqsim.pvtsimulation.simulation.__module_protocol__
    util: jneqsim.neqsim.pvtsimulation.util.__module_protocol__

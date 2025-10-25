
import sys
if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

import jneqsim.neqsim.fluidmechanics.util.fluidmechanicsvisualization.flowsystemvisualization
import jneqsim.neqsim.fluidmechanics.util.fluidmechanicsvisualization.flowsystemvisualization.twophaseflowvisualization.twophasepipeflowvisualization
import typing



class TwoPhaseFlowVisualization(jneqsim.neqsim.fluidmechanics.util.fluidmechanicsvisualization.flowsystemvisualization.FlowSystemVisualization):
    @typing.overload
    def __init__(self): ...
    @typing.overload
    def __init__(self, int: int, int2: int): ...


class __module_protocol__(Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("jneqsim.neqsim.fluidmechanics.util.fluidmechanicsvisualization.flowsystemvisualization.twophaseflowvisualization")``.

    TwoPhaseFlowVisualization: typing.Type[TwoPhaseFlowVisualization]
    twophasepipeflowvisualization: jneqsim.neqsim.fluidmechanics.util.fluidmechanicsvisualization.flowsystemvisualization.twophaseflowvisualization.twophasepipeflowvisualization.__module_protocol__

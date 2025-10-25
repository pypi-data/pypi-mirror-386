# pylint: disable=notimplemented-raised, too-many-lines, too-many-public-methods
"""
ICoCo compatible interface to couple the visualizer to other codes using the coupling tool C3PO

ICOCO interface API:
https://github.com/cea-trust-platform/icoco-coupling

C3PO coupling tool:
https://github.com/code-coupling/c3po


The process threads structure of a coupling with the visualiser works as follow:


|             C3PO used process               |   Slave 1 process  |
|   C3PO Thread     -       Visualizer thread |   Slave 1 thread   |

        *
            C3PO objects, and drivers creation
        *   --------------------------------------->    *
            For each Visualization panel, a new process is created with a slave that will provide the data to the visualizer (1 in this example)

        *
            GridStackDriver initialisation
        *   ------------------->    *
            pn.serve() -> creation of the visualizer thread
                                    *   ----------->    *
                                    *   <-----------    *
            At each update of a panel (requested by the visualizer thread, on a button clic for example), an exchange of request is done between the visualizer thread and its associated thread.
                                    *
            The visualizer thread can then request itself to update the visualizer at the end of the tick based on the data received from the slave.

        *   --------------------------------------->    *
            At each setInputMedFieldDouble call, the C3PO thread provides the slave associated to the field the new version of the field.
        *
            If the C3PO Thread requests an update to the Visualizer, in the end, the C3PO Thread requests a plot update, two cases:
                -   The C3PO Thread doesn't have the hand on the plots, throwing an exception;
                -   The C3PO Thread adds a task, it is not read by the Visualizer thread, therefore not updating.

                                    *
            The visualizer update has to come from the Visualizer thread to be able to work:
                -   A play button was added, if clicked, a periodic task is added (from the Visualizer thread which handles the GUI) every second to refresh the visualization;
                -   The C3PO Thread will set a boolean to mark the need for an update;
                -   At each periodic task, if the boolean is at True, the Visualizer thread refreshes the geometry
"""

from typing import List, Tuple

from icoco.utils import medcoupling  # type: ignore
from icoco.exception import WrongContext, WrongArgument
from icoco.problem import Problem, ValueType

import panel as pn
import socket

from scivianna.interface.generic_interface import IcocoInterface
from scivianna.layout.gridstack import GridStackLayout
from scivianna.panel.line_plot_panel import LineVisualisationPanel


class Value:

    UPDATE_RATE = "UPDATE_RATE"
    """Int value to define the update frequency (done 1/UPDATE_RATE calls to solveTimeStep)"""


class GridStackProblem(Problem):
    panel: GridStackLayout

    def __init__(
        self, grid_stack: GridStackLayout, title="C3PO Coupling visualizer"
    ):
        self.gridstack = grid_stack

        self.time = 0.0
        self._dt: float = -1.0
        self._up_rate = 1
        self._up_skipped = 0
        self.stationary = True

        self.data_file_path = None
        self.title = title

    def setDataFile(self, datafile: str) -> None:
        """(Optional) Provide the relative path of a data file to be used by the code.

        This method must be called before initialize().

        Parameters
        ----------
        datafile : str
            relative path to the data file.

        Raises
        ------
        WrongContext
            exception if called multiple times or after initialize().
        WrongArgument
            exception if an invalid path is provided.
        """
        self.data_file_path = datafile

    def initialize(self) -> bool:
        """(Mandatory) Initialize the current problem instance.

        In this method the code should allocate all its internal structures and be ready to execute.
        File reads, memory allocations, and other operations likely to fail should be performed
        here, and not in the constructor (and not in the setDataFile() or in the setMPIComm()
        methods either).
        This method must be called only once (after a potential call to setMPIComm() and/or
        setDataFile()) and cannot be called again before terminate() has been performed.

        Returns
        -------
        bool
            true if all OK, otherwise false.

        Raises
        ------
        WrongContext
            exception if called multiple times or after initialize().
        """
        print("\n\nVisualizer initializing\n\n")
        # if self.data_file_path is not None:
        #     with open(self.data_file_path, "r") as f:
        #         data = json.load(f)

        #         for panel_name in data:
        #             if not panel_name in self.gridstack.visualisation_panels:
        #                 raise ValueError(f"Datafile panel name {panel_name} not present in the provided GridStack. Available keys: {list(self.gridstack.visualisation_panels.keys())}")

        #             key, file_path = data[panel_name]
        #             panel = self.gridstack.get_panel(panel_name)

        #             slave = panel.get_slave()
        #             slave.reset()
        #             slave.read_file(file_path, key)

        #             new_panel = VisualizationPanel(slave, name=panel.name)
        #             self.gridstack.set_panel(panel_name, new_panel)
        #             new_panel.field_color_selector.options = list(set(slave.get_labels()))
        #             new_panel.field_color_selector.value = [new_panel.field_color_selector.options[-1]]
        #             new_panel.recompute()

        # self.gridstack.make_grid_stack()

        ip_adress = socket.gethostbyname(socket.gethostname())

        """
            Catching a free port to provide to pn.serve
        """
        sock = socket.socket()
        sock.bind((ip_adress, 0))
        port = sock.getsockname()[1]
        sock.close()

        pn.serve(
            pn.template.BootstrapTemplate(
                main=[
                    pn.Column(
                        self.gridstack.bounds_row,
                        self.gridstack.main_frame,
                        height_policy="max",
                        width_policy="max",
                        margin=0,
                    )
                ],
                sidebar=[self.gridstack.side_bar],
                title=self.title,
            ),
            address=ip_adress,
            websocket_origin=f"{ip_adress}:{port}",
            port=port,
            # show = False,
            threaded=True,
            title=self.title,
        )

        self.panels_to_recompute: List[str] = []

        self._dt = None
        self.time = 0.0
        self._up_rate = 1
        self._up_skipped = 0
        return True

    def terminate(self) -> None:
        """(Mandatory) Terminate the current problem instance and release all allocated resources.

        Terminate the computation, free the memory and save whatever needs to be saved.
        This method is called once at the end of the computation or after a non-recoverable error.
        No other ICoCo method except setDataFile(), setMPIComm() and initialize() may be called
        after this.

        Raises
        ------
        WrongContext
            exception if called before initialize() or after terminate().
            exception if called inside the TIME_STEP_DEFINED context (see Problem documentation).
        """
        self._dt = -1.0
        self.time = 0.0
        self._up_rate = 1
        self._up_skipped = 0

    def presentTime(self) -> float:
        """(Mandatory) Return the current time of the simulation.

        Can be called any time between initialize() and terminate().
        The current time can only change during a call to validateTimeStep() or to resetTime().

        Returns
        -------
        float
            the current (physical) time of the simulation

        Raises
        ------
        WrongContext
            exception if called before initialize() or after terminate().
        """
        return self.time

    def computeTimeStep(self) -> Tuple[float, bool]:
        """(Mandatory) Return the next preferred time step (time increment) for this code, and
        whether the code wants to stop.

        Both data are only indicative, the supervisor is not required to take them into account.
        This method is however marked as mandatory, since most of the coupling schemes expect the
        code to provide this information (those schemes then typically compute the minimum of the
        time steps of all the codes being coupled). Hence a possible implementation is to return a
        huge value, if a precise figure can not be computed.

        Can be called whenever the code is outside the TIME_STEP_DEFINED context (see Problem
        documentation).

        Returns
        -------
        Tuple[float, bool]
            - the preferred time step for this code (only valid if stop is false).
            - stop set to true if the code wants to stop. It can be used for example to indicate
              that, according to a certain criterion, the end of the transient computation is
              reached from the code point of view.

        Raises
        ------
        WrongContext
            exception if called before initialize() or after terminate().
            exception if called inside the TIME_STEP_DEFINED context (see Problem documentation).
        """
        return 1e8, False

    def initTimeStep(self, dt: float) -> bool:
        """(Mandatory) Provide the next time step (time increment) to be used by the code.

        After this call (if successful), the computation time step is defined to ]t, t + dt] where
        t is the value returned by presentTime(). The code enters the TIME_STEP_DEFINED context.

        A time step = 0.0 may be used when the stationaryMode is set to true for codes solving
        directly for the steady-state.

        Parameters
        ----------
        dt : float
            dt the time step to be used by the code

        Returns
        -------
        bool
            false means that given time step is not compatible with the code time scheme.

        Raises
        ------
        WrongContext
            exception if called before initialize() or after terminate().
            exception if called inside the TIME_STEP_DEFINED context (see Problem documentation).
            exception if called several times without resolution.
        WrongArgument
            exception if dt is invalid (dt < 0.0).
        """

        if self._dt is not None and self._dt < 0.0:
            raise WrongContext(
                prob=f"{self.__class__.__module__}.{self.__class__.__name__}",
                method="initTimeStep",
                precondition="must be called after initialize.",
            )
        if self._dt is not None:
            raise WrongContext(
                prob=f"{self.__class__.__module__}.{self.__class__.__name__}",
                method="initTimeStep",
                precondition="must be called outside time step context.",
            )
        if dt < 0.0:
            raise WrongArgument(
                prob=f"{self.__class__.__module__}.{self.__class__.__name__}",
                method="initTimeStep",
                arg="dt",
                condition="must be >= 0.0.",
            )

        self._dt = dt

    def solveTimeStep(self) -> bool:
        """(Mandatory) Perform the computation on the current time interval.

        Can be called whenever the code is inside the TIME_STEP_DEFINED context
        (see Problem documentation).

        Returns
        -------
        bool
            true if computation was successful, false otherwise.

        Raises
        ------
        WrongContext
            exception if called before initialize() or after terminate().
            exception if called outside the TIME_STEP_DEFINED context (see Problem documentation).
            exception exception if called several times without a call to validateTimeStep() or to
            abortTimeStep().
        """
        if self._up_skipped == self._up_rate:
            # here we should transfer data and update the visu
            self.gridstack.mark_to_recompute(self.panels_to_recompute)
            self.panels_to_recompute.clear()

        return True

    def validateTimeStep(self) -> None:
        """(Mandatory) Validate the computation performed by solveTimeStep.

        Can be called whenever the code is inside the TIME_STEP_DEFINED context (see Problem
        documentation).

        After this call:
        - the present time has been advanced to the end of the computation time step
        - the computation time step is undefined (the code leaves the TIME_STEP_DEFINED context).

        Raises
        ------
        WrongContext
            exception if called before initialize() or after terminate().
            exception if called outside the TIME_STEP_DEFINED context (see Problem documentation).
            exception if called before the solveTimeStep() method.
        """

        self.time += self._dt
        self._dt = None

        if self._up_skipped == self._up_rate:
            self._up_skipped = 0
        else:
            self._up_skipped += 1

    def abortTimeStep(self):
        self._dt = None

    def setStationaryMode(self, stationaryMode: bool) -> None:
        """(Mandatory) Set whether the code should compute a stationary solution or a transient one.

        New in version 2 of ICoCo. By default the code is assumed to be in stationary mode False
        (i.e. set up for a transient computation).
        If set to True, solveTimeStep() can be used either to solve a time step in view of an
        asymptotic solution, or to solve directly for the steady-state. In this last case, a time
        step = 0. can be used with initTimeStep() (whose call is always needed).
        The stationary mode status of the code can only be modified by this method (or by a call to
        terminate() followed by initialize()).

        Parameters
        ----------
        stationaryMode : bool
            true if the code should compute a stationary solution.

        Raises
        ------
        WrongContext
            called inside the TIME_STEP_DEFINED context (see Problem documentation).
            called before initialize() or after terminate().
        """
        self.stationary = stationaryMode

    def getStationaryMode(self) -> bool:
        """(Mandatory) Indicate whether the code should compute a stationary solution or a
        transient one.

        See also setStationaryMode().

        Can be called whenever the code is outside the TIME_STEP_DEFINED context
        (see Problem documentation).

        Returns
        -------
        bool
            true if the code has been set to compute a stationary solution.

        Raises
        ------
        WrongContext
            exception if called before initialize() or after terminate().
            exception if called inside the TIME_STEP_DEFINED context (see Problem documentation).
        """
        return self.stationary

    def getValueType(self, name: str) -> ValueType:

        if name == Value.UPDATE_RATE:
            return ValueType.Int

        super().getValueType(name=name)

    def getInputValuesNames(self):

        return [Value.UPDATE_RATE]

    def setInputIntValue(self, name: str, val: float):

        if name == Value.UPDATE_RATE:
            self._up_rate = val
            return

        super().setInputIntValue(name=name, val=val)

    def getInputMEDDoubleFieldTemplate(
        self, name: str
    ) -> medcoupling.MEDCouplingFieldDouble:
        """(Optional) Retrieve an empty shell for an input field. This shell can be filled by the
        caller and then be given to the code via setInputField(). The field has the MEDDoubleField
        format.

        The code uses this method to populate 'afield' with all the data that represents the context
        of the field (i.e. its support mesh, its discretization -- on nodes, on elements, ...).
        The remaining job for the caller of this method is to fill the actual values of the field
        itself.
        When this is done the field can be sent back to the code through the method setInputField().
        This method is not mandatory but is useful to know the mesh, discretization... on which an
        input field is expected.

        See Problem documentation for more details on the time semantic of a field.

        Parameters
        ----------
        name : str
            name of the field for which we would like the empty shell

        Returns
        -------
        medcoupling.MEDCouplingFieldDouble
            field object (in MEDDoubleField format) that will be populated with all the contextual
            information.
            Any previous information in this object will be discarded.

        Raises
        ------
        WrongContext
            exception if called before initialize() or after terminate().
        WrongArgument
            exception if the field name is invalid.
        """
        visualization_panel, field_name = name.split("@")

        slave = self.gridstack.get_panel(visualization_panel).get_slave()

        if field_name not in slave.get_labels():
            raise ValueError(
                f"Unknown requested field {field_name} for panel  {visualization_panel}, available fields: {list(slave.get_labels())}. Make sure the key requested by the exchanger is defined as panel_name@field_name"
            )

        return slave.getInputMEDDoubleFieldTemplate(field_name)

    def setInputMEDDoubleField(
        self, name: str, afield: medcoupling.MEDCouplingFieldDouble
    ) -> None:
        """(Optional) Provide the code with input data in the form of a MEDDoubleField.

        The method getInputFieldTemplate(), if implemented, may be used first to prepare an empty
        shell of the field to pass to the code.

        See Problem documentation for more details on the time semantic of a field.

        Parameters
        ----------
        name : str
            name of the field that is given to the code.
        afield : medcoupling.MEDCouplingFieldDouble
            field object (in MEDDoubleField format) containing the input data to be read by the
            code. The name of the field set on this instance (with the Field::setName() method)
            should not be checked. However its time value should be to ensure it is within the
            proper time interval ]t, t+dt].

        Raises
        ------
        WrongContext
            exception if called before initialize() or after terminate().
        WrongArgument
            exception if the field name ('name' parameter) is invalid.
            exception if the time property of 'afield' does not belong to the currently computed
            time step ]t, t + dt]
        """

        print("setting fields...")
        visualization_panel, field_name = name.split("@")

        panel = self.gridstack.get_panel(visualization_panel)
        slave = panel.get_slave()

        if field_name not in slave.get_labels():
            raise ValueError(
                f"Unknown requested field {field_name} for panel  {visualization_panel}, available fields: {list(slave.get_labels())}. Make sure the key requested by the exchanger is defined as panel_name@field_name"
            )

        #   The time is set before the field
        slave.setTime(self.time)
        return_val = slave.setInputMEDDoubleField(field_name, afield)

        self.panels_to_recompute.append(visualization_panel)

        return return_val

    def setInputDoubleValue(self, name: str, val: float) -> None:
        """(Optional) Provide the code with a scalar double data.

        See Problem documentation for more details on the time semantic of a scalar value.

        Parameters
        ----------
        name : str
            name of the scalar value that is given to the code.
        val : float
            value passed to the code.

        Raises
        ------
        WrongArgument
            exception if the scalar name ('name' parameter) is invalid.
        WrongContext
            exception if called before initialize() or after terminate().
        """

        visualization_panel, field_name = name.split("@")

        panel = self.gridstack.get_panel(visualization_panel)
        slave = panel.get_slave()

        #   The time is set before the field
        slave.setTime(self.time)
        return_val = slave.setInputDoubleValue(field_name, val)

        self.panels_to_recompute.append(visualization_panel)

        return return_val

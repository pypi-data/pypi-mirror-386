import multiprocessing as mp
import numpy as np
import pandas as pd
from typing import Any, List, Tuple, Dict, Union

from scivianna.data.data2d import Data2D
from scivianna.interface.option_element import OptionElement
from scivianna.utils.polygonize_tools import PolygonElement
from scivianna.enums import VisualizationMode, GeometryType, DataType

from typing import TYPE_CHECKING

#   TYPE_CHECKING : Allows fake import of modules pylance work without importing them
if TYPE_CHECKING:
    import medcoupling

from scivianna.constants import MESH, MATERIAL


class GenericInterface:
    """ Generic interface class that implement basic functions. This class mutualises functions that are shared between its child classes.
    """
    def read_file(self, file_path: str, file_label: str) -> None:
        """Read a file and store its content in the interface

        Parameters
        ----------
        file_path : str
            File to read
        file_label : str
            Label to define the file type

        Raises
        ------
        NotImplementedError
            Function to override in the code interfaces
        """
        raise NotImplementedError()

    def get_labels(self) -> List[str]:
        """Returns a list of fields names displayable with this interface

        Returns
        -------
        List[str]
            List of fields names
        """
        return [MESH, MATERIAL]

    def get_label_coloring_mode(self, label: str) -> VisualizationMode:
        """Returns wheter the given field is colored based on a string value or a float.

        Parameters
        ----------
        label : str
            Field to color name

        Returns
        -------
        VisualizationMode
            Coloring mode

        Raises
        ------
        NotImplementedError
            Function to override in the code interfaces
        """
        raise NotImplementedError()

    def get_file_input_list(self) -> List[Tuple[str, str]]:
        """Returns a list of file label and its description for the GUI

        Returns
        -------
        List[Tuple[str, str]]
            List of (file label, description)

        Raises
        ------
        NotImplementedError
            The function was not implemented in the code interface.
        """
        raise NotImplementedError()

    def get_options_list(self) -> List[OptionElement]:
        """Returns a list of options required by a code interface to add to the coordinate ribbon.

        Returns
        -------
        List[OptionElement]
            List of option objects.
        """
        return []
    
    @classmethod
    def serialize(self, obj: Any, key: str) -> Any:
        """This function receives an object that is about to be transmitted at the given key.
        -   If the object can be passed through a python multiprocessing Queue, it can be returned.
        -   If the object can't, it is serialized, and the code returns the file path.

        The read function will then be able to expect the returned object at the given key.

        By default, this class returns the obj, if the cobject can't be passed, overwrite this function.

        Parameters
        ----------
        obj : Any
            Object that is sent to the generic interface
        key : str
            Key associated to the object

        Returns
        -------
        Any
            Object transmissible through a multiprocessing Queue associated to the given object.
        """
        return obj


class Geometry2D(GenericInterface):
    """ Interface parent class for classes that can compute geometry 2D slices.
    """
    geometry_type:GeometryType
    """Enum telling if the geometry is 2D or 3D (Displays the axis card and the w coordinate in the GUI)."""
    data_type:DataType
    """Enum saying if the data are returned in a 2D grid or a polygon list"""
    rasterized:bool = False
    """Boolean telling if the geometry is made by rasterizing a 2D grid (displays the line count in the GUI)."""
    

    def compute_2D_data(
        self,
        u: Tuple[float, float, float],
        v: Tuple[float, float, float],
        u_min: float,
        u_max: float,
        v_min: float,
        v_max: float,
        u_steps: int,
        v_steps: int,
        w_value: float,
        q_tasks: mp.Queue,
        options: Dict[str, Any],
    ) -> Tuple[Data2D, bool]:
        """Returns a list of polygons that defines the geometry in a given frame

        Parameters
        ----------
        u : Tuple[float, float, float]
            Horizontal coordinate director vector
        v : Tuple[float, float, float]
            Vertical coordinate director vector
        u_min : float
            Lower bound value along the u axis
        u_max : float
            Upper bound value along the u axis
        v_min : float
            Lower bound value along the v axis
        v_max : float
            Upper bound value along the v axis
        u_steps : int
            Number of points along the u axis
        v_steps : int
            Number of points along the v axis
        w_value : float
            Value along the u ^ v axis
        q_tasks : mp.Queue
            Queue from which get orders from the master.
        options : Dict[str, Any]
            Additional options for frame computation.

        Returns
        -------
        Data2D
            Geometry to display
        bool
            Were the polygons updated compared to the past call

        Raises
        ------
        NotImplementedError
            Function to override in the code interfaces
        """
        raise NotImplementedError()

    def get_value_dict(
        self, value_label: str, volumes: List[Union[int, str]], options: Dict[str, Any]
    ) -> Dict[Union[int, str], str]:
        """Returns a volume name - field value map for a given field name

        Parameters
        ----------
        value_label : str
            Field name to get values from
        volumes : List[Union[int,str]]
            List of volumes names
        options : Dict[str, Any]
            Additional options for frame computation.

        Returns
        -------
        Dict[Union[int,str], str]
            Field value for each requested volume names

        Raises
        ------
        NotImplementedError
            Function to override in the code interfaces
        """
        raise NotImplementedError()

class Geometry2DPolygon(Geometry2D):
    """ Interface parent class for classes that can compute geometry 2D slices and provide a list of polygons.
    """
class Geometry2DGrid(Geometry2D):
    """ Interface parent class for classes that can compute geometry 2D slices and provide a numpy array.
    """
    rasterized:bool = True
    """Boolean telling if the geometry is made by rasterizing a 2D grid (displays the line count in the GUI)."""
    

class ValueAtLocation(GenericInterface):
    """ Interface parent class to implement a function to get values at a specific location.
    """
    def get_value(
        self,
        position: Tuple[float, float, float],
        volume_index: str,
        material_name: str,
        field: str,
    ) -> Union[str, float]:
        """Provides the result value of a field from either the (x, y, z) position, the volume index, or the material name.

        Parameters
        ----------
        position : Tuple[float, float, float]
            Position at which the value is requested
        volume_index : str
            Index of the requested volume
        material_name : str
            Name of the requested material
        field : str
            Requested field name

        Returns
        -------
        Union[str, float]
            Field value
        """
        raise NotImplementedError()

    def get_values(
        self,
        positions: List[Tuple[float, float, float]],
        volume_indexes: List[str],
        material_names: List[str],
        field: str,
    ) -> List[Union[str, float]]:
        """Provides the result values at different positions from either the (x, y, z) positions, the volume indexes, or the material names.

        Parameters
        ----------
        positions : List[Tuple[float, float, float]]
            List of position at which the value is requested
        volume_indexes : List[str]
            Indexes of the requested volumes
        material_names : List[str]
            Names of the requested materials
        field : str
            Requested field name

        Returns
        -------
        List[Union[str, float]]
            Field values
        """
        raise NotImplementedError()

class Value1DAtLocation(GenericInterface):
    """ Interface parent class to implement a function to get 1D data at a specific location.
    """
    def get_1D_value(
        self,
        position: Tuple[float, float, float],
        volume_index: str,
        material_name: str,
        field: str,
    ) -> Union[pd.Series, List[pd.Series]]:
        """Provides the 1D value of a field from either the (x, y, z) position, the volume index, or the material name.

        Parameters
        ----------
        position : Tuple[float, float, float]
            Position at which the value is requested
        volume_index : str
            Index of the requested volume
        material_name : str
            Name of the requested material
        field : str
            Requested field name

        Returns
        -------
        Union[pd.Series, List[pd.Series]]
            Field value
        """
        raise NotImplementedError()


class OverLine(GenericInterface):
    """ Interface parent class to implement a function to compute a field value along a 1D line.
    """
    def compute_1D_line_data(
        self,
        pos: Tuple[float, float, float],
        u: Tuple[float, float, float],
        d: float,
        q_tasks: mp.Queue,
        options: Dict[str, Any],
    ) -> pd.DataFrame:
        """Returns a list of polygons that defines the geometry in a given frame

        Parameters
        ----------
        pos : Tuple[float, float, float]
            1D data line start location
        u : Tuple[float, float, float]
            Data line direction vector
        d : float
            Distance to travel by the 1D line
        q_tasks : mp.Queue
            Queue from which get orders from the master.
        options : Dict[str, Any]
            Additional options for frame computation.

        Returns
        -------
        pd.DataFrame
            Pandas dataframe containing the data

        Raises
        ------
        NotImplementedError
            Function to override in the code interfaces
        """
        raise NotImplementedError()


class IcocoInterface(GenericInterface):
    """ Interface parent class to implement the C3PO functions required for a code coupling visualization.
    """
    def getInputMEDDoubleFieldTemplate(self, field_name: str) -> "medcoupling.MEDCouplingFieldDouble":
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
        raise NotImplementedError

    def setInputMEDDoubleField(
        self, field_name: str, field: "medcoupling.MEDCouplingFieldDouble"
    ):
        """(Optional) Provide the code with input data in the form of a MEDDoubleField.

        The method getInputFieldTemplate(), if implemented, may be used first to prepare an empty
        shell of the field to pass to the code.

        See Problem documentation for more details on the time semantic of a field.

        Parameters
        ----------
        name : str
            name of the field that is given to the code.
        field : medcoupling.MEDCouplingFieldDouble
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
        raise NotImplementedError

    def setTime(self, time:float):
        """This non-Icoco function allows setting the current time in an interface to associate to the received value.

        Parameters
        ----------
        time : float
            Current time
        """
        raise NotImplementedError

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
        raise NotImplementedError

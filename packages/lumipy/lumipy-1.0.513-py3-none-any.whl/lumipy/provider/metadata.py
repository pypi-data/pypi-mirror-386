from enum import Enum
from typing import Optional, Dict, Union, List

from lumipy.lumiflex import DType


class ColumnMeta:
    """Column Metadata class that represents the properties of a provider column.

    """

    def __init__(
            self,
            name: str,
            data_type: DType,
            description: Optional[str] = None,
            is_main: Optional[bool] = False,
            is_primary_key: Optional[bool] = False
    ):
        """Constructor for the ColumnMeta class.

        Args:
            name (str): name of the provider column.
            data_type (str): data type of the provider column.
            description (Optional[str]): description of the provider column.
            is_main (Optional[bool]): whether the provider column is a main column or not.
            is_primary_key (Optional[bool]): whether the provider column is a primary key column.

        """

        if not isinstance(data_type, DType):
            raise TypeError("ColumnMeta() data_type arg must be a DType enum value.")

        self.name = name
        self.data_type = data_type
        self.description = description if description is not None else ""
        self.is_main = is_main
        self.is_primary_key = is_primary_key

    def to_dict(self) -> Dict[str, Union[str, int, float, bool]]:
        """Build dictionary object that contains the column metadata.

        Returns:
            Dict[str, Union[str, int, float, bool]]: dictionary representing the column metadata.
        """

        return {
            "Name": self.name,
            "Type": self.data_type.name,
            "Description": self.description,
            "IsMain": self.is_main,
            "IsPrimaryKey": self.is_primary_key
        }


class ParamMeta:
    """Parameter metadata class that represents the properties of a provider parameter.

    """
    def __init__(
            self,
            name: str,
            data_type: DType,
            description: Optional[str] = None,
            default_value: Optional[object] = None,
            is_required: Optional[bool] = False
    ):
        """Constructor for the ParamMeta class

        Args:
            name (str): name of the provider parameter.
            data_type (str): data type of the provider parameter.
            description (Optional[str]): optional description of the provider parameter.
            default_value (Optional[object]): optional default value of the provider parameter.
            is_required (Optional[bool]): flag that sets whether this parameter must always be specified. If set to true
            the provider will throw an error when a value is not given.
        """

        if not isinstance(data_type, DType):
            raise TypeError("ParamMeta() data_type arg must be a DType enum value.")

        self.name = name
        self.data_type = data_type
        self.description = description if description is not None else ""
        self.default_value = default_value
        self.is_required = is_required

    def to_dict(self) -> Dict[str, Union[str, int, float, bool]]:
        """Build dictionary object that contains the parameter metadata.

        Returns:
            Dict[str, Union[str, int, float, bool]]: dictionary representing the parameter metadata.
        """

        return {
            "Name": self.name,
            "Type": self.data_type.name,
            "Description": self.description,
            "DefaultValue": self.default_value
        }


class TableParam:
    """Table Parameter metadata class that represents the properties of a provider table parameter.

    """

    def __init__(
            self,
            name: str,
            columns: Optional[List[ColumnMeta]] = None,
            description: Optional[str] = None
    ):
        """Constructor for TableParam class.

        Args:
            name (str): name of the table parameter.
            columns (Optional[List[ColumnMeta]]): columns of the table parameter. If left blank the provider will accept
            any shape table.
            description (str): description of the table parameter.
        """
        self.name = name
        self.description = description if description is not None else ""
        self.columns = columns if columns is not None else []

    def to_dict(self) -> Dict[str, Union[str, int, float, bool]]:
        """Build dictionary object that contains the table parameter metadata.

        Returns:
            Dict[str, Union[str, int, float, bool]]: dictionary representing the table parameter metadata.
        """
        return {
            "Name": self.name,
            "Type": "Table",
            "Description": self.description,
            "Columns": [c.to_dict() for c in self.columns]
        }


class RegistrationType(Enum):
    DataProvider = 0
    DataProviderFactory = 1
    DirectProvider = 2
    SqlClient = 3
    QueryOrchestrator = 4
    FileSystem = 5


class RegistrationCategory(Enum):
    none = 0
    System = 1
    Administration = 2
    Lusid = 3
    Logs = 4
    Files = 5
    View = 6
    Testing = 7
    Utilities = 8
    MarketData = 9
    DatabaseView = 10
    Developer = 11
    Corporate = 12
    OtherData = 13


class RegistrationAttributes(Enum):
    none = 0
    Generator = 1
    Writer = 2
    DomainAlterable = 3
    RequiresConfiguration = 4


class LifeCycleStage(Enum):
    Stable = 0
    EarlyAccess = 1
    Beta = 2
    Experimental = 3
    Internal = 4
    Deprecated = 5

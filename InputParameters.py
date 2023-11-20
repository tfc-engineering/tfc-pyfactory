import enum


class ParameterType(enum.IntEnum):
    """Type enum for parameters"""
    NO_VALUE = 0,
    BOOLEAN = 1,
    INTEGER = 2,
    FLOAT = 3,
    STRING = 4,
    ARRAY = 5,
    BLOCK = 6


class Parameter:
    """A class to store a hierarchical input-parameters based on primitive types."""

    def __init__(self, name: str, value: any) -> None:
        """Basic constructor. If this is a parameter-block, supply None as the value."""
        self.name = name
        self.value = None
        self.sub_params = []  # Sub-list of Parameter
        self.n = 0

        self.setValue(value)

    def setValue(self, value):
        """Sets the value of the parameter. This could change the type of the parameter"""
        if isinstance(value, bool):
            self.type = ParameterType.BOOLEAN
            self.value = value
            self.sub_params = []
        elif isinstance(value, int):
            self.type = ParameterType.INTEGER
            self.value = value
            self.sub_params = []
        elif isinstance(value, float):
            self.type = ParameterType.FLOAT
            self.value = value
            self.sub_params = []
        elif isinstance(value, str):
            self.type = ParameterType.STRING
            self.value = value
            self.sub_params = []
        elif isinstance(value, list):
            self.type = ParameterType.ARRAY
            k = 0
            for sub_value in value:
                self.sub_params.append(Parameter(str(k), sub_value))
                k += 1
            self.value = None
        elif isinstance(value, dict):
            self.type = ParameterType.BLOCK
            for sub_name in value:
                self.addParameter(sub_name, value[sub_name])
            self.value = None
        else:
            self.type = ParameterType.NO_VALUE
            self.value = None

    def addParameter(self, name: str, value: any) -> None:
        """Adds a parameter to the list of sub-parameters."""
        # First check for duplicates
        for param in self.sub_params:
            if param.name == name:
                raise Exception(
                    f'ERROR: Parameter with name "{name}" already exists.')

        if isinstance(value, Parameter):
            self.sub_params.append(value)
        else:
            self.sub_params.append(Parameter(name, value))

    def getBooleanValue(self) -> bool:
        """Returns the boolean value of the parameter"""
        if int(self.type) > 3:
            raise Exception(f'ERROR: Cannot convert parameter "{self.name}" to bool. It is of'
                            f'type {str(self.type)}')
        return bool(self.value)

    def getIntegerValue(self) -> int:
        """Returns the integer value of the parameter"""
        if int(self.type) > 3:
            raise Exception(f'ERROR: Cannot convert parameter "{self.name}" to int. It is of'
                            f'type {str(self.type)}')
        return int(self.value)

    def getFloatValue(self) -> float:
        """Returns the float value of the parameter"""
        if int(self.type) > 3:
            raise Exception(f'ERROR: Cannot convert parameter "{self.name}" to float. It is of'
                            f'type {str(self.type)}')
        return float(self.value)

    def getStringValue(self) -> str:
        """Returns the float value of the parameter"""
        if self.type != ParameterType.STRING:
            raise Exception(f'ERROR: Cannot convert parameter "{self.name}" to str. It is of'
                            f'type {str(self.type)}')
        return float(self.value)

    def getValue(self):
        """Returns the arbitrary value of the parameter"""
        return self.value

    def getParam(self, str_or_num):
        """Returns the sub-parameter at the given index or name"""
        if isinstance(str_or_num, str):
            for sub_param in self.sub_params:
                if sub_param.name == str_or_num:
                    return sub_param
        else:
            return self.sub_params[int(str_or_num)]

        raise Exception(
            f'ERROR: Parameter "{self.name}" has no sub-parameter at {str_or_num}')

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n < len(self.sub_params):
            ret_val = self.sub_params[self.n]
            self.n += 1
            return ret_val
        else:
            raise StopIteration

    def __str__(self) -> str:
        if self.type == ParameterType.BOOLEAN:
            return "True" if self.value == True else "False"
        elif self.type == ParameterType.INTEGER or self.type == ParameterType.FLOAT:
            return str(self.value)
        elif self.type == ParameterType.STRING:
            return f'"{self.value}"'
        elif self.type == ParameterType.ARRAY:
            outstr = "["
            for index, sub_param in enumerate(self.sub_params):
                outstr += sub_param.__str__()
                if index < (len(self.sub_params) - 1):
                    outstr += ","
            outstr += "]"
            return outstr
        else:
            outstr = "{"
            for index, sub_param in enumerate(self.sub_params):
                outstr += f'"{sub_param.name}"=' + sub_param.__str__()
                if index < (len(self.sub_params) - 1):
                    outstr += ","
            outstr += "}"
            return outstr


class InputParameterTag:
    def __init__(self, tag_name: str, value: any):
        self.tag_name = tag_name
        self.value = value


class InputParameters(Parameter):
    def __init__(self):
        super().__init__("", None)

        self.tags = {}

    def addOptionalParameter(param_name: str, default_value: any, doc_string: str,
                             tags: list = []):
        for param in self.sub_params:
            raise Exception(f'ERROR: Parameter "{param_name}" already exists')
        self.addParameter(param_name, default_value)

        tag_list = []
        if param_name in self.tags:
            tag_list = self.tags[param_name]
        else:
            self.tags[param_name] = tag_list

        tag_list.append(InputParameterTag("doc_string", doc_string))
        tag_list.append(InputParameterTag("optional"))

        for tag in tags:
            tag_list.append(tag)

    def addRequiredParam(param_name: str, param_type: ParameterType, doc_string: str,
                         tags: list):
        for param in self.sub_params:
            raise Exception(f'ERROR: Parameter "{param_name}" already exists')
        self.addParameter(param_name, default_value)

        if param_type == ParameterType.BOOLEAN:
            self.addParameter(param_name, False)
        elif param_type == ParameterType.INTEGER:
            self.addParameter(param_name, 0)
        elif param_type == ParameterType.FLOAT:
            self.addParameter(param_name, 0.0)
        elif param_type == ParameterType.STRING:
            self.addParameter(param_name, "")
        elif param_type == ParameterType.ARRAY:
            self.addParameter(param_name, [])
        elif param_type == ParameterType.BLOCK:
            self.addParameter(param_name, {})

        tag_list = []
        if param_name in self.tags:
            tag_list = self.tags[param_name]
        else:
            self.tags[param_name] = tag_list

        tag_list.append(InputParameterTag("doc_string", doc_string))
        tag_list.append(InputParameterTag("required"))

        for tag in tags:
            tag_list.append(tag)

    def assignParameters(params: Parameter):
        """Assigns a parameter block to this input-parameters block"""

        # First check all the parameters are valid
        for param in params:
            is_valid = False
            for in_param in self.sub_params:
                if in_param.name == param.name:
                    is_valid = True
                    break

            if not is_valid:
                raise Exception(
                    f'ERROR: Parameter "{param.name}" is not a valid parameter.')

        # Now check params has all the required params
        for in_param in self.sub_params:
            tag_list = self.tags[in_param.name]

            for tag in tag_list:
                if tag.name == "required":
                    found = False
                    for param in params:
                        if param.name == in_param.name:
                            found = True
                            break

                    if not found:
                        raise Exception(f'ERROR: Required parameter "{in_param.name}"'
                                        'not supplied.')

        # Now assign the parameters
        for param in params:
            for in_param in self.sub_params:
                if in_param.name == param.name:
                    tag_list = self.tags[in_param.name]

                    mutable = False
                    for tag in tag_list:
                        if tag.name == "mutable":
                            mutable = True
                            break

                    if mutable:
                        in_param.setValue(param.value)
                    else:
                        if in_param.type != param.type:
                            raise Exception(f'ERROR: Attempting to assign type {str(param.type)}'
                                            f'to parameter "{in_param.name}" which is of type '
                                            f'{str(in_param.type)}')

                        in_param.setValue(param.value)

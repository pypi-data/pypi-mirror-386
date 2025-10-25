import os.path
import re
import shlex

from cmlibs.utils.zinc.field import create_field_finite_element, find_or_create_field_group
from cmlibs.zinc.context import Context
from cmlibs.zinc.field import Field
from cmlibs.zinc.status import OK as ZINC_OK

from cmlibs.importer.base import valid
from cmlibs.importer.errors import ImporterImportInvalidInputs, ImporterImportUnknownParameter, ImporterImportXYZValueError
from cmlibs.utils.zinc.general import ChangeManager, AbstractNodeDataObject, create_node


class XYZValueDatapoint(AbstractNodeDataObject):

    def __init__(self, field_names, data):
        super(XYZValueDatapoint, self).__init__(field_names)
        self._data = data


def identifier():
    return "XYZValue"


def import_data_into_region(region, inputs):
    if isinstance(inputs, list) and len(inputs) == 1:
        inputs = inputs[0]

    if not valid(inputs, parameters("input")):
        raise ImporterImportInvalidInputs(f"Invalid input given to importer: {identifier()}")

    field_module = region.getFieldmodule()
    with ChangeManager(field_module):
        data, header = _read_input_file(inputs)

        data_points = field_module.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_DATAPOINTS)
        data_template = data_points.createNodetemplate()

        field_names = []
        for key, item in header.items():
            field_names.append(key)
            if key == "coordinates":
                component_names = [e[1] for e in sorted(item)]
                datapoint_field = create_field_finite_element(field_module, key, len(component_names),
                                                              type_coordinate=True, managed=True, component_names=component_names)
            elif isinstance(data[0][item[0]], str):
                datapoint_field = field_module.createFieldStoredString()
                datapoint_field.setName(key)
            else:
                datapoint_field = create_field_finite_element(field_module, key, len(item),
                                                              type_coordinate=False, managed=True)
            data_template.defineField(datapoint_field)

        for entry in data:
            field_data = {}
            for key, values in header.items():
                setattr(XYZValueDatapoint, key, lambda self, k=key: self._data[k])
                if key == "coordinates":
                    field_data[key] = [entry[v[0]] for v in values]
                elif isinstance(entry[values[0]], str):
                    field_data[key] = entry[values[0]]
                else:
                    field_data[key] = [entry[v] for v in values]

            data_object = XYZValueDatapoint(field_names, field_data)
            create_node(field_module, data_object, node_set_name="datapoints")


def import_data(inputs, output_directory):
    output = None
    context = Context(identifier())
    region = context.getDefaultRegion()

    import_data_into_region(region, inputs)

    # Inputs has already been validated by this point so it is safe to use.
    filename_parts = os.path.splitext(os.path.basename(inputs))
    output_exf = os.path.join(output_directory, filename_parts[0] + ".exf")
    result = region.writeFile(output_exf)
    if result == ZINC_OK:
        output = output_exf

    return output


def parameters(parameter_name=None):
    importer_parameters = {
        "version": "0.1.0",
        "id": identifier(),
        "title": "XYZ List of Points + Values",
        "description":
            """
            XYZValue importer is for importing XYZ and field value data stored in space separated columns.
            The first column is the X coordinate, the second column is the Y coordinate, the
            third column is the Z coordinate. Any subsequent columns are for setting values at that location.
            A value will initially be converted to a float value and if this fails then it will be interpreted as a string.
            The '#' character can be used to indicate a comment, any text after the '#' will be ignored.
            The first line of the file may be a header line. The header line will be used to assign labels to the coordinate values
            and field names to the field values.
            If you are looking to create a multi-component field name give each column the same name and give them a suffix of
            '_1', '_2', '_3', etc. to identify the component of the field.
            """,
        "input": {
            "mimetype": "text/plain",
        },
        "output": {
            "mimetype": "text/x.vnd.abi.exf+plain",
        }
    }

    if parameter_name is not None:
        if parameter_name in importer_parameters:
            return importer_parameters[parameter_name]
        else:
            raise ImporterImportUnknownParameter(f"Importer '{identifier()}' does not have parameter: {parameter_name}")

    return importer_parameters


def _add_data_point(field_module, datapoint_field, node, row):
    field_cache = field_module.createFieldcache()
    field_cache.setNode(node)
    datapoint_field.assignReal(field_cache, row)


def _read_input_file(inputs):
    header = []
    data = []
    with open(inputs) as f:
        try:
            lines = f.readlines()
        except UnicodeDecodeError:
            raise ImporterImportXYZValueError("Point cloud data file is not valid.")

        for line in lines:
            split_line = line.split('#', 1)
            line = split_line[0].strip()
            if not line:
                continue  # Skip empty lines and comments.

            parts = shlex.split(line)
            if header is not None and len(header) == 0:
                # Test to see if first line is a header line.
                if _is_header(parts):
                    header = _parse_multi_component_header(parts)
                    continue
                else:
                    header = None

            entry = []
            try:
                x, y, z = map(float, parts[:3])
                entry.extend([x, y, z])
            except ValueError:
                raise ImporterImportXYZValueError(f"Invalid point data: {parts}")

            for part in parts[3:]:
                try:
                    entry.append(float(part))
                except ValueError:
                    entry.append(part)

            data.append(entry)

    if len(data) == 0:
        raise ImporterImportXYZValueError("Point cloud data file has no data.")

    if header is None:
        parts = ["xyz"[n] if n < 3 else f"field{n-2}" for n in range(0, len(data[0])) ]
        header = _parse_multi_component_header(parts)

    return data, header


def _is_header(parts):
    """
    Check if the line is a header line.
    A header line is defined as follows:
    The first column does not convert to a float value.
    """
    try:
        float(parts[0])
        return False
    except ValueError:
        return True


def _parse_multi_component_header(columns: list) -> dict[str, int]:
    """
    Parses a space-separated header line to find multi-component fields.

    Multi-component fields are expected to have a suffix like '_1', '_2', etc.
    This function groups them under a single base name and counts the components.

    Args:
        columns: A list of column headers.

    Returns:
        A dictionary where keys are the base field names and
        values are the integer component counts.
    """

    # This regex pattern captures two groups:
    # 1. (.+?)   - The "base name" (any character, non-greedy)
    # 2. _(\d+)$ - A literal underscore followed by one or more digits
    #             at the very end of the string.
    component_pattern = re.compile(r'(.+?)_(\d+)$')

    header_info = {}

    for index, column_name in enumerate(columns):
        # Check if the column name matches our multi-component pattern
        match = component_pattern.match(column_name)

        if match:
            # If it's a component (e.g., "Velocity_1"),
            # use the base name (e.g., "Velocity") as the key.
            base_name = match.group(1)

            # Use .get() to either get the current count or 0, then add 1
            header_info[base_name] = header_info.get(base_name, []) + [index]

        elif index < 3:
            header_info["coordinates"] = header_info.get("coordinates", []) + [(index, column_name)]
        else:
            # If it's a simple name (e.g., "X" or "Label"),
            # use the name itself as the key.
            # This also correctly handles a base name and a component
            # (e.g., "Pressure" and "Pressure_1" would result in "Pressure: 2")
            header_info[column_name] = header_info.get(column_name, []) + [index]

    return header_info

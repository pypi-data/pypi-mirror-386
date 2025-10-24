import importlib
import inspect
import json
import os
from typing import Any, Callable, Dict, List, get_type_hints
import logging

from pydantic import TypeAdapter, BaseModel

from ibm_watsonx_orchestrate.utils.utils import yaml_safe_load
from ibm_watsonx_orchestrate.utils.file_manager import safe_open
from ibm_watsonx_orchestrate.agent_builder.connections import ExpectedCredentials
from .base_tool import BaseTool
from .types import PythonToolKind, ToolSpec, ToolPermission, ToolRequestBody, ToolResponseBody, JsonSchemaObject, ToolBinding, \
    PythonToolBinding
from ibm_watsonx_orchestrate.utils.exceptions import BadRequest

_all_tools = []
logger = logging.getLogger(__name__)

JOIN_TOOL_PARAMS = {
    'original_query': str,
    'task_results': Dict[str, Any],
    'messages': List[Dict[str, Any]],
}

def _parse_expected_credentials(expected_credentials: ExpectedCredentials | dict):
    parsed_expected_credentials = []
    if expected_credentials:
        for credential in expected_credentials:
            if isinstance(credential, ExpectedCredentials):
                parsed_expected_credentials.append(credential)
            else:
                parsed_expected_credentials.append(ExpectedCredentials.model_validate(credential))
    
    return parsed_expected_credentials

class PythonTool(BaseTool):
    def __init__(self,
                fn,
                name: str = None,
                description: str = None,
                input_schema: ToolRequestBody = None,
                output_schema: ToolResponseBody = None,
                permission: ToolPermission = ToolPermission.READ_ONLY,
                expected_credentials: List[ExpectedCredentials] = None,
                display_name: str = None,
                kind: PythonToolKind = PythonToolKind.TOOL,
                spec=None
                ):
        self.fn = fn
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.permission = permission
        self.display_name = display_name
        self.kind = kind
        self.expected_credentials=_parse_expected_credentials(expected_credentials)
        self._spec = None
        if spec:
            self._spec = spec

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)
    
    @property
    def __tool_spec__(self):
        if self._spec:
            return self._spec
        
        import docstring_parser
        from langchain_core.tools.base import create_schema_from_function
        from langchain_core.utils.json_schema import dereference_refs

        if self.fn.__doc__ is not None:
            doc = docstring_parser.parse(self.fn.__doc__)
        else:
            doc = None

        _desc = self.description
        if self.description is None and doc is not None:
            _desc = doc.description

        
        spec = ToolSpec(
            name=self.name or self.fn.__name__,
            display_name=self.display_name,
            description=_desc,
            permission=self.permission
        )

        spec.binding = ToolBinding(python=PythonToolBinding(function=''))

        linux_friendly_os_cwd = os.getcwd().replace("\\", "/")
        function_binding = (inspect.getsourcefile(self.fn)
                            .replace("\\", "/")
                            .replace(linux_friendly_os_cwd+'/', '')
                            .replace('.py', '')
                            .replace('/','.') +
                            f":{self.fn.__name__}")
        spec.binding.python.function = function_binding

        sig = inspect.signature(self.fn)
        
        # If the function is a join tool, validate its signature matches the expected parameters. If not, raise error with details.
        if self.kind == PythonToolKind.JOIN_TOOL:
            _validate_join_tool_func(self.fn, sig, spec.name)

        if not self.input_schema:
            try:
                input_schema_model: type[BaseModel] = create_schema_from_function(spec.name, self.fn, parse_docstring=True)
            except:
                logger.warning("Unable to properly parse parameter descriptions due to incorrectly formatted docstring. This may result in degraded agent performance. To fix this, please ensure the docstring conforms to Google's docstring format.")
                input_schema_model: type[BaseModel] = create_schema_from_function(spec.name, self.fn, parse_docstring=False)
            input_schema_json = input_schema_model.model_json_schema()
            input_schema_json = dereference_refs(input_schema_json)

            # Convert the input schema to a JsonSchemaObject
            input_schema_obj = JsonSchemaObject(**input_schema_json)
            input_schema_obj = _fix_optional(input_schema_obj)

            spec.input_schema = ToolRequestBody(
                type='object',
                properties=input_schema_obj.properties or {},
                required=input_schema_obj.required or []
            )
        else:
            spec.input_schema = self.input_schema
        
        _validate_input_schema(spec.input_schema)

        if not self.output_schema:
            ret = sig.return_annotation
            if ret != sig.empty:
                _schema = dereference_refs(TypeAdapter(ret).json_schema())
                if '$defs' in _schema:
                    _schema.pop('$defs')
                spec.output_schema = _fix_optional(ToolResponseBody(**_schema))

                if _schema.get('type') == 'string' and _schema.get('format', None) is not None:
                    spec.output_schema.format = _schema.get('format')

            else:
                spec.output_schema = ToolResponseBody()

            if doc is not None and doc.returns is not None and doc.returns.description is not None:
                spec.output_schema.description = doc.returns.description

        else:
            spec.output_schema = ToolResponseBody()
        
         # Validate the generated schema still conforms to the requirement for a join tool
        if self.kind == PythonToolKind.JOIN_TOOL:
            if not spec.is_custom_join_tool():
                raise ValueError(f"Join tool '{spec.name}' does not conform to the expected join tool schema. Please ensure the input schema has the required fields: {JOIN_TOOL_PARAMS.keys()} and the output schema is a string.")

        self._spec = spec
        return spec
    
    @staticmethod
    def from_spec(file: str) -> 'PythonTool':
        with safe_open(file, 'r') as f:
            if file.endswith('.yaml') or file.endswith('.yml'):
                spec = ToolSpec.model_validate(yaml_safe_load(f))
            elif file.endswith('.json'):
                spec = ToolSpec.model_validate(json.load(f))
            else:
                raise BadRequest('file must end in .json, .yaml, or .yml')

        if spec.binding.python is None:
            raise BadRequest('failed to load python tool as the tool had no python binding')

        [module, fn_name] = spec.binding.python.function.split(':')
        fn = getattr(importlib.import_module(module), fn_name)

        return PythonTool(fn=fn, spec=spec)

    def __repr__(self):
        return f"PythonTool(fn={self.__tool_spec__.binding.python.function}, name='{self.__tool_spec__.name}', display_name='{self.__tool_spec__.display_name or ''}', description='{self.__tool_spec__.description}')"

    def __str__(self):
        return self.__repr__()

def _fix_optional(schema):
    if schema.properties is None:
        return schema
    # Pydantic tends to create types of anyOf: [{type: thing}, {type: null}] instead of simply
    # while simultaneously marking the field as required, which can be confusing for the model.
    # This removes union types with null and simply marks the field as not required
    not_required = []
    replacements = {}
    if schema.required is None:
        schema.required = []
    for k, v in schema.properties.items():
        # Simple null type & required -> not required
        if v.type == 'null' and k in schema.required:
            not_required.append(k)
        # Optional with null & required
        if v.anyOf is not None and [x for x in v.anyOf if x.type == 'null']:
            if k in schema.required:
            # required with default -> not required 
            # required without default -> required & remove null from union
                if v.default:
                    not_required.append(k)
                else:
                    v.anyOf = list(filter(lambda x: x.type != 'null', v.anyOf))
                if len(v.anyOf) == 1:
                    replacements[k] = v.anyOf[0]
            else:
            # not required with default -> no change
            # not required without default -> means default input is 'None'
                v.default = v.default if v.default else 'null'


    schema.required = list(filter(lambda x: x not in not_required, schema.required if schema.required is not None else []))
    for k, v in replacements.items():
        combined = {
            **schema.properties[k].model_dump(exclude_unset=True, exclude_none=True),
            **v.model_dump(exclude_unset=True, exclude_none=True)
        }
        schema.properties[k] = JsonSchemaObject(**combined)
        schema.properties[k].anyOf = None
        
    for k in schema.properties.keys():
        if schema.properties[k].type == 'object':
            schema.properties[k] = _fix_optional(schema.properties[k])

    return schema

def _validate_input_schema(input_schema: ToolRequestBody) -> None:
    props = input_schema.properties
    for prop in props:
        property_schema = props.get(prop)
        if not (property_schema.type or property_schema.anyOf):
            logger.warning(f"Missing type hint for tool property '{prop}' defaulting to 'str'. To remove this warning add a type hint to the property in the tools signature. See Python docs for guidance: https://docs.python.org/3/library/typing.html")

def _validate_join_tool_func(fn: Callable, sig: inspect.Signature | None = None, name: str | None = None) -> None:
    if sig is None:
        sig = inspect.signature(fn)
    if name is None:
        name = fn.__name__
    
    params = sig.parameters
    type_hints = get_type_hints(fn)
    
    # Validate parameter order
    actual_param_names = list(params.keys())
    expected_param_names = list(JOIN_TOOL_PARAMS.keys())
    if actual_param_names[:len(expected_param_names)] != expected_param_names:
        raise ValueError(
            f"Join tool function '{name}' has incorrect parameter names or order. Expected: {expected_param_names}, got: {actual_param_names}"
        )
    
    # Validate the type hints
    for param, expected_type in JOIN_TOOL_PARAMS.items():
        if param not in type_hints:
            raise ValueError(f"Join tool function '{name}' is missing type for parameter '{param}'")
        actual_type = type_hints[param]
        if actual_type != expected_type:
            raise ValueError(f"Join tool function '{name}' has incorrect type for parameter '{param}'. Expected {expected_type}, got {actual_type}")

def tool(
    *args,
    name: str = None,
    description: str = None,
    input_schema: ToolRequestBody = None,
    output_schema: ToolResponseBody = None,
    permission: ToolPermission = ToolPermission.READ_ONLY,
    expected_credentials: List[ExpectedCredentials] = None,
    display_name: str = None,
    kind: PythonToolKind = PythonToolKind.TOOL,
) -> Callable[[{__name__, __doc__}], PythonTool]:
    """
    Decorator to convert a python function into a callable tool.

    :param name: the agent facing name of the tool (defaults to the function name)
    :param description: the description of the tool (used for tool routing by the agent)
    :param input_schema: the json schema args to the tool
    :param output_schema: the response json schema for the tool
    :param permission: the permissions needed by the user of the agent to invoke the tool
    :return:
    """
    # inspiration: https://github.com/pydantic/pydantic/blob/main/pydantic/validate_call_decorator.py
    def _tool_decorator(fn):
        t = PythonTool(
            fn=fn,
            name=name,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
            permission=permission,
            expected_credentials=expected_credentials,
            display_name=display_name,
            kind=kind
        )
            
        _all_tools.append(t)
        return t

    if len(args) == 1 and callable(args[0]):
        return _tool_decorator(args[0])
    return _tool_decorator


def get_all_python_tools():
    return [t for t in _all_tools]

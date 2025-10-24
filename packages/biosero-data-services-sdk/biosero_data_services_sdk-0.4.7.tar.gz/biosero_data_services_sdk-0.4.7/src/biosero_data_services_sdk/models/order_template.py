import json
from copy import deepcopy
from pathlib import Path
from typing import Self
from typing import override

from pydantic import BaseModel
from pydantic import Field
from pydantic import JsonValue
from pydantic import field_serializer

from .base import DataServicesModel
from .identity import DataServicesIdentityProperty


class OrderParameter(DataServicesIdentityProperty):
    pass


def parse_input_parameters_from_response(response: dict[str, JsonValue]) -> list[OrderParameter] | None:
    assert "inputParameters" in response, f"Order response must contain 'inputParameters' field: {response}"
    input_parameters = response["inputParameters"]
    assert isinstance(input_parameters, list | type(None)), (
        f"'inputParameters' field must be a list or None, got {type(input_parameters)} for {input_parameters}"
    )
    if input_parameters is None:
        return None
    input_parameters_pydantic: list[OrderParameter] = []
    for parameter in input_parameters:
        assert isinstance(parameter, dict), (
            f"Each parameter in 'inputParameters' must be a dict, got {type(parameter)} for {parameter}"
        )
        input_parameters_pydantic.append(OrderParameter.model_validate(parameter))
    return input_parameters_pydantic


class OrderTemplateScript(DataServicesModel):
    name: str
    language: str  # TODO: theoretically this is an Enum...but we don't actually have the schema from BioSero
    code: str

    @override
    @classmethod
    def from_api_response(cls, response: dict[str, JsonValue]) -> Self:
        assert "name" in response, "OrderTemplateScript response must contain 'name' field"
        name = response["name"]
        assert isinstance(name, str), f"'name' field must be a string, got {type(name)} for {name}"

        assert "language" in response, "OrderTemplateScript response must contain 'language' field"
        language = response["language"]
        assert isinstance(language, str), f"'language' field must be a string, got {type(language)} for {language}"

        assert "code" in response, "OrderTemplateScript response must contain 'code' field"
        code = response["code"]
        assert isinstance(code, str), f"'code' field must be a string, got {type(code)} for {code}"

        obj = cls(name=name, language=language, code=code)
        obj.set_full_response_dict(response)
        return obj


class OrderTemplateWorkflow(DataServicesModel):
    name: str
    scripts: list[OrderTemplateScript] = Field(default_factory=list[OrderTemplateScript])

    @field_serializer("scripts")
    def serialize_scripts(self, courses: list[OrderTemplateScript]) -> list[dict[str, JsonValue]]:
        return [script.model_dump(by_alias=True) for script in courses]

    def model_to_pass_to_api_for_update(self) -> str:
        out_dict = self.model_dump(by_alias=True)
        if hasattr(self, "_full_response_dict"):
            for key, value in self.full_response_dict.items():
                if key not in out_dict:
                    out_dict[key] = value
        return json.dumps(out_dict)

    @override
    @classmethod
    def from_api_response(cls, response: dict[str, JsonValue]) -> Self:
        assert "scripts" in response, "OrderTemplateWorkflow response must contain 'scripts' field"
        scripts = response["scripts"]
        assert isinstance(scripts, list), f"'scripts' field must be a list, got {type(scripts)} for {scripts}"
        scripts_pydantic: list[OrderTemplateScript] = []
        for script in scripts:
            assert isinstance(script, dict), f"Each script in 'scripts' must be a dict, got {type(script)} for {script}"
            scripts_pydantic.append(OrderTemplateScript.from_api_response(script))

        assert "name" in response, "OrderTemplateWorkflow response must contain 'name' field"
        name = response["name"]
        assert isinstance(name, str), f"'name' field must be a string, got {type(name)} for {name}"

        obj = cls(name=name, scripts=scripts_pydantic)
        obj.set_full_response_dict(response)
        return obj


def _sort_nested_dict(json_value: JsonValue) -> JsonValue:
    """Recursively sort all dictionary keys alphabetically for deterministic JSON file output.

    Fields in the priority list will always come first (in that order) to make reviewing the file easier for humans
    """
    if isinstance(json_value, dict):
        # First create sorted result with all keys
        result: dict[str, JsonValue] = {}
        # Priority fields first (if they exist)
        priority_fields = [
            "name",
            "description",
            "helpText",
            "value",
            "defaultValue",
            "category",
            "valueType",
            "isDisabled",
            "isPausePointSet",
            "isAsync",
            "children",
        ]
        for field in priority_fields:
            if field in json_value:
                result[field] = _sort_nested_dict(json_value[field])

        # Then add all other keys in alphabetical order
        for key in sorted(json_value.keys()):
            if key not in priority_fields:
                result[key] = _sort_nested_dict(json_value[key])
        return result
    if isinstance(json_value, list):
        return [_sort_nested_dict(i) for i in json_value]
    return json_value


ORDER_TEMPLATE_SCRIPTS_SUBFOLDER_NAME = "scripts"
ORDER_TEMPLATE_JSON_FILENAME = "order_template.json"


class OrderTemplateDumpedFolderInfo(BaseModel):
    folder_path: Path
    file_paths: set[Path]


class OrderTemplate(DataServicesModel):
    name: str
    description: str | None = None
    input_parameters: list[OrderParameter] | None = Field(default=None, serialization_alias="inputParameters")
    workflow: OrderTemplateWorkflow | None
    is_hidden: bool = Field(serialization_alias="isHidden")

    @field_serializer("workflow")
    def serialize_workflow(self, workflow: OrderTemplateWorkflow | None) -> str | None:
        if workflow is None:
            return None
        return workflow.model_to_pass_to_api_for_update()

    def model_to_pass_to_api_for_update(self) -> dict[str, JsonValue]:
        out_dict = self.model_dump(by_alias=True)
        if hasattr(self, "_full_response_dict"):
            for key, value in self.full_response_dict.items():
                if key not in out_dict:
                    out_dict[key] = value
        return out_dict

    @override
    @classmethod
    def from_api_response(cls, response: dict[str, JsonValue]) -> Self:
        assert "name" in response, "OrderTemplate response must contain 'name' field"
        name = response["name"]
        assert isinstance(name, str), f"'name' field must be a string, got {type(name)} for {name}"

        assert "description" in response, "OrderTemplate response must contain 'description' field"
        description = response["description"]
        assert isinstance(description, (str, type(None))), (
            f"'description' field must be a string or None, got {type(description)} for {description}"
        )

        assert "isHidden" in response, "OrderTemplate response must contain 'isHidden' field"
        is_hidden = response["isHidden"]
        assert isinstance(is_hidden, bool), f"'isHidden' field must be a boolean, got {type(is_hidden)} for {is_hidden}"

        assert "workflow" in response, "OrderTemplate response must contain 'workflow' field"
        workflow_value = response["workflow"]
        assert isinstance(workflow_value, (str, type(None))), (
            f"'workflow' field must be a string or None, got {type(workflow_value)} for {workflow_value}"
        )
        workflow_pydantic: OrderTemplateWorkflow | None = None
        if workflow_value is not None:
            workflow_pydantic = OrderTemplateWorkflow.from_api_response(json.loads(workflow_value))

        obj = cls(
            name=name,
            description=description,
            workflow=workflow_pydantic,
            is_hidden=is_hidden,
            input_parameters=parse_input_parameters_from_response(response),
        )
        obj.set_full_response_dict(response)
        return obj

    @classmethod
    def from_folder(cls, folder: Path) -> Self:
        with (folder / ORDER_TEMPLATE_JSON_FILENAME).open("r") as f:
            data = json.load(f)
            if data["workflow"] is not None:
                data["workflow"] = json.dumps(data["workflow"])
        template = cls.from_api_response(data)
        if template.workflow is not None:
            for script in template.workflow.scripts:
                script_name = script.name
                script_path = folder / ORDER_TEMPLATE_SCRIPTS_SUBFOLDER_NAME / f"{script_name}.csx"
                with script_path.open("r") as f:
                    code = f.read()
                line_feed_code = code.replace("\r\n", "\n").replace(
                    "\r", "\n"
                )  # force to CRLF that BioSero (likely) expects
                crlf_code = line_feed_code.replace("\n", "\r\n")
                script.code = crlf_code

        return template

    def dump_to_folder(
        self, root_folder: Path, *, create_subfolder_using_template_name: bool = False
    ) -> OrderTemplateDumpedFolderInfo:
        copied_self = deepcopy(self)  # don't alter this actual instance when rearranging it to dump to folder
        file_paths: set[Path] = set()
        if create_subfolder_using_template_name:
            name_for_folder = self.name
            if name_for_folder.endswith(" "):
                name_for_folder = name_for_folder[:-1] + "_trailing_space_replaced"
            if name_for_folder.startswith(" "):
                name_for_folder = "leading_space_replaced_" + name_for_folder[1:]
            root_folder = root_folder / name_for_folder
        root_folder.mkdir(parents=True, exist_ok=True)
        scripts_folder = root_folder / ORDER_TEMPLATE_SCRIPTS_SUBFOLDER_NAME
        if copied_self.workflow is not None:
            for script in copied_self.workflow.scripts:
                scripts_folder.mkdir(exist_ok=True)
                script_path = scripts_folder / f"{script.name}.csx"
                file_paths.add(script_path)
                with (
                    script_path.open(
                        "w",
                        newline="",  # we're already being very explicit already about line endings, and we don't want Python doing anything extra under the hood on Windows vs Linux
                    ) as f
                ):
                    _ = f.write(script.code)
                script.code = f"stored in {ORDER_TEMPLATE_SCRIPTS_SUBFOLDER_NAME}/{script.name}.csx"
        order_template_path = root_folder / ORDER_TEMPLATE_JSON_FILENAME
        file_paths.add(order_template_path)
        with (order_template_path).open("w") as f:
            api_model = copied_self.model_to_pass_to_api_for_update()
            if copied_self.workflow is not None:
                workflow = api_model["workflow"]
                assert isinstance(workflow, str), (
                    f"'workflow' field must be a string, got {type(workflow)} for {workflow}"
                )
                api_model["workflow"] = json.loads(workflow)
            json.dump(_sort_nested_dict(api_model), f, indent=2)
        return OrderTemplateDumpedFolderInfo(folder_path=root_folder, file_paths=file_paths)

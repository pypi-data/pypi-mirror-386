import json
from abc import ABCMeta
from typing import List

from loguru import logger

from flowllm.op.base_async_op import BaseAsyncOp
from flowllm.schema.tool_call import ToolCall, ParamAttrs


class BaseAsyncToolOp(BaseAsyncOp, metaclass=ABCMeta):

    def __init__(self,
                 enable_print_output: bool = True,
                 tool_index: int = 0,
                 save_answer: bool = False,
                 input_schema_mapping: dict = None,
                 output_schema_mapping: dict = None,
                 **kwargs):
        super().__init__(**kwargs)

        self.enable_print_output: bool = enable_print_output
        self.tool_index: int = tool_index
        self.save_answer: bool = save_answer
        self.input_schema_mapping: dict | None = input_schema_mapping  # map key to context
        self.output_schema_mapping: dict | None = output_schema_mapping  # map key to context

        self._tool_call: ToolCall | None = None
        self.input_dict: dict = {}
        self.output_dict: dict = {}

    def build_tool_call(self) -> ToolCall:
        return ToolCall(**{
            "description": "",
            "input_schema": {}
        })

    @property
    def tool_call(self):
        if self._tool_call is None:
            self._tool_call = self.build_tool_call()
            self._tool_call.name = self.short_name
            self._tool_call.index = self.tool_index

            if not self._tool_call.output_schema:
                self._tool_call.output_schema = {
                    f"{self.short_name}_result": ParamAttrs(
                        type="str",
                        description=f"The execution result of the {self.short_name}")
                }

        return self._tool_call

    @property
    def output_keys(self) -> str | List[str]:
        output_keys = []
        for name, attrs in self.tool_call.output_schema.items():
            if name not in output_keys:
                output_keys.append(name)

        if len(output_keys) == 1:
            return output_keys[0]
        else:
            return output_keys

    @property
    def output(self) -> str:
        if isinstance(self.output_keys, str):
            return self.output_dict[self.output_keys]
        else:
            raise NotImplementedError("use `output_dict` to get result")

    def set_result(self, value = "", key: str = ""):
        if isinstance(self.output_keys, str):
            self.output_dict[self.output_keys] = value
        else:
            self.output_dict[key] = value

    def set_results(self, **kwargs):
        for k, v in kwargs.items():
            self.set_result(v, k)

    async def async_before_execute(self):
        for name, attrs in self.tool_call.input_schema.items():
            context_key = name
            if self.input_schema_mapping and name in self.input_schema_mapping:
                context_key = self.input_schema_mapping[name]
            if self.tool_index != 0:
                context_key += f".{self.tool_index}"

            if context_key in self.context:
                self.input_dict[name] = self.context[context_key]
            elif attrs.required:
                raise ValueError(f"{self.name}: {name} is required")

    async def async_after_execute(self):
        for name, value in self.output_dict.items():
            context_key = name
            if self.output_schema_mapping and name in self.output_schema_mapping:
                context_key = self.output_schema_mapping[name]
            if self.tool_index != 0:
                context_key += f".{self.tool_index}"

            logger.info(f"{self.name} set context key={context_key}")
            self.context[context_key] = value

        if self.save_answer:
            if isinstance(self.output_keys, str):
                self.context.response.answer = self.output_dict.get(self.output_keys, "")
            else:
                self.context.response.answer = json.dumps(self.output_dict, ensure_ascii=False)

        if self.enable_print_output:
            if self.tool_index == 0:
                logger.info(f"{self.name}.output_dict={self.output_dict}")
            else:
                logger.info(f"{self.name}.{self.tool_index}.output_dict={self.output_dict}")

    async def async_default_execute(self):
        if isinstance(self.output_keys, str):
            self.output_dict[self.output_keys] = f"{self.name} execution failed!"
        else:
            for output_key in self.output_keys:
                self.output_dict[output_key] = f"{self.name} execution failed!"

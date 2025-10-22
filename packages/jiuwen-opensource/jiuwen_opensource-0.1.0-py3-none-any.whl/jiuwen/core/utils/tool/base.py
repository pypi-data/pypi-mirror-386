#!/usr/bin/python3.11
# coding: utf-8
# Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved

from abc import abstractmethod

from jiuwen.core.utils.llm.messages import ToolInfo
from jiuwen.core.utils.tool.constant import Input, Output


class Tool:
    """tool class that defined the data types and content for LLM modules"""
    def __init__(self):
        pass

    @abstractmethod
    def invoke(self, inputs: Input, **kwargs) -> Output:
        """invoke the tool"""
        pass

    @abstractmethod
    async def ainvoke(self, inputs: Input, **kwargs) -> Output:
        """async invoke the tool"""
        pass

    @abstractmethod
    def get_tool_info(self) -> ToolInfo:
        """get tool info"""
        pass


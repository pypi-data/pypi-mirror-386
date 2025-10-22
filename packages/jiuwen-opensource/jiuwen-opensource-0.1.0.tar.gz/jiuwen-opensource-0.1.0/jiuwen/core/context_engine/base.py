#!/usr/bin/python3.10
# coding: utf-8
# Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved

from enum import Enum
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Union, Dict, Any, Optional, List

from jiuwen.core.utils.llm.messages import BaseMessage
from jiuwen.core.utils.prompt.template.template import Template


class ContextVariable(BaseModel):
    name: str = Field(default=...)
    description: str = Field(default="")
    value: Optional[str] = Field(default=None)
    default_value: Optional[str] = Field(default=None)

    def get_value(self):
        return self.value if self.value else self.default_value


class ContextOwner(BaseModel):
    agent_id: str = Field(default="")
    workflow_id: str = Field(default="")
    session_id: str = Field(default="")
    app_id: str = Field(default="")
    user_id: str = Field(default="")

    def __hash__(self) -> int:
        return hash((self.agent_id, self.workflow_id, self.session_id, self.app_id, self.user_id))

    def __eq__(self, other: "ContextOwner") -> bool:
        if isinstance(other, ContextOwner):
            return self.agent_id == other.agent_id and self.workflow_id == other.workflow_id \
                and self.session_id == other.session_id and self.app_id == other.app_id
        return False

    def __contains__(self, other: "ContextOwner"):
        if isinstance(other, ContextOwner):
            return (not self.session_id or self.session_id == other.session_id) \
                    and (not self.agent_id or self.agent_id == self.agent_id) \
                    and (not self.workflow_id or self.workflow_id == self.workflow_id)
        return False


class Context(ABC):
    @abstractmethod
    def batch_add_messages(self,
                           messages: Union[List[Dict], List[BaseMessage]],
                           tags: Optional[Dict[str, str]] = None):
        pass

    @abstractmethod
    def add_message(self,
                    message: BaseMessage,
                    tags: Optional[Dict[str, str]] = None):
        pass

    @abstractmethod
    def get_messages(self,
                    num: int = -1,
                    tags: Optional[Dict[str, str]] = None) -> List[BaseMessage]:
        pass

    @abstractmethod
    def get_latest_message(self,
                           role: str = None) -> Union[BaseMessage, None]:
        pass

    @abstractmethod
    def get_variable(self,
                     name: str) -> Optional[ContextVariable]:
        pass

    @abstractmethod
    def set_variable(self,
                     name: str,
                     value: ContextVariable):
        pass

    @abstractmethod
    def assemble(self,
                 message: Union[str, BaseMessage, List[BaseMessage]],
                 variables: Optional[Dict[str, str]] = None,
                 **kwargs) -> Union[str, BaseMessage, List[BaseMessage]]:
        pass

    @abstractmethod
    def assemble_by_pipeline(self,
                             message: Union[str, BaseMessage, List[BaseMessage]],
                             variables: Optional[Dict[str, str]] = None,
                             **kwargs) -> Union[str, BaseMessage, List[BaseMessage]]:
        pass

    @abstractmethod
    def get_compressed_history(self,
                               config: Optional[Dict[str, Any]] = None,
                               owner: Optional[ContextOwner] = None) -> List[BaseMessage]:
        pass


class ContextType(Enum):
    USER_INPUT = "user_input"
    SYSTEM_PROMPT = "system_prompt"
    VARIABLES = "variables"
    CHAT_HISTORY = "chat_history"
    MEMORY = "memory"
    TOOLS = "tools"
    FULL_PROMPT = "full_prompt"


class ContextWindow(BaseModel):
    user_input: Union[str, Dict] = Field(default="")
    prompt: Template = Field(default=Template(content=""))
    variables: Dict[str, ContextVariable] = Field(default={})
    chat_history: Union[str, List[BaseMessage]] = Field(default="")
    memory: Optional[Any] = Field(default=None)
    tools: Union[str, Dict] = Field(default="")
    full_prompt: Union[str, BaseMessage, List[BaseMessage]] = Field(default="")

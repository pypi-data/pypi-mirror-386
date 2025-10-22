from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field

from jiuwen.agent.common.enum import ControllerType
from jiuwen.agent.config.base import AgentConfig
from jiuwen.core.component.common.configs.model_config import ModelConfig


class ConstrainConfig(BaseModel):
    reserved_max_chat_rounds: int = Field(default=10)
    max_iteration: int = Field(default=5)


class IntentDetectionConfig(BaseModel):
    intent_detection_template: List[Dict] = Field(default_factory=list)
    default_class: str = Field(default="分类1")
    enable_input: bool = Field(default=True)
    enable_history: bool = Field(default=False)
    chat_history_max_turn: int = Field(default=5)
    category_list: List[str] = Field(default_factory=list)
    user_prompt: str = Field(default="")
    example_content: List[str] = Field(default_factory=list)


class ReActAgentConfig(AgentConfig):
    controller_type: ControllerType = Field(default=ControllerType.ReActController)
    model: Optional[ModelConfig] = Field(default=None)
    prompt_template_name: str = Field(default="react_system_prompt")
    prompt_template: List[Dict] = Field(default_factory=list)
    constrain: ConstrainConfig = Field(default=ConstrainConfig())
    # intent_detection_config: IntentDetectionConfig = Field(default=IntentDetectionConfig())

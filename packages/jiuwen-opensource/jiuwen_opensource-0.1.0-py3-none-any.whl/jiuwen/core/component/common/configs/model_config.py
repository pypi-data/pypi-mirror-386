#!/usr/bin/python3.10
# coding: utf-8
# Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved
from dataclasses import field, dataclass

from jiuwen.core.utils.llm.base import BaseModelInfo


@dataclass
class ModelConfig:
    model_provider: str
    model_info: BaseModelInfo = field(default_factory=BaseModelInfo)

#!/usr/bin/python3.11
# coding: utf-8
# Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved

from typing import TypeVar

Input = TypeVar('Input', contravariant=True)
Output = TypeVar('Output', contravariant=True)

HTTP_METHOD = {"GET", "POST", "HEAD", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH", "TRACE"}
MAX_RESULT_SIZE = 10 * 1024 * 1024
REQUEST_TIMEOUT = 60

# RestFul Res
ERR_CODE = "errCode"
ERR_MESSAGE = "errMessage"
RESTFUL_DATA = "data"
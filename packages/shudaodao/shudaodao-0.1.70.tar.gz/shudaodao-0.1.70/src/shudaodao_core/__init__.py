#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：李锋
# @Software ：PyCharm
# @Date     ：2025/8/26 下午12:11
# @Desc     ：

# 其他类库的引用
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Relationship, SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from .app.base_app import Application
from .auth.auth_router import AuthRouter
from .config.app_config import AppConfig
from .config.running_config import RunningConfig
from .controller.generic_controller import GenericController
from .controller.router_config import RouterConfig
from .controller.table_controller import AuthController
from .engine.database_engine import DatabaseEngine
from .engine.disk_engine import DiskEngine
from .engine.redis_engine import RedisEngine
from .enums.str_int import EnumStr, EnumInt
from .exception.service_exception import (
    AuthException,
    LoginException,
    PermissionException,
    ServiceErrorException,
    DataNotFoundException,
    ValueException
)
from .generate.config import GeneratorConfig
from .logger.logging_ import logging
from .schemas.query_request import QueryRequest
from .schemas.response import BaseResponse
from .services.auth_service import AuthService
from .services.data_service import DataService
from .services.enum_service import EnumService
from .services.generate_service import GeneratorService
from .services.query_service import QueryService
from .services.session_service import AsyncSessionService
from .sqlmodel_ext.field import Field
from .utils.core_utils import CoreUtil
from .utils.generate_unique_id import get_primary_str, get_primary_id
from .utils.response_utils import ResponseUtil

__all__ = [
    # FastAPI & SQLModel 快捷导出
    "Depends",
    "SQLModel",
    "Relationship",
    "create_engine",
    "create_async_engine",
    "AsyncSession",
    # SQLModel.Field 的封装
    "Field",

    # 核心应用与配置
    "Application",
    "AppConfig",
    "RunningConfig",

    # 路由与控制器
    "AuthRouter",
    "RouterConfig",
    "GenericController",
    "AuthController",

    # 引擎
    "DatabaseEngine",
    "DiskEngine",
    "RedisEngine",

    # 枚举
    "EnumStr",
    "EnumInt",

    # 异常
    "AuthException",
    "LoginException",
    "PermissionException",
    "ServiceErrorException",
    "DataNotFoundException",
    "ValueException",

    # 生成器相关
    "GeneratorConfig",
    "GeneratorService",

    # 日志
    "logging",

    # 请求与响应
    "QueryRequest",
    "BaseResponse",

    # 服务类
    "AuthService",
    "DataService",
    "QueryService",
    "AsyncSessionService",
    "EnumService",

    # 工具类与函数
    "CoreUtil",
    "ResponseUtil",
    "get_primary_str",
    "get_primary_id",
]

import asyncio
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar, cast

import singleton
from fastapi import APIRouter, BackgroundTasks, Query, Request
from pydantic import BaseModel

from .core.config import Settings
from .core.exceptions import BaseHTTPException
from .models import BaseEntity
from .schemas import BaseEntitySchema, PaginatedResponse
from .tasks import TaskStatusEnum

# Define a type variable
T = TypeVar("T", bound=BaseEntity)
TS = TypeVar("TS", bound=BaseEntitySchema)
TSCHEMA = TypeVar("TSCHEMA", bound=BaseModel)


class AbstractBaseRouter(metaclass=singleton.Singleton):
    model: type[T]  # type: ignore
    schema: type[TS] | None  # type: ignore

    unique_per_user: bool = False
    create_mine_if_not_found: bool = False

    def __init__(
        self,
        *,
        model: type[T] | None = None,
        schema: type[TS] | None = None,
        user_dependency: Callable[[Request], Any] | None = None,
        prefix: str | None = None,
        tags: list[str] | None = None,
        **kwargs: object,
    ) -> None:
        if model is None:
            if self.model is None:
                raise ValueError(
                    f"model is required in {self.__class__.__name__} "
                    "router class"
                )
        else:
            self.model = model
        if schema is None:
            if self.schema is None:
                raise ValueError(
                    f"schema is required in {self.__class__.__name__} "
                    "router class"
                )
        else:
            self.schema = schema

        self.user_dependency = user_dependency
        if prefix is None:
            prefix = f"/{self.model.__name__.lower()}s"
        if tags is None:
            tags = [self.model.__name__]

        self.router = APIRouter(
            prefix=prefix, tags=cast(list[str | Enum], tags), **kwargs
        )

        self.config_schemas(self.schema, **kwargs)
        self.config_routes(**kwargs)

    def config_schemas(self, schema: TS, **kwargs: object) -> None:
        self.schema = schema
        self.list_item_schema = kwargs.get("list_item_schema", schema)
        self.list_response_schema = kwargs.get(
            "list_response_schema", PaginatedResponse[self.list_item_schema]
        )
        self.retrieve_response_schema = kwargs.get(
            "retrieve_response_schema", schema
        )
        self.create_response_schema = kwargs.get(
            "create_response_schema", schema
        )
        self.update_response_schema = kwargs.get(
            "update_response_schema", schema
        )
        self.delete_response_schema = kwargs.get(
            "delete_response_schema", schema
        )

        self.create_request_schema = kwargs.get(
            "create_request_schema", schema
        )
        self.update_request_schema = kwargs.get(
            "update_request_schema", schema
        )

    def config_routes(
        self,
        *,
        prefix: str = "",
        list_route: bool = True,
        retrieve_route: bool = True,
        create_route: bool = True,
        update_route: bool = True,
        delete_route: bool = True,
        statistics_route: bool = False,
        mine_route: bool = False,
        **kwargs: object,
    ) -> None:
        prefix = prefix.strip("/")
        prefix = f"/{prefix}" if prefix else ""

        if list_route:
            self.router.add_api_route(
                f"{prefix}",
                self.list_items,
                methods=["GET"],
                response_model=self.list_response_schema,
                status_code=200,
            )

        if mine_route:
            self.router.add_api_route(
                f"{prefix}/mine",
                self.mine_items,
                methods=["GET"],
                response_model=(
                    self.retrieve_response_schema
                    if self.unique_per_user
                    else self.list_response_schema
                ),
                status_code=200,
            )

        if statistics_route:
            self.router.add_api_route(
                f"{prefix}/statistics",
                self.statistics,
                methods=["GET"],
            )

        if retrieve_route:
            self.router.add_api_route(
                f"{prefix}/{{uid:str}}",
                self.retrieve_item,
                methods=["GET"],
                response_model=self.retrieve_response_schema,
                status_code=200,
            )

        if create_route:
            self.router.add_api_route(
                f"{prefix}",
                self.create_item,
                methods=["POST"],
                response_model=self.create_response_schema,
                status_code=201,
            )

        if update_route:
            self.router.add_api_route(
                f"{prefix}/{{uid:str}}",
                self.update_item,
                methods=["PATCH"],
                response_model=self.update_response_schema,
                status_code=200,
            )

        if delete_route:
            self.router.add_api_route(
                f"{prefix}/{{uid:str}}",
                self.delete_item,
                methods=["DELETE"],
                response_model=self.delete_response_schema,
            )

    async def get_item(
        self,
        uid: str,
        *,
        user_id: str | None = None,
        tenant_id: str | None = None,
        **kwargs: object,
    ) -> T:
        item = await self.model.get_item(
            uid=uid,
            user_id=user_id,
            tenant_id=tenant_id,
            **kwargs,
        )
        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message={
                    "en": f"{self.model.__name__.capitalize()} not found"
                },
            )
        return item

    async def get_user(
        self, request: Request, **kwargs: object
    ) -> object | None:
        if self.user_dependency is None:
            return None
        if asyncio.iscoroutinefunction(self.user_dependency):
            return await self.user_dependency(request)
        return self.user_dependency(request)

    async def get_user_id(
        self, request: Request, **kwargs: object
    ) -> str | None:
        user = await self.get_user(request)
        user_id = user.uid if user else None
        return user_id

    async def _statistics(
        self,
        request: Request,
        created_at_from: datetime | None = None,
        created_at_to: datetime | None = None,
        **kwargs: object,
    ) -> dict:
        params: dict[str, Any] = dict(request.query_params)
        if "is_deleted" in params:
            params["is_deleted"] = params["is_deleted"].lower() == "true"

        return {
            "total": await self.model.total_count(**params, **kwargs),
            **params,
        }

    async def statistics(
        self,
        request: Request,
        created_at_from: datetime | None = None,
        created_at_to: datetime | None = None,
    ) -> dict:
        return await self._statistics(
            request=request,
            created_at_from=created_at_from,
            created_at_to=created_at_to,
        )

    async def _list_items(
        self,
        request: Request,
        offset: int = 0,
        limit: int = 10,
        **kwargs: object,
    ) -> PaginatedResponse[TS]:
        user_id = kwargs.pop("user_id", await self.get_user_id(request))
        limit = max(1, min(limit, Settings.page_max_limit))

        items, total = await self.model.list_total_combined(
            user_id=user_id,
            offset=offset,
            limit=limit,
            **kwargs,
        )
        items_in_schema = [
            self.list_item_schema(**item.model_dump()) for item in items
        ]

        return PaginatedResponse(
            items=items_in_schema,
            total=total,
            offset=offset,
            limit=limit,
        )

    async def list_items(
        self,
        request: Request,
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=Settings.page_max_limit),
        created_at_from: datetime | None = None,
        created_at_to: datetime | None = None,
    ) -> PaginatedResponse[TS]:
        return await self._list_items(
            request=request,
            offset=offset,
            limit=limit,
            created_at_from=created_at_from,
            created_at_to=created_at_to,
        )

    async def retrieve_item(
        self,
        request: Request,
        uid: str,
    ) -> T:
        user_id = await self.get_user_id(request)
        item = await self.get_item(uid=uid, user_id=user_id)
        return item

    async def create_item(
        self,
        request: Request,
        data: dict,
    ) -> T:
        user_id = await self.get_user_id(request)
        if isinstance(data, BaseModel):
            data = data.model_dump()
        item = await self.model.create_item({**data, "user_id": user_id})
        return item

    async def update_item(
        self,
        request: Request,
        uid: str,
        data: dict,
    ) -> T:
        user_id = await self.get_user_id(request)
        if isinstance(data, BaseModel):
            data = data.model_dump(exclude_unset=True)
        item = await self.get_item(uid=uid, user_id=user_id)
        item = await self.model.update_item(item, data)
        return item

    async def delete_item(
        self,
        request: Request,
        uid: str,
    ) -> T:
        user_id = await self.get_user_id(request)
        item = await self.get_item(uid=uid, user_id=user_id)

        item = await self.model.delete_item(item)
        return item

    async def mine_items(
        self,
        request: Request,
    ) -> PaginatedResponse[TS]:
        user_id = await self.get_user_id(request)
        resp = await self._list_items(request=request, user_id=user_id)
        if resp.total == 0 and self.create_mine_if_not_found:
            resp.items = [await self.model.create_item({"user_id": user_id})]
            resp.total = 1
        if self.unique_per_user:
            return resp.items[0]
        return resp


class AbstractTaskRouter(AbstractBaseRouter):
    def __init__(
        self,
        *,
        model: type[T] | None = None,
        schema: type[TS] | None = None,
        user_dependency: Callable[[Request], Any] | None = None,
        draftable: bool = True,
        **kwargs: object,
    ) -> None:
        self.draftable = draftable
        super().__init__(
            model=model,
            user_dependency=user_dependency,
            schema=schema,
            **kwargs,
        )

    def config_routes(self, **kwargs: object) -> None:
        super().config_routes(**kwargs)

        if self.draftable and kwargs.get("start_route", True):
            self.router.add_api_route(
                "/{uid:str}/start",
                self.start_item,
                methods=["POST"],
                response_model=self.retrieve_response_schema,
            )

        if kwargs.get("webhook_route", True):
            self.router.add_api_route(
                "/{uid:str}/webhook",
                self.webhook,
                methods=["POST"],
                status_code=200,
            )

    async def statistics(
        self,
        request: Request,
        created_at_from: datetime | None = None,
        created_at_to: datetime | None = None,
        task_status: TaskStatusEnum | None = None,
    ) -> dict:
        return await super().statistics(request)

    async def create_item(
        self,
        request: Request,
        data: dict,
        background_tasks: BackgroundTasks,
        blocking: bool = False,
    ) -> T:
        if not self.draftable:
            data["task_status"] = "init"

        item = await super().create_item(request, data)

        if item.task_status == "init" or not self.draftable:
            if blocking:
                await item.start_processing()
            else:
                background_tasks.add_task(item.start_processing)
        return item

    async def start_item(
        self, request: Request, uid: str, background_tasks: BackgroundTasks
    ) -> dict:
        user_id = await self.get_user_id(request)
        item = await self.get_item(uid=uid, user_id=user_id)
        background_tasks.add_task(item.start_processing)
        return item.model_dump()

    async def webhook(
        self,
        request: Request,
        uid: str,
        data: dict,
    ) -> dict:
        import logging

        logging.info("Webhook received for %s with data %s", uid, data)
        return {"message": f"Webhook received for {uid} with data", **data}


def copy_router(router: APIRouter, new_prefix: str) -> APIRouter:
    new_router = APIRouter(prefix=new_prefix)
    for route in router.routes:
        route_data = route.__dict__
        route_data["path"] = route_data["path"].replace(router.prefix, "")
        new_router.add_api_route(**route_data)

    return new_router

from typing import Type, Generic, TypeVar, Any
from pydantic import BaseModel, ValidationError

from jiuwen.core.stream.emitter import StreamEmitter

T = TypeVar("T")
S = TypeVar("S", bound=BaseModel)


class StreamWriter(Generic[T, S]):

    def __init__(self, stream_emitter: StreamEmitter, schema_type: Type[S]):
        if stream_emitter is None:
            raise ValueError("stream_emitter can not be None")

        self._stream_emitter = stream_emitter
        self._schema_type = schema_type

    async def write(self, stream_data: T) -> None:
        try:
            validated_data = self._schema_type.model_validate(stream_data)
        except ValidationError as e:
            raise ValueError(
                f"Data validation failed for schema {self._schema_type.__name__}"
            ) from e

        await self._do_write(validated_data)

    async def _do_write(self, validated_data: S) -> None:
        await self._stream_emitter.emit(validated_data)


class OutputSchema(BaseModel):
    type: str
    index: int
    payload: Any


class OutputStreamWriter(StreamWriter[dict, OutputSchema]):

    def __init__(
        self,
        stream_emitter: StreamEmitter,
        schema_type: Type[OutputSchema] = OutputSchema,
    ):
        super().__init__(stream_emitter, schema_type)


class TraceSchema(BaseModel):
    type: str
    payload: Any


class TraceStreamWriter(StreamWriter[dict, TraceSchema]):

    def __init__(
        self,
        stream_emitter: StreamEmitter,
        schema_type: Type[TraceSchema] = TraceSchema,
    ):
        super().__init__(stream_emitter, schema_type)


class CustomSchema(BaseModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"


class CustomStreamWriter(StreamWriter[dict, CustomSchema]):

    def __init__(
        self,
        stream_emitter: StreamEmitter,
        schema_type: Type[CustomSchema] = CustomSchema,
    ):
        super().__init__(stream_emitter, schema_type)

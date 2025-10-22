import uuid
from datetime import datetime
from typing import Optional, Dict, List, Callable
from pydantic import ConfigDict, Field, BaseModel


class Span(BaseModel):
    trace_id: str = Field(alias="traceId")
    start_time: datetime = Field(default=None, alias="startTime")
    end_time: Optional[datetime] = Field(default=None, alias="endTime")
    inputs: Optional[dict] = Field(default=None, alias="inputs")
    outputs: Optional[dict] = Field(default=None, alias="outputs")
    error: Optional[dict] = Field(default=None, alias="error")
    invoke_id: str = Field(default=None, alias="invokeId")
    parent_invoke_id: Optional[str] = Field(default=None, alias="parentInvokeId")
    child_invokes_id: List[str] = Field(default=[], alias="childInvokes")

    model_config = ConfigDict(populate_by_name=True)

    def update(self, data: dict):
        for attr_name, value in data.items():
            if not hasattr(self, attr_name):
                continue
            setattr(self, attr_name, value)


class TraceAgentSpan(Span):
    invoke_type: str = Field(default=None, alias="invokeType")
    name: str = Field(default=None, alias="name")
    elapsed_time: Optional[str] = Field(default=None, alias="elapsedTime")
    meta_data: Optional[dict] = Field(default=None, alias="metaData")  # include llm function tools and token infos


class TraceWorkflowSpan(Span):
    execution_id: str = Field(default="", alias="executionId")
    conversation_id: str = Field(default="", alias="conversationId")
    on_invoke_data: List[dict] = Field(default=[], alias="onInvokeData")  # 用于记录当前组件执行时间的中间过程信息
    agent_id: str = Field(default="", alias="agentId")
    component_id: str = Field(default="", alias="componentId")  # 放到metadata
    component_name: str = Field(default="", alias="componentName")  # 放到metadata
    component_type: str = Field(default="", alias="componentType")  # 即invoke_type
    agent_parent_invoke_id: str = Field(default="", alias="agentParentInvokeId")  # 给未来适配workflow节点中嵌套workflow预留
    meta_data: Optional[str] = Field(default=None, alias="metaData")  # 包括：模型的输入的function tools信息，模型的token使用信息
    # for loop component
    loop_node_id: Optional[str] = Field(default=None, alias="loopNodeId")
    loop_index: Optional[int] = Field(default=None, alias="loopIndex")
    # node status
    status: Optional[str] = Field(default=None, alias="status")
    # for llm invoke data
    llm_invoke_data: Dict[str, dict] = Field(default=[], exclude=True)  # 模型数据，临时存储
    # for subworkflow
    parent_node_id: str = Field(default="", alias="parentNodeId")


class SpanManager:
    """用于管理tracer handler运行期间的span"""

    def __init__(self, trace_id: str, parent_node_id: str = ""):
        self._trace_id = trace_id
        self._parent_node_id = parent_node_id
        self._order = []
        self._runtime_spans = {}

    def get_span(self, invoke_id: str):
        if invoke_id not in self._order:
            return None
        return self._runtime_spans.get(invoke_id, None)

    def pop_span(self, invoke_id: str):
        if invoke_id not in self._order:
            return
        self._order.remove(invoke_id)
        self._runtime_spans.pop(invoke_id)

    def refresh_span_record(self, invoke_id: str, runtime_span: Dict[str, Span]):
        if invoke_id not in self._order:
            self._order.append(invoke_id)
        self._runtime_spans[invoke_id] = runtime_span[invoke_id]

    def _refresh_parent_child_span(self, span, parent_span=None):
        if parent_span:
            parent_span.child_invokes_id.append(span.invoke_id)
            self.refresh_span_record(parent_span.invoke_id, {parent_span.invoke_id: parent_span})
        self.refresh_span_record(span.invoke_id, {span.invoke_id: span})

    def create_agent_span(self, parent_span: Optional[TraceAgentSpan] = None) -> TraceAgentSpan:
        invoke_id = str(uuid.uuid4())
        span = TraceAgentSpan(invoke_id=invoke_id, parent_invoke_id=parent_span.invoke_id if parent_span else None,
                              trace_id=self._trace_id)
        self._refresh_parent_child_span(span, parent_span)
        return span

    def create_workflow_span(self, invoke_id: str,
                             parent_span: Optional[TraceWorkflowSpan] = None) -> TraceWorkflowSpan:
        span = TraceWorkflowSpan(invoke_id=invoke_id, parent_invoke_id=parent_span.invoke_id if parent_span else None,
                                 trace_id=self._trace_id, parent_node_id=self._parent_node_id,
                                 execution_id=self._trace_id)
        self._refresh_parent_child_span(span, parent_span)
        return span

    def update_span(self, span: Span, data: dict):
        span.update(data)
        self.refresh_span_record(span.invoke_id, {span.invoke_id: span})

    def end_span(self):
        pass

    @property
    def last_span(self):
        if not self._order:
            return None
        last_span_id = self._order[-1]
        if last_span_id not in self._runtime_spans:
            return None
        return self._runtime_spans[last_span_id]

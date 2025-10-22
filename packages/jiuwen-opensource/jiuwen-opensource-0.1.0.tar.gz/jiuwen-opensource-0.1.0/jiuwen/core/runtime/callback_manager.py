from abc import abstractmethod
from typing import Callable, Dict, List

def trigger_event(func):
    func._is_trigger_event = True
    return func

class BaseHandler:
    """无状态数据处理"""
    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.trigger_event = trigger_event
        
    def __init__(self, owner):
        self.owner = owner
        
    @abstractmethod
    def event_name(self):
        pass
    
    def get_trigger_events(self):
        return [
            name for name in dir(self)
            if callable(getattr(self, name)) and
                getattr(getattr(self, name), "_is_trigger_event", False)
        ]
        
class CallbackManager:
    def __init__(self):
        self._handlers: Dict[str, BaseHandler] = {}
        self._trigger_events: Dict[str, List] = {}
        
    def _instantiation_handler(self, handler_class_name: Callable):
        handler = handler_class_name(owner=self)
        if not isinstance(handler, handler_class_name):
            raise TypeError("handler class name cannot be instantiation")
        return handler
    
    def _init_handler(self, handler_map: dict):
        for handler_name, handler in handler_map.items():
            if handler_name in self._handlers:
                raise ValueError(f"handler class name exists")
        self._handlers[handler_name] = handler
        trigger_events = handler.get_trigger_events()
        self._trigger_events[handler_name] = trigger_events
        
    async def trigger(self, handler_class_name: str, event_name: str, **kwargs):
        if handler_class_name not in self._trigger_events or event_name not in self._trigger_events[
            handler_class_name
        ]:
            raise TypeError(f"event name not exists: {handler_class_name}, {event_name}")
        handler = self._handlers[handler_class_name]
        if hasattr(handler, event_name):
            method = getattr(handler, event_name)
            await method(**kwargs)
            
    def register_handler(self, configs: dict):
        self._init_handler(configs)
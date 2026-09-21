from .base import AIProvider

class AnthropicProvider(AIProvider):
    async def chat(self, messages, **kwargs): raise NotImplementedError
    async def chat_stream(self, messages, **kwargs): raise NotImplementedError
    async def get_models(self): raise NotImplementedError
    
    @property
    def supports_streaming(self) -> bool: return False
    @property
    def supports_tools(self) -> bool: return False
    @property
    def supports_vision(self) -> bool: return False

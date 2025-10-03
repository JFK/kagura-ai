"""
Kagura AI 2.0 - Python-First AI Agent Framework

Example:
    from kagura import agent

    @agent
    async def hello(name: str) -> str:
        '''Say hello to {{ name }}'''
        pass

    result = await hello("World")
"""
__version__ = "2.0.0-alpha.1"

__all__ = ["__version__"]

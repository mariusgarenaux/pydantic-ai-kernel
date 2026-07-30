"""A wrapper of pydantic-ai in jupyter kernel"""

__version__ = "1.5.1"


from .kernel import PydanticAIBaseKernel  # noqa: F401
from .jupydantic_agent import JuPydanticAgent
from .agent_config import AgentConfig, ModelProviderConfig, ModelConfig  # noqa: F401
from .boosted_magic import BoostedMagic, boosted_option, complete_from_list

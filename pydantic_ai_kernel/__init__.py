"""An example Jupyter kernel"""

__version__ = "1.4.2"


from .kernel import PydanticAIBaseKernel  # noqa: F401
from .agent_config import AgentConfig, ModelProviderConfig, ModelConfig  # noqa: F401
from .boosted_magic import BoostedMagic, boosted_option, complete_from_list

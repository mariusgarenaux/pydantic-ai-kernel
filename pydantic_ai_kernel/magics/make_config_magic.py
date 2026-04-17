from metakernel import Magic, option
from pydantic_ai_kernel import PydanticAIBaseKernel


class EditConfigMagic(Magic):
    """
    Loads the config file in a cell, and adds the magic %%write_config
    to save the content of the config in the file when the cell is
    executed.
    """

    @option(
        "--template",
        default=None,
        help="Name of the template to use. Can be ollama, open_web_ui, openai",
    )
    def line_make_config(self, template: str | None = None):
        """
        %make_config --template <template_name> : create or change the config file

        Either create a config file at ~/.jupyter/jupyter_<app_name>_config.yaml
        or load the existing one in a cell, to change it.

        You can give a template with the flag --template (ollama, openai, open_web_ui).
        You can also look at the scheme for the configuration file.
        https://github.com/mariusgarenaux/pydantic-ai-kernel
        """
        self.kernel: PydanticAIBaseKernel
        absolute_path_config = self.kernel.get_config_dir()
        with open(absolute_path_config) as f:
            text = f.read()
        if text != "" and template is not None:
            if self.kernel.ask_user_approval(
                f"The config file is not empty. Do you want to overwrite it with the template `{template}` ?"
            ):
                content = config_templates[template]

            else:
                content = text
        else:
            if template is not None:
                content = config_templates[template]
            else:
                content = text
        self.kernel.payload.append(
            {
                "source": "set_next_input",
                "text": "%%write_config\n" + content,
            }
        )


config_templates = {
    "ollama": """
agent_name: ollama
system_prompt: ""
model: 
  model_name: <model_name>
  model_type: openai
  model_provider:
    name: ollama
    params:
      base_url: http://localhost:11434/v1
    """,
    "open_web_ui": """
agent_name: owui
system_prompt: ""
model: 
  model_name: <model_name>
  model_type: openai
  model_provider:
    name: openai
    params:
      api_key: <from_owui>
      base_url: <https://owui_url/api> # must end with /api !
    """,
    "openai": """
model:
  model_name: <model_name>
  model_type: openai
  model_provider:
    name: openai
    params:
      api_key: <>
      base_url: <openai_api>
    """,
}


def register_magics(kernel: PydanticAIBaseKernel) -> None:
    kernel.register_magics(EditConfigMagic)

import os

from pydantic_ai_kernel import (
    PydanticAIBaseKernel,
    BoostedMagic,
    boosted_option,
    complete_from_list,
)
from pydantic_ai_kernel.utils import LoadConfigError
from metakernel.magics.file_magic import FileMagic

template_list = ["ollama", "open_web_ui", "openai"]

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


class ConfigMagic(BoostedMagic):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_magic = FileMagic(self.kernel)
        # tried with subclassing FileMagic directly,
        # but gives access to cell_file, which is not
        # wanted for this kernel.
        # This can cause problem since self.file_magic
        # object does not have access to all elements
        # (p.e. self.code must be manually upstreamed)

    @boosted_option(
        "--path",
        default=None,
        help="The path to the configuration file to load, create or edit.",
    )
    @boosted_option(
        "--edit",
        default=False,
        action="store_true",
        help="Whether to edit or not the config located at path, and save it in usual config dir.",
    )
    @boosted_option(
        "-t",
        "--template",
        help="Name of the template to use. Can be ollama, open_web_ui, openai",
        choices=template_list,
        completer=lambda w, r: complete_from_list(template_list, w, r),
    )
    @boosted_option(
        "-r",
        "--reset",
        action="store_true",
        default=False,
        help="Whether to reset agent history after loading config.",
    )
    def line_config(
        self,
        path: str | None = None,
        edit: bool = False,
        template: str | None = None,
        reset: bool = False,
    ) -> None:
        """
        %config : loads, edit or create agent config file

        Examples :
        -------
            • %config : try to load ~/.jupyter/jupyter_<app_name>_config.yaml
                and propose to create or edit it if it does not work
            • %config --path /my/config.yaml : load config located at
                /my/config.yaml
            • %config --path /my/config.yaml --edit : edit or
                create config located at /my/config.yaml
            • %config --reset : same as %config, but reset the agent
                history when the config is reloaded. Else, it is
                kept among configuration files.
        """
        self.kernel: PydanticAIBaseKernel  # type hints
        self.evaluate = False

        # 1 - try to load config file located at path, or default path
        if path is None:
            path = self.kernel.get_config_dir()

        if template is None and not edit:
            try:
                self.kernel.agent_config = self.kernel.load_config(path=path)
            except LoadConfigError as e:
                self.kernel.log.debug(f"Error while loading config file : {e}")
                if not self.kernel.ask_user_approval(
                    f"Could not load config from `{path}`. Do you want to edit this file ?"
                ):
                    return

            else:
                self.kernel.log.info("Config was loaded from default path.")
                if reset:
                    self.kernel.message_history = []
                agent = self.kernel.create_agent()
                self.kernel.agent = agent
                return

        # 2 - Loading failed, or user wants to edit the config file
        config_path = path if path is not None else self.kernel.get_config_dir()
        self.kernel.log.info(config_path)
        if os.path.isfile(config_path):
            with open(config_path, "rt") as f:
                content = f.read()

            if template is None:
                template = self.kernel.raw_input(
                    f"[Optional] Use template among `{template_list}` (leave empty for no template): "
                )
                if template not in template_list:
                    template = None

            if len(content) > 0 and template is not None:
                if self.kernel.ask_user_approval(
                    f"A file exists at {config_path}. Do you want to overwrite it with the template `{template}` ?"
                ):
                    content = config_templates[template]
                else:
                    return
        else:
            # we create the file
            open(config_path, "w")
            content = "" if template is None else config_templates[template]

        self.kernel.payload.append(
            {
                "source": "set_next_input",
                "text": f"%%file {config_path}\n" + content,
            }
        )


def register_magics(kernel) -> None:
    kernel.register_magics(ConfigMagic)

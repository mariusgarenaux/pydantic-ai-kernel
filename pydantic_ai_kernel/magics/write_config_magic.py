from metakernel.magics.file_magic import FileMagic
from metakernel import Magic
from pydantic_ai_kernel import PydanticAIBaseKernel


class WriteConfigMagic(Magic):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_magic = FileMagic(self.kernel)
        # tried with subclassing FileMagic directly,
        # but gives access to cell_file, which is not
        # wanted for this kernel.
        # This can cause problem since self.file_magic
        # object does not have access to all elements
        # (p.e. self.code must be manually upstreamed)

    def cell_write_config(self):
        """
        %%write_config : write the content of cell in config file
        Write the content of the cell (without %%write_config) into
        the configuration file, located at ~/.jupyter/jupyter_<app_name>_config.yaml
        """
        self.kernel: PydanticAIBaseKernel
        if self.code == "":
            if not self.kernel.ask_user_approval(
                "The provided file content is empty. Do you validate that you want to delete content from config file ?"
            ):
                return
        self.file_magic.code = self.code
        self.file_magic.cell_file(self.kernel.get_config_dir())
        self.kernel.config_has_changed = True  # to trigger the refresh of the agent
        # on the next do_execute

        self.evaluate = False


def register_magics(kernel: PydanticAIBaseKernel) -> None:
    kernel.register_magics(WriteConfigMagic)

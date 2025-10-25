from e2b import Sandbox as SandboxBase
from e2b_devcontainers.utils import escape_string


class DevContainerSandbox(SandboxBase):
    def run_cmd(self, command: str, **kwargs):
        return self.__exec_cmd(f'-c "{escape_string(command)}"', **kwargs)

    def __exec_cmd(self, command: str, **kwargs):
        return self.commands.run(f"/devcontainer.sh {command}", **kwargs, user="root")

from e2b import Sandbox as SandboxBase
from e2b_devcontainers.utils import escape_string


class DevContainerSandbox(SandboxBase):
    def run_cmd(self, command: str, **kwargs):
        """
        Run a command in the devcontainer sandbox.
        :param command: The command to run.
        :param kwargs: The keyword arguments to pass to the command.
        :return: The output of the command.
        """
        return self.__exec_cmd(f'-c "{escape_string(command)}"', **kwargs)

    def __exec_cmd(self, command: str, **kwargs):
        """
        Execute a command in the devcontainer sandbox.
        :param command: The command to execute.
        :param kwargs: The keyword arguments to pass to the command.
        :return: The output of the command.
        """
        return self.commands.run(f"/devcontainer.sh {command}", **kwargs, user="root")

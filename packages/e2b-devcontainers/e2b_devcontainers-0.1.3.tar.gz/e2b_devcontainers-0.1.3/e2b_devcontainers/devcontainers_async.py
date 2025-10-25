from e2b import AsyncSandbox as AsyncSandboxBase
from e2b_devcontainers.utils import escape_string


class DevContainerSandboxAsync(AsyncSandboxBase):
    async def run_cmd(self, command: str, **kwargs):
        """
        Run a command in the devcontainer sandbox.
        :param command: The command to run.
        :param kwargs: The keyword arguments to pass to the command.
        :return: The output of the command.
        """
        return await self.__exec_cmd(f'-c "{escape_string(command)}"', **kwargs)

    async def __exec_cmd(self, command: str, **kwargs):
        """
        Execute a command in the devcontainer sandbox.
        :param command: The command to execute.
        :param kwargs: The keyword arguments to pass to the command.
        :return: The output of the command.
        """
        return await self.commands.run(
            f"/devcontainer.sh {command}", **kwargs, user="root"
        )

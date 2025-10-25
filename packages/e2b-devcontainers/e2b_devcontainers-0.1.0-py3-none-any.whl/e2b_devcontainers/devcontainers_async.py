from e2b import Sandbox as SandboxBase

class DevcontainerSandboxAsync(SandboxBase):
    async def run_command(self, command: str, **kwargs):
        return await self.commands.run(f"/devcontainer.sh -c {command}", **kwargs)

    async def exec(self, command: str, **kwargs):
        return await self.commands.run(f"/devcontainer.sh {command}", **kwargs)

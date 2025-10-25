from e2b import Sandbox as SandboxBase

class DevcontainerSandbox(SandboxBase):
    def run_command(self, command: str, **kwargs):
        return self.commands.run(f"/devcontainer.sh -c {command}", **kwargs)

    def exec(self, command: str, **kwargs):
        return self.commands.run(f"/devcontainer.sh {command}", **kwargs)

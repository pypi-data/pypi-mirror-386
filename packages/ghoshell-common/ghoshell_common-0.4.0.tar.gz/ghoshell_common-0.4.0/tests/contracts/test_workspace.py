from ghoshell_common.contracts import (
    WorkspaceLoggerProvider, WorkspaceConfigsProvider, WorkspaceAssetsRepoProvider, LocalWorkspaceProvider,
    LoggerItf, Workspace, Configs, YamlConfig,
)
from ghoshell_container import Container


def test_workspace_baseline_in_memory():
    container = Container()
    container.register(
        WorkspaceLoggerProvider(),
        WorkspaceConfigsProvider(),
        LocalWorkspaceProvider(),
    )
    assert container.get(LoggerItf) is not None
    ws = container.get(Workspace)
    assert ws is not None

    configs = container.get(Configs)
    assert configs is not None

    class FooConf(YamlConfig):
        relative_path = "foo.yml"
        foo: int = 123

    foo = configs.get_or_create(FooConf())
    assert foo.foo == 123

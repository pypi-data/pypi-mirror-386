import os
from abc import ABC, abstractmethod
from typing import Optional

from ghoshell_common.contracts.storage import Storage, DefaultFileStorage, MemoryStorage
from ghoshell_container import Container, Provider
from os.path import abspath
import shutil

__all__ = ['Workspace', 'LocalWorkspace', 'LocalWorkspaceProvider']


class Workspace(ABC):
    """
    workspace 目录文件管理.
    用于管理一个项目的本地文件存储.
    """

    @abstractmethod
    def root(self) -> Storage:
        """
        workspace 根 storage.
        """
        pass

    @abstractmethod
    def configs(self) -> Storage:
        """
        配置文件存储路径.
        """
        pass

    @abstractmethod
    def runtime(self) -> Storage:
        """
        运行时数据存储路径.
        """
        pass

    @abstractmethod
    def assets(self) -> Storage:
        """
        数据资产存储路径.
        """
        pass


class LocalWorkspace(Workspace):

    def __init__(self, workspace_dir: str):
        workspace_dir = abspath(workspace_dir)
        self._ws_root_dir = workspace_dir
        if not self._ws_root_dir:
            self._root = MemoryStorage(self._ws_root_dir)
        else:
            self._root = DefaultFileStorage(workspace_dir)

    def root(self) -> Storage:
        return self._root

    def configs(self) -> Storage:
        return self._root.sub_storage("configs")

    def runtime(self) -> Storage:
        return self._root.sub_storage("runtime")

    def assets(self) -> Storage:
        return self._root.sub_storage("assets")


class LocalWorkspaceProvider(Provider[Workspace]):

    def __init__(
            self,
            workspace_dir: str = "",
            stub_dir: Optional[str] = None,
    ):
        if workspace_dir == "":
            # 使用脚本运行的路径作为 workspace.
            workspace_dir = abspath(workspace_dir)
        self._ws_dir = workspace_dir
        self._stub_dir = abspath(stub_dir) if stub_dir else None

    def singleton(self) -> bool:
        return True

    def factory(self, con: Container) -> Optional[Workspace]:
        if self._ws_dir and self._stub_dir and not os.path.exists(self._stub_dir):
            os.makedirs(self._stub_dir)
            shutil.copytree(self._stub_dir, self._ws_dir)
        return LocalWorkspace(self._ws_dir)

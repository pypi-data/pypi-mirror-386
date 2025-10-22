# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# pyre-strict

import asyncio
import importlib
import json
import logging
import os
import warnings
from contextlib import AbstractContextManager
from pathlib import Path

from typing import (
    Any,
    Callable,
    cast,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Type,
    TYPE_CHECKING,
    TypeVar,
)
from urllib.parse import urlparse
from weakref import WeakSet

from monarch._rust_bindings.monarch_hyperactor.alloc import AllocConstraints
from monarch._rust_bindings.monarch_hyperactor.context import Instance as HyInstance
from monarch._rust_bindings.monarch_hyperactor.pytokio import PythonTask, Shared
from monarch._rust_bindings.monarch_hyperactor.shape import Extent, Region, Shape, Slice
from monarch._rust_bindings.monarch_hyperactor.v1.proc_mesh import (
    ProcMesh as HyProcMesh,
)
from monarch._src.actor.actor_mesh import (
    _Actor,
    _Lazy,
    _this_host_for_fake_in_process_host,
    Actor,
    ActorMesh,
    context,
)
from monarch._src.actor.allocator import AllocHandle, SimAllocator
from monarch._src.actor.code_sync import (
    CodeSyncMeshClient,
    CodeSyncMethod,
    RemoteWorkspace,
    WorkspaceConfig,
    WorkspaceLocation,
    WorkspaceShape,
)
from monarch._src.actor.device_utils import _local_device_count

from monarch._src.actor.endpoint import endpoint
from monarch._src.actor.future import Future
from monarch._src.actor.logging import LoggingManager
from monarch._src.actor.shape import MeshTrait
from monarch.tools.config.environment import CondaEnvironment
from monarch.tools.config.workspace import Workspace
from monarch.tools.utils import conda as conda_utils


if TYPE_CHECKING:
    Tensor = Any
    DeviceMesh = Any
    from monarch._src.actor.proc_mesh import SetupActor  # noqa
    from monarch._src.actor.v1.host_mesh import HostMesh


logger: logging.Logger = logging.getLogger(__name__)


T = TypeVar("T")
TActor = TypeVar("TActor", bound=Actor)


_proc_mesh_registry: WeakSet["ProcMesh"] = WeakSet()


def get_active_proc_meshes() -> List["ProcMesh"]:
    """Get a list of all active ProcMesh instances."""
    return list(_proc_mesh_registry)


class ProcMesh(MeshTrait):
    """
    A distributed mesh of processes for actor computation.

    ProcMesh represents a collection of processes that can spawn and manage actors.
    It provides the foundation for distributed actor systems by managing process
    allocation, lifecycle, and communication across multiple hosts and devices.

    The ProcMesh supports spawning actors, monitoring process health, logging
    configuration, and code synchronization across distributed processes.
    """

    def __init__(
        self,
        hy_proc_mesh: "Shared[HyProcMesh]",
        host_mesh: "HostMesh",
        region: Region,
        root_region: Region,
        _initialized_hy_proc_mesh: Optional[HyProcMesh],
        _device_mesh: Optional["DeviceMesh"] = None,
    ) -> None:
        _proc_mesh_registry.add(self)

        self._initialized_proc_mesh = _initialized_hy_proc_mesh
        if not self._initialized_proc_mesh:

            async def task(hy_proc_mesh_task: Shared[HyProcMesh]) -> HyProcMesh:
                self._initialized_proc_mesh = await hy_proc_mesh_task
                return self._initialized_proc_mesh

            hy_proc_mesh = PythonTask.from_coroutine(task(hy_proc_mesh)).spawn()

        self._proc_mesh = hy_proc_mesh
        self._host_mesh = host_mesh
        self._region = region
        self._root_region = root_region
        self._maybe_device_mesh = _device_mesh
        self._stopped = False
        self._logging_manager = LoggingManager()
        self._controller_controller: Optional["_ControllerController"] = None
        self._code_sync_client: Optional[CodeSyncMeshClient] = None

    @property
    def initialized(self) -> Future[Literal[True]]:
        """
        Future completes with 'True' when the ProcMesh has initialized.
        Because ProcMesh are remote objects, there is no guarentee that the ProcMesh is
        still usable after this completes, only that at some point in the past it was usable.
        """
        pm: Shared[HyProcMesh] = self._proc_mesh

        async def task() -> Literal[True]:
            await pm
            return True

        return Future(coro=task())

    @property
    def host_mesh(self) -> "HostMesh":
        if self.extent.nelements != 1:
            raise NotImplementedError(
                "`ProcMesh.host_mesh` is not yet supported for non-singleton proc meshes."
            )
        elif self._host_mesh.is_fake_in_process:
            host_mesh = _this_host_for_fake_in_process_host.try_get()
            assert host_mesh is not None, (
                "Attempted to get `_this_host_for_fake_in_process_host` before the root client context "
                "initialized it. This should not be possible."
            )
            return host_mesh
        else:
            return self._host(0)

    @property
    def _ndslice(self) -> Slice:
        return self._region.slice()

    @property
    def _labels(self) -> List[str]:
        return self._region.labels

    def _new_with_shape(self, shape: Shape) -> "ProcMesh":
        if shape == self._region.as_shape():
            return self

        device_mesh = (
            None
            if self._maybe_device_mesh is None
            else self._maybe_device_mesh._new_with_shape(shape)
        )

        initialized_pm: Optional[HyProcMesh] = (
            None
            if self._initialized_proc_mesh is None
            else self._initialized_proc_mesh.sliced(shape.region)
        )

        async def task() -> HyProcMesh:
            return (
                initialized_pm
                if initialized_pm
                else (await self._proc_mesh).sliced(shape.region)
            )

        return ProcMesh(
            PythonTask.from_coroutine(task()).spawn(),
            self._host_mesh,
            shape.region,
            self._root_region,
            initialized_pm,
            _device_mesh=device_mesh,
        )

    def spawn(
        self, name: str, Class: Type[TActor], *args: Any, **kwargs: Any
    ) -> TActor:
        """
        Spawn a T-typed actor mesh on the process mesh.

        Args:
        - `name`: The name of the actor.
        - `Class`: The class of the actor to spawn.
        - `args`: Positional arguments to pass to the actor's constructor.
        - `kwargs`: Keyword arguments to pass to the actor's constructor.

        Returns:
        - The actor instance.
        """
        return self._spawn_nonblocking(name, Class, *args, **kwargs)

    @property
    async def _proc_mesh_for_asyncio_fixme(self) -> HyProcMesh:
        """
        Get ProcMesh on the asyncio event stream.
        We should redo this functionality to work on the tokio stream.
        This must be called on the asyncio stream.
        """
        assert asyncio.get_running_loop() is not None
        return await Future(coro=self._proc_mesh.task())

    async def monitor(self) -> None:
        logger.debug("monitor is not implemented for v1 ProcMesh")

    @classmethod
    def from_host_mesh(
        self,
        host_mesh: "HostMesh",
        hy_proc_mesh: "Shared[HyProcMesh]",
        region: Region,
        setup: Callable[[], None] | None = None,
        _attach_controller_controller: bool = True,
    ) -> "ProcMesh":
        pm = ProcMesh(hy_proc_mesh, host_mesh, region, region, None)

        if _attach_controller_controller:
            instance = context().actor_instance
            pm._controller_controller = instance._controller_controller
            instance._add_child(pm)

        async def task(
            pm: "ProcMesh",
            hy_proc_mesh_task: "Shared[HyProcMesh]",
            setup_actor: Optional["SetupActor"],
            stream_log_to_client: bool,
        ) -> HyProcMesh:
            hy_proc_mesh = await hy_proc_mesh_task

            await pm._logging_manager.init(hy_proc_mesh, stream_log_to_client)

            if setup_actor is not None:
                await setup_actor.setup.call()

            return hy_proc_mesh

        setup_actor = None
        if setup is not None:
            from monarch._src.actor.proc_mesh import SetupActor  # noqa

            # If the user has passed the setup lambda, we need to call
            # it here before any of the other actors are spawned so that
            # the environment variables are set up before cuda init.
            setup_actor = pm._spawn_nonblocking_on(
                hy_proc_mesh, "setup", SetupActor, setup
            )

        pm._proc_mesh = PythonTask.from_coroutine(
            task(pm, hy_proc_mesh, setup_actor, host_mesh.stream_logs)
        ).spawn()

        return pm

    def __repr__(self) -> str:
        return repr(self._proc_mesh)

    def __str__(self) -> str:
        return str(self._proc_mesh)

    def _spawn_nonblocking(
        self, name: str, Class: Type[TActor], *args: Any, **kwargs: Any
    ) -> TActor:
        return self._spawn_nonblocking_on(self._proc_mesh, name, Class, *args, **kwargs)

    def to_table(self) -> str:
        return self._device_mesh.to_table()

    def _spawn_nonblocking_on(
        self,
        pm: "Shared[HyProcMesh]",
        name: str,
        Class: Type[TActor],
        *args: Any,
        **kwargs: Any,
    ) -> TActor:
        if not issubclass(Class, Actor):
            raise ValueError(
                f"{Class} must subclass monarch.service.Actor to spawn it."
            )

        instance = context().actor_instance
        actor_mesh = HyProcMesh.spawn_async(
            pm, instance._as_rust(), name, _Actor, emulated=False
        )
        service = ActorMesh._create(
            Class,
            actor_mesh,
            self._region.as_shape(),
            self,
            self._controller_controller,
            *args,
            **kwargs,
        )
        instance._add_child(service)
        return cast(TActor, service)

    @property
    def _device_mesh(self) -> "DeviceMesh":
        from monarch._src.actor.proc_mesh import _has_tensor_engine

        if not _has_tensor_engine():
            raise RuntimeError(
                "DeviceMesh is not available because tensor_engine was not compiled (USE_TENSOR_ENGINE=0)"
            )

        # type: ignore[21]
        from monarch.mesh_controller import spawn_tensor_engine  # @manual

        if self._maybe_device_mesh is None:
            # type: ignore[21]
            self._maybe_device_mesh = spawn_tensor_engine(self)
        return self._maybe_device_mesh

    # pyre-ignore
    def activate(self) -> AbstractContextManager:
        return self._device_mesh.activate()

    def rank_tensor(self, dim: str | Sequence[str]) -> "Tensor":
        return self._maybe_device_mesh.rank(dim)

    def rank_tensors(self) -> Dict[str, "Tensor"]:
        return self._maybe_device_mesh.ranks

    async def logging_option(
        self,
        stream_to_client: bool = True,
        aggregate_window_sec: int | None = 3,
        level: int = logging.INFO,
    ) -> None:
        """
        Set the logging options for the remote processes

        Args:
            stream_to_client (bool): If True, logs from the remote processes will be streamed to the client.
            Defaults to True.
            aggregate_window_sec (Optional[int]): If not None, logs from the remote processes will be aggregated
            and sent to the client every aggregate_window_sec seconds. Defaults to 3 seconds, meaning no aggregation.
            Error will be thrown if aggregate_window_sec is set and stream_to_client is False.
            level (int): The logging level of the logger. Defaults to logging.INFO.

        Returns:
            None
        """
        await self.initialized

        await self._logging_manager.logging_option(
            stream_to_client=stream_to_client,
            aggregate_window_sec=aggregate_window_sec,
            level=level,
        )

    async def __aenter__(self) -> "ProcMesh":
        if self._stopped:
            raise RuntimeError("`ProcMesh` has already been stopped")
        return self

    def stop(self) -> Future[None]:
        """
        This will stop all processes (and actors) in the mesh and
        release any resources associated with the mesh.
        """

        instance = context().actor_instance._as_rust()

        async def _stop_nonblocking(instance: HyInstance) -> None:
            await (await self._proc_mesh).stop_nonblocking(instance)
            self._stopped = True

        return Future(coro=_stop_nonblocking(instance))

    async def __aexit__(
        self, exc_type: object, exc_val: object, exc_tb: object
    ) -> None:
        # In case there are multiple nested "async with" statements, we only
        # want it to close once.
        if not self._stopped:
            await self.stop()

    @classmethod
    def _from_initialized_hy_proc_mesh(
        cls,
        hy_proc_mesh: HyProcMesh,
        host_mesh: "HostMesh",
        region: Region,
        root_region: Region,
    ) -> "ProcMesh":
        async def task() -> HyProcMesh:
            return hy_proc_mesh

        return ProcMesh(
            PythonTask.from_coroutine(task()).spawn(),
            host_mesh,
            region,
            root_region,
            _initialized_hy_proc_mesh=hy_proc_mesh,
        )

    def __reduce_ex__(self, protocol: ...) -> Tuple[Any, Tuple[Any, ...]]:
        return ProcMesh._from_initialized_hy_proc_mesh, (
            self._initialized_proc_mesh
            if self._initialized_proc_mesh
            else self._proc_mesh.block_on(),
            self._host_mesh,
            self._region,
            self._root_region,
        )

    def _host(self, proc_rank: int) -> "HostMesh":
        base_proc_rank = self._region.slice().get(proc_rank)
        n_procs = len(self._root_region.slice())
        procs_per_host = n_procs // len(self._host_mesh.region.slice())
        host_rank = base_proc_rank // procs_per_host
        base_host_rank = self._host_mesh.region.slice().get(host_rank)
        return self._host_mesh.slice(
            **self._host_mesh.region.point_of_base_rank(base_host_rank)
        )

    async def sync_workspace(
        self,
        workspace: Workspace,
        conda: bool = False,
        auto_reload: bool = False,
    ) -> None:
        raise NotImplementedError(
            "sync_workspace is not implemented for v1 ProcMesh. Use HostMesh.sync_workspace instead."
        )

    async def _sync_workspace(
        self,
        workspace: Workspace,
        conda: bool = False,
        auto_reload: bool = False,
    ) -> None:
        """
        Sync local code changes to the remote processes.

        Args:
            workspace: The workspace to sync.
            conda: If True, also sync the currently activated conda env.
            auto_reload: If True, automatically reload the workspace on changes.
        """
        if self._code_sync_client is None:
            self._code_sync_client = CodeSyncMeshClient.spawn_blocking(
                client=context().actor_instance,
                proc_mesh=await self._proc_mesh_for_asyncio_fixme,
            )

        # TODO(agallagher): We need some way to configure and pass this
        # in -- right now we're assuming the `gpu` dimension, which isn't
        # correct.
        # The workspace shape (i.e. only perform one rsync per host).
        assert set(self._region.labels).issubset({"gpus", "hosts"})

        workspaces = {}
        for src_dir, dst_dir in workspace.dirs.items():
            local = Path(src_dir)
            workspaces[local] = WorkspaceConfig(
                local=local,
                remote=RemoteWorkspace(
                    location=WorkspaceLocation.FromEnvVar(
                        env="WORKSPACE_DIR",
                        relpath=dst_dir,
                    ),
                    shape=WorkspaceShape.shared("gpus"),
                ),
                method=CodeSyncMethod.Rsync(),
            )

        # If `conda` is set, also sync the currently activated conda env.
        conda_prefix = conda_utils.active_env_dir()
        if isinstance(workspace.env, CondaEnvironment):
            conda_prefix = workspace.env._conda_prefix

        if conda and conda_prefix is not None:
            conda_prefix = Path(conda_prefix)

            # Resolve top-level symlinks for rsync/conda-sync.
            while conda_prefix.is_symlink():
                conda_prefix = conda_prefix.parent / conda_prefix.readlink()

            # Build a list of additional paths prefixes to fixup when syncing
            # the conda env.
            conda_prefix_replacements = {}

            # Auto-detect editable installs and implicitly add workspaces for
            # them.
            # NOTE(agallagher): There's sometimes a `python3.1` symlink to
            # `python3.10`, so avoid it.
            (lib_python,) = [
                dirpath
                for dirpath in conda_prefix.glob("lib/python*")
                if not os.path.islink(dirpath)
            ]
            for direct_url in lib_python.glob(
                "site-packages/*.dist-info/direct_url.json"
            ):
                # Parse the direct_url.json to see if it's an editable install
                # (https://packaging.python.org/en/latest/specifications/direct-url/#example-pip-commands-and-their-effect-on-direct-url-json).
                with open(direct_url) as f:
                    info = json.load(f)
                if not info.get("dir_info", {}).get("editable", False):
                    continue

                # Extract the workspace path from the URL (e.g. `file///my/workspace/`).
                url = urlparse(info["url"])
                assert url.scheme == "file", f"expected file:// URL, got {url.scheme}"

                # Get the project name, so we can use it below to create a unique-ish
                # remote directory.
                dist = importlib.metadata.PathDistribution(direct_url.parent)
                name = dist.metadata["Name"]

                local = Path(url.path)

                # Check if we've already defined a workspace for this local path.
                existing = workspaces.get(local)
                if existing is not None:
                    assert existing.method == CodeSyncMethod.Rsync()
                    remote = existing.remote
                else:
                    # Otherwise, add the workspace to the list.
                    remote = RemoteWorkspace(
                        location=WorkspaceLocation.FromEnvVar(
                            env="WORKSPACE_DIR",
                            relpath=f"__editable__.{name}",
                        ),
                        shape=WorkspaceShape.shared("gpus"),
                    )
                    workspaces[local] = WorkspaceConfig(
                        local=local,
                        remote=remote,
                        method=CodeSyncMethod.Rsync(),
                    )

                logging.info(
                    f"Syncing editable install of {name} from {local} (to {remote.location})"
                )

                # Make sure we fixup path prefixes to the editable install.
                conda_prefix_replacements[local] = remote.location

            workspaces[conda_prefix] = WorkspaceConfig(
                local=conda_prefix,
                remote=RemoteWorkspace(
                    location=WorkspaceLocation.FromEnvVar(
                        env="CONDA_PREFIX",
                        relpath="",
                    ),
                    shape=WorkspaceShape.shared("gpus"),
                ),
                method=CodeSyncMethod.CondaSync(conda_prefix_replacements),
            )

        assert self._code_sync_client is not None
        await self._code_sync_client.sync_workspaces(
            instance=context().actor_instance._as_rust(),
            workspaces=list(workspaces.values()),
            auto_reload=auto_reload,
        )

    @classmethod
    def from_alloc(
        self,
        alloc: AllocHandle,
        setup: Callable[[], None] | None = None,
        _attach_controller_controller: bool = True,
    ) -> "ProcMesh":
        warnings.warn(
            (
                "DEPRECATION WARNING: this function will soon be unsupported. "
                "Use `HostMesh.allocate_nonblocking(...).spawn_procs(...)` instead."
            ),
            DeprecationWarning,
            stacklevel=2,
        )

        from monarch._src.actor.host_mesh import HostMesh

        return HostMesh.allocate_nonblocking(
            "host_mesh_from_alloc",
            Extent(*zip(*alloc._extent.items())),
            alloc._allocator,
            alloc._constraints,
        ).spawn_procs(bootstrap=setup)


class _ControllerController(Actor):
    def __init__(self) -> None:
        self._controllers: Dict[str, Actor] = {}

    # pyre-ignore
    @endpoint
    def get_or_spawn(
        self,
        self_ref: "_ControllerController",  # This is actually an ActorMesh[_ControllerController]
        name: str,
        Class: Type[TActor],
        *args: Any,
        **kwargs: Any,
    ) -> TActor:
        if name not in self._controllers:
            from monarch._src.actor.v1.host_mesh import this_proc

            proc = this_proc()
            proc._controller_controller = self_ref
            self._controllers[name] = proc.spawn(name, Class, *args, **kwargs)
        return cast(TActor, self._controllers[name])


# Lazy init so that the controller_controller and does not produce logs when it isn't used.
# Checking for the controller (when it does not already exist in the MonarchContext) needs a lock,
# otherwise two initializing procs will both try to init resulting in duplicates. The critical
# region is not blocking: it spawns a separate task to do the init, assigns the
# Shared[_ControllerController] from that task to the global and releases the lock.
_controller_controller: _Lazy[_ControllerController] = _Lazy(
    lambda: context().actor_instance.proc_mesh.spawn(
        "controller_controller", _ControllerController
    )
)


def _get_controller_controller() -> "Tuple[ProcMesh, _ControllerController]":
    return context().actor_instance.proc_mesh, _controller_controller.get()


def get_or_spawn_controller(
    name: str, Class: Type[TActor], *args: Any, **kwargs: Any
) -> Future[TActor]:
    """
    Creates a singleton actor (controller) indexed by name, or if it already exists, returns the
    existing actor.

    Args:
        name (str): The unique name of the actor, used as a key for retrieval.
        Class (Type): The class of the actor to spawn. Must be a subclass of Actor.
        *args (Any): Positional arguments to pass to the actor constructor.
        **kwargs (Any): Keyword arguments to pass to the actor constructor.

    Returns:
        A Future that resolves to a reference to the actor.
    """
    cc = context().actor_instance._controller_controller
    return cc.get_or_spawn.call_one(cc, name, Class, *args, **kwargs)


def proc_mesh(
    *,
    gpus: Optional[int] = None,
    hosts: int = 1,
    env: dict[str, str] | None = None,
    setup: Callable[[], None] | None = None,
) -> ProcMesh:
    """
    [DEPRECATED] Create a distributed process mesh across hosts.

    This function creates a process mesh using distributed process allocation
    across multiple hosts and GPUs. Used for production distributed computing.

    Args:
        gpus: Number of GPUs per host. If None, uses local device count.
        hosts: Number of hosts to allocate. Defaults to 1.
        env: Environment variables to set on remote processes.
        setup: Optional setup function to run on each process at startup.

    Returns:
        ProcMesh: A distributed process mesh with the specified configuration.

    Warning:
        This function is deprecated. Use `this_host().spawn_procs()` with
        appropriate per_host configuration instead.
    """
    warnings.warn(
        (
            "DEPRECATION WARNING: this function will soon be unsupported. "
            "Use this_host().spawn_procs(per_host = {'hosts': 2, 'gpus': 3}) "
            "instead of monarch.actor.proc_mesh(hosts=2, gpus=3)."
        ),
        DeprecationWarning,
        stacklevel=2,
    )

    if env is not None and len(env) > 0:
        raise ValueError(
            "`env` is not supported for `proc_mesh(...)`, and you shouldn't be using this function anyway. "
            "Use `this_host().spawn_procs(per_host = {'hosts': ..., 'gpus': ...})` instead."
        )

    from monarch._src.actor.host_mesh import this_host

    return this_host().spawn_procs(
        per_host={"hosts": hosts, "gpus": gpus if gpus else _local_device_count()},
        bootstrap=setup,
    )


def local_proc_mesh(*, gpus: Optional[int] = None, hosts: int = 1) -> ProcMesh:
    """
    [DEPRECATED] Create a local process mesh for testing and development.

    This function creates a process mesh using local allocation instead of
    distributed process allocation. Primarily used for testing scenarios.

    Args:
        gpus: Number of GPUs to allocate per host. If None, uses local device count.
        hosts: Number of hosts to allocate. Defaults to 1.

    Returns:
        ProcMesh: A locally allocated process mesh.

    Warning:
        This function is deprecated. Use `fake_in_process_host().spawn_procs()`
        for testing or `this_proc().spawn_procs()` for current process actors.
    """
    warnings.warn(
        (
            "DEPRECATION WARNING: this function will soon be unsupported. "
            "Use monarch._src.actor.host_mesh.fake_in_process_host().spawn_procs "
            "for testing. For launching an actor in the current process use "
            "this_proc().spawn_procs()."
        ),
        DeprecationWarning,
        stacklevel=2,
    )

    from monarch._src.actor.host_mesh import fake_in_process_host

    return fake_in_process_host().spawn_procs(
        per_host={"hosts": hosts, "gpus": gpus if gpus else _local_device_count()},
    )


def sim_proc_mesh(
    *,
    gpus: int = 1,
    hosts: int = 1,
    racks: int = 1,
    zones: int = 1,
    dcs: int = 1,
    regions: int = 1,
) -> ProcMesh:
    """Create a simulated process mesh for testing distributed scenarios.

    This function creates a process mesh using simulation allocation to test
    distributed behavior without requiring actual remote resources.

    Args:
        gpus: Number of GPUs per host. Defaults to 1.
        hosts: Number of hosts. Defaults to 1.
        racks: Number of racks. Defaults to 1.
        zones: Number of zones. Defaults to 1.
        dcs: Number of data centers. Defaults to 1.
        regions: Number of regions. Defaults to 1.

    Returns:
        ProcMesh: A simulated process mesh with the specified topology.
    """
    from monarch._src.actor.host_mesh import HostMesh

    host_mesh = HostMesh.allocate_nonblocking(
        "sim",
        Extent(
            ["regions", "dcs", "zones", "racks", "hosts"],
            [regions, dcs, zones, racks, hosts],
        ),
        SimAllocator(),
        AllocConstraints(),
    )
    return host_mesh.spawn_procs(per_host={"gpus": gpus})

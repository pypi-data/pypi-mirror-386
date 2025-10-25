# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# pyre-strict
import logging
import time
from logging import Logger
from typing import Any, Callable, Optional, Protocol

from monarch._rust_bindings.monarch_extension.client import (  # @manual=//monarch/monarch_extension:monarch_extension
    ClientActor,
    SystemSnapshotFilter,
)

from monarch._rust_bindings.monarch_hyperactor.proc import (  # @manual=//monarch/monarch_extension:monarch_extension
    ActorId,
    init_proc,
    Proc,
)

from monarch._src.actor.shape import NDSlice
from monarch.common.client import Client
from monarch.common.device_mesh import DeviceMesh, DeviceMeshStatus
from monarch.common.invocation import DeviceException, RemoteException
from monarch.common.mast import MastJob
from monarch.controller.rust_backend.controller import RustController

TORCHX_MAST_TASK_GROUP_NAME = "script"

logger: Logger = logging.getLogger(__name__)

# A world tuple contains a worker world name and a controller actor id
# The pair forms a functional world that can be used to create a device mesh
MeshWorld = tuple[str, ActorId]

# Taken from //monarch/controller/src/bootstrap.rs
WORLD_WORKER_LABEL = "world.monarch.meta.com/worker"
WORLD_CONTROLLER_LABEL = "world.monarch.meta.com/controllerActorId"
WORLD_CONTROLLER_IP = "world.monarch.meta.com/ip_addr"


class IBootstrap(Protocol):
    def get_mesh_worlds(self) -> list[MeshWorld]:
        """Returns the list of mesh worlds."""
        ...

    def kill_mesh(self, mesh_world: MeshWorld) -> None:
        """Kills a mesh in a bootstrap instance."""
        ...

    def spawn_mesh(self, mesh_world: MeshWorld) -> None:
        """Spawns a mesh in a bootstrap instance."""
        ...


class IPoolDeviceMeshProvider(Protocol):
    def new_mesh(self, timeout_in_sec: Optional[int] = None) -> DeviceMesh:
        raise NotImplementedError()


class PoolDeviceMeshProvider:
    """
    Given a client actor, the device mesh provider discovers and keeps track of
    the world status and provides a device mesh given a healthy world.
    """

    def __init__(
        self,
        hosts: int,
        gpus: int,
        proc: Proc,
    ) -> None:
        self._hosts = hosts
        self._gpus = gpus
        self._mesh_map: dict[MeshWorld, DeviceMesh | None] = {}
        self._create_count = 0
        self._proc = proc
        # Root client is not used to create device meshes.
        # It is only used to pull the world status.
        self._root_client: ClientActor = ClientActor(
            proc=self._proc,
            actor_name="root_client",  # The client name really doesn't matter
        )

    def new_mesh(self, timeout_in_sec: Optional[int] = None) -> DeviceMesh:
        """
        Creates a new device mesh based on the current world status.
        If no healthy world is found, the call will block until a healthy world is found
        or timeout_in_sec is reached.xtimeout_in_sec being None indicates no timeout.
        """

        logger.info("Trying to allocate a new mesh in its desired world...")

        def _create_exit(
            client: Client,
        ) -> Callable[[Optional[RemoteException | DeviceException | Exception]], None]:
            def _exit(
                error: Optional[RemoteException | DeviceException | Exception] = None,
            ) -> None:
                client.shutdown(True, error)

            return _exit

        def _is_world_healthy(world_status: dict[str, str], target_world: str) -> bool:
            return (
                target_world in world_status
                and DeviceMeshStatus(world_status[target_world])
                == DeviceMeshStatus.LIVE
            )

        now = time.time()
        while timeout_in_sec is None or time.time() - now < timeout_in_sec:
            # Pull the fresh world status
            self._refresh_worlds()
            world_status = self._root_client.world_status()
            self._remove_evicted_worlds(world_status)

            # Find the next available world
            for mesh_world, mesh in self._mesh_map.items():
                if mesh is not None:
                    # Mesh has been allocated to this world, skip
                    continue

                worker_world, controller_id = mesh_world
                controller_world = controller_id.world_name

                if (not _is_world_healthy(world_status, worker_world)) or (
                    not _is_world_healthy(world_status, controller_world)
                ):
                    # Either controller world is not ready or worker world is not ready
                    continue

                # Previously this grafted a child actor ("new_with_parent") to the root client.
                # This is not a legal thing to do to: instead, we create a unique controller
                # actor name based on the root client.
                controller_actor_name = f"{self._root_client.actor_id.actor_name}.backend_controller_{self._create_count}"
                self._create_count += 1
                backend_ctrl = RustController(
                    proc=self._proc,
                    client_actor=ClientActor(self._proc, controller_actor_name),
                    controller_id=controller_id,
                    worker_world_name=worker_world,
                )
                client = Client(backend_ctrl, self._hosts * self._gpus, self._gpus)

                # TODO: we need to consider hosts and gpus constraints as well
                dm = DeviceMesh(
                    client,
                    NDSlice(
                        offset=0,
                        sizes=[self._hosts, self._gpus],
                        strides=[self._gpus, 1],
                    ),
                    ("host", "gpu"),
                    worker_world,
                )
                dm.exit = _create_exit(client)
                self._mesh_map[mesh_world] = dm

                logger.info("Mesh successfully allocated in world: %s", worker_world)

                return dm

            # TODO(T216841374): Change to healthy world push based checks
            sleep_sec = 0.05
            logger.debug(f"No healthy world found, sleeping for {sleep_sec}s...")
            time.sleep(sleep_sec)

        raise TimeoutError(f"Could not find a healthy world in {timeout_in_sec}s!")

    def _refresh_worlds(self) -> None:
        system_snapshot = self._root_client.world_state(
            filter=SystemSnapshotFilter(world_labels={WORLD_WORKER_LABEL: "1"})
        )
        for world_id, world_snapshot in system_snapshot.items():
            if WORLD_CONTROLLER_LABEL not in world_snapshot.labels:
                continue
            controller_actor_id = ActorId.from_string(
                world_snapshot.labels[WORLD_CONTROLLER_LABEL]
            )
            world_tuple = (world_id, controller_actor_id)
            if world_tuple not in self._mesh_map:
                logger.debug(f"Discovered new worker world {world_id}")
                self._mesh_map[world_tuple] = None

    def _remove_evicted_worlds(self, world_status: dict[str, str]) -> None:
        """
        Go through the mesh map and remove the world that has already been evicted by the system.
        """
        mesh_worlds_to_remove = []
        for mesh_world, _ in self._mesh_map.items():
            worker_world, controller_id = mesh_world
            controller_world = controller_id.world_name

            if (
                world_status.get(worker_world) is None
                or world_status.get(controller_world) is None
            ):
                logger.debug(f"Removing Evicted world {mesh_world}")
                mesh_worlds_to_remove.append(mesh_world)

        for mesh_world in mesh_worlds_to_remove:
            self._mesh_map.pop(mesh_world)


def rust_mast_mesh(
    job_name: str, system_port: int = 29500, **kwargs: Any
) -> DeviceMesh:
    job = MastJob(job_name, TORCHX_MAST_TASK_GROUP_NAME)
    if not job.is_running():
        job.wait_for_running(10 * 60)
    hostnames = job.get_hostnames()
    system_addr = f"metatls!{hostnames[0]}.facebook.com:{system_port}"
    return rust_backend_mesh(
        system_addr,
        **kwargs,
    )


def rust_backend_mesh(
    system_addr: str,
    hosts: int,
    gpus: int,
) -> DeviceMesh:
    dms = rust_backend_meshes(
        system_addr,
        hosts,
        gpus,
        requested_meshes=1,
    )
    assert len(dms) == 1
    return dms[0]


def rust_backend_meshes(
    system_addr: str,
    hosts: int,
    gpus: int,
    requested_meshes: int = 1,
) -> list[DeviceMesh]:
    """
    Given system system_addr, discover worlds registered and create a device mesh per
    world with hosts and gpus. The call will block until requested_meshes
    are discovered and created, or 1200s timeout is reached.
    Args:
        system_addr: the system address to connect to.
        hosts: number of hosts to create the device mesh with.
        gpus: number of gpus to create the device mesh with.
        requested_meshes: the minimum number of meshes to create.
    """
    mesh_provider = rust_backend_mesh_provider(system_addr, hosts, gpus)
    dms: list[DeviceMesh] = []

    # Given a client actor and a list of world names, wait for all the worlds to be ready.
    max_timeout_in_sec = 1200
    start_time = time.time()
    while True:
        if time.time() - start_time > max_timeout_in_sec:
            raise TimeoutError(
                f"Timeout ({max_timeout_in_sec} sec) waiting for all worlds to be ready."
            )
        mesh = mesh_provider.new_mesh()
        dms.append(mesh)
        if len(dms) == requested_meshes:
            return dms


def rust_backend_mesh_provider(
    system_addr: str,
    hosts: int,
    gpus: int,
    client_proc_id: str = "client[0]",
    # pyre-fixme[11]: Annotation `DeviceMeshProvider` is not defined as a type.
) -> PoolDeviceMeshProvider:
    proc: Proc = init_proc(
        proc_id=client_proc_id,
        bootstrap_addr=system_addr,
        timeout=5,
        supervision_update_interval=5,
    )
    return PoolDeviceMeshProvider(hosts, gpus, proc)

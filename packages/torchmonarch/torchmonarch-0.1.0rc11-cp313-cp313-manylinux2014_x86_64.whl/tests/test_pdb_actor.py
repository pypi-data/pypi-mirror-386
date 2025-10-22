# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# pyre-unsafe
import sys
import traceback

import pytest
import torch

from monarch import fetch_shard, remote
from monarch._rust_bindings.monarch_extension.client import (  # @manual=//monarch/monarch_extension:monarch_extension
    ClientActor,
    DebuggerMessage as ClientDebuggerMessage,
)
from monarch._rust_bindings.monarch_extension.debugger import (
    DebuggerMessage as PdbDebuggerMessage,
    get_bytes_from_write_action,
)
from monarch._rust_bindings.monarch_messages.debugger import DebuggerAction
from monarch.actor import this_host
from monarch_supervisor.logging import fix_exception_lines


def custom_excepthook(exc_type, exc_value, exc_traceback):
    tb_lines = fix_exception_lines(
        traceback.format_exception(exc_type, exc_value, exc_traceback)
    )
    print("\n".join(tb_lines), file=sys.stderr)


sys.excepthook = custom_excepthook


remote_test_pdb_actor = remote(
    "monarch.worker._testing_function.test_pdb_actor",
    propagate=lambda: torch.zeros(1),
)


@pytest.mark.skipif(
    torch.cuda.device_count() < 2,
    reason="Not enough GPUs, this test requires at least 2 GPUs",
)
# Set global timeout--sandcastle's timeout is 600s. A test that sandcastle times
# out is not counted as a failure, so we set a more restrictive timeout to
# ensure we see a hard failure in CI.
@pytest.mark.timeout(120)
class TestPdbActor:
    def test_pdb_actor(self):
        # Use modern mesh pattern from distributed_tensors.py
        mesh = this_host().spawn_procs({"gpu": 1})

        with mesh.activate():
            client = mesh.client.inner._actor
            assert isinstance(client, ClientActor)
            fut = fetch_shard(remote_test_pdb_actor())
            msg = client.get_next_message(timeout_msec=None)
            assert isinstance(msg, ClientDebuggerMessage)
            assert isinstance(msg.action, DebuggerAction.Paused)
            client.send(
                msg.debugger_actor_id,
                PdbDebuggerMessage(action=DebuggerAction.Attach()).serialize(),
            )
            msg = client.get_next_message(timeout_msec=None)
            assert isinstance(msg, ClientDebuggerMessage)
            assert isinstance(msg.action, DebuggerAction.Read)
            assert msg.action.requested_size == 4
            client.send(
                msg.debugger_actor_id,
                PdbDebuggerMessage(action=DebuggerAction.Write(b"1234")).serialize(),
            )
            msg = client.get_next_message(timeout_msec=None)
            assert isinstance(msg, ClientDebuggerMessage)
            assert isinstance(msg.action, DebuggerAction.Write)
            assert get_bytes_from_write_action(msg.action) == b"5678"
            client.send(
                msg.debugger_actor_id,
                PdbDebuggerMessage(action=DebuggerAction.Detach()).serialize(),
            )
            fut.result()

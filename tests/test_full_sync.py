import asyncio
import time

import pytest

from src.types.peer_info import PeerInfo
from src.protocols import peer_protocol
from src.util.ints import uint16
from tests.setup_nodes import setup_two_nodes, test_constants, bt


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop


class TestFullSync:
    @pytest.fixture(scope="function")
    async def two_nodes(self):
        async for _ in setup_two_nodes():
            yield _

    @pytest.mark.asyncio
    async def test_basic_sync(self, two_nodes):
        num_blocks = 100
        blocks = bt.get_consecutive_blocks(test_constants, num_blocks, [], 10)
        full_node_1, full_node_2, server_1, server_2 = two_nodes

        for i in range(1, num_blocks):
            async for _ in full_node_1.block(peer_protocol.Block(blocks[i])):
                pass

        await server_2.start_client(
            PeerInfo(server_1._host, uint16(server_1._port)), None
        )

        await asyncio.sleep(2)  # Allow connections to get made
        start_unf = time.time()

        while time.time() - start_unf < 60:
            # The second node should eventually catch up to the first one, and have the
            # same tip at height num_blocks - 1.
            if (
                max([h.height for h in full_node_2.blockchain.get_current_tips()])
                == num_blocks - 1
            ):
                print(f"Time taken to sync {num_blocks} is {time.time() - start_unf}")

                return
            await asyncio.sleep(0.1)

        raise Exception("Took too long to process blocks")

    @pytest.mark.asyncio
    async def test_short_sync(self, two_nodes):
        num_blocks = 10
        num_blocks_2 = 4
        blocks = bt.get_consecutive_blocks(test_constants, num_blocks, [], 10)
        blocks_2 = bt.get_consecutive_blocks(
            test_constants, num_blocks_2, [], 10, seed=b"123"
        )
        full_node_1, full_node_2, server_1, server_2 = two_nodes

        # 10 blocks to node_1
        for i in range(1, num_blocks):
            async for _ in full_node_1.block(peer_protocol.Block(blocks[i])):
                pass
        # 4 different blocks to node_2
        for i in range(1, num_blocks_2):
            async for _ in full_node_2.block(peer_protocol.Block(blocks_2[i])):
                pass

        # 6th block from node_1 to node_2
        async for _ in full_node_2.block(peer_protocol.Block(blocks[5])):
            pass

        await server_2.start_client(
            PeerInfo(server_1._host, uint16(server_1._port)), None
        )
        await asyncio.sleep(2)  # Allow connections to get made

        start_unf = time.time()

        while time.time() - start_unf < 30:
            # The second node should eventually catch up to the first one, and have the
            # same tip at height num_blocks - 1.
            if (
                max([h.height for h in full_node_2.blockchain.get_current_tips()])
                == num_blocks - 1
            ):
                print(f"Time taken to sync {num_blocks} is {time.time() - start_unf}")
                return
            await asyncio.sleep(0.1)

        raise Exception("Took too long to process blocks")

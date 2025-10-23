# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import heapq
from cosmos_rl.utils.logging import logger
import cosmos_rl.utils.distributed as dist_util
from cosmos_rl.utils.distributed import HighAvailabilitylNccl
import torch


def karmarkar_karp(seqlen_list: list[int], k_partitions: int, equal_size: bool):
    # Karmarkar-Karp differencing method for k-partition problem: https://en.wikipedia.org/wiki/Largest_differencing_method
    # Implementation Reference: https://github.com/volcengine/verl/blob/main/verl/utils/seqlen_balancing.py#L27
    class Set:
        def __init__(self) -> None:
            self.sum = 0
            self.items = []

        def add(self, idx: int, val: int):
            self.items.append((idx, val))
            self.sum += val

        def merge(self, other):
            for idx, val in other.items:
                self.items.append((idx, val))
                self.sum += val

        def __lt__(self, other):
            if self.sum != other.sum:
                return self.sum < other.sum
            if len(self.items) != len(other.items):
                return len(self.items) < len(other.items)
            return self.items < other.items

    class State:
        def __init__(self, items: list[tuple[int, int]], k: int) -> None:
            self.k = k
            # sets should always be decreasing order
            self.sets = [Set() for _ in range(k)]
            assert len(items) in [1, k], f"{len(items)} not in [1, {k}]"
            for i, (idx, seqlen) in enumerate(items):
                self.sets[i].add(idx=idx, val=seqlen)
            self.sets = sorted(self.sets, reverse=True)

        def get_partitions(self):
            partitions = []
            for i in range(len(self.sets)):
                cur_partition = []
                for idx, _ in self.sets[i].items:
                    cur_partition.append(idx)
                partitions.append(cur_partition)
            return partitions

        def merge(self, other):
            for i in range(self.k):
                self.sets[i].merge(other.sets[self.k - 1 - i])
            self.sets = sorted(self.sets, reverse=True)

        @property
        def spread(self) -> int:
            return self.sets[0].sum - self.sets[-1].sum

        def __lt__(self, other):
            # least heap, let the state with largest spread to be popped first,
            # if the spread is the same, let the state who has the largest set
            # to be popped first.
            if self.spread != other.spread:
                return self.spread > other.spread
            return self.sets[0] > other.sets[0]

        def __repr__(self) -> str:
            repr_str = "["
            for i in range(self.k):
                if i > 0:
                    repr_str += ","
                repr_str += "{"
                for j, (_, seqlen) in enumerate(self.sets[i].items):
                    if j > 0:
                        repr_str += ","
                    repr_str += str(seqlen)
                repr_str += "}"
            repr_str += "]"
            return repr_str

    sorted_seqlen_list = sorted([(seqlen, i) for i, seqlen in enumerate(seqlen_list)])
    states_pq = []
    if equal_size:
        assert (
            len(seqlen_list) % k_partitions == 0
        ), f"{len(seqlen_list)} % {k_partitions} != 0"
        for offset in range(0, len(sorted_seqlen_list), k_partitions):
            items = []
            for i in range(k_partitions):
                seqlen, idx = sorted_seqlen_list[offset + i]
                items.append((idx, seqlen))
            heapq.heappush(states_pq, State(items=items, k=k_partitions))
    else:
        for seqlen, idx in sorted_seqlen_list:
            heapq.heappush(states_pq, State(items=[(idx, seqlen)], k=k_partitions))

    while len(states_pq) > 1:
        state0 = heapq.heappop(states_pq)
        state1 = heapq.heappop(states_pq)
        # merge states
        state0.merge(state1)
        heapq.heappush(states_pq, state0)

    final_state = states_pq[0]
    partitions = final_state.get_partitions()
    if equal_size:
        for i, partition in enumerate(partitions):
            assert len(partition) * k_partitions == len(
                seqlen_list
            ), f"{len(partition)} * {k_partitions} != {len(seqlen_list)}"
    return partitions


# Refer to: https://github.com/volcengine/verl/blob/main/verl/utils/seqlen_balancing.py#L151
def get_seqlen_balanced_partitions(
    seqlen_list: list[int], k_partitions: int, equal_size: bool
):
    """
    Calculates partitions of indices from seqlen_list such that the sum of sequence lengths
    in each partition is balanced. Uses the Karmarkar-Karp differencing method.

    This is useful for balancing workload across devices or batches, especially when
    dealing with variable sequence lengths.

    Args:
        seqlen_list (List[int]): A list of sequence lengths for each item.
        k_partitions (int): The desired number of partitions.
        equal_size (bool): If True, ensures that each partition has the same number of items.
                           Requires len(seqlen_list) to be divisible by k_partitions.
                           If False, partitions can have varying numbers of items, focusing
                           only on balancing the sum of sequence lengths.

    Returns:
        List[List[int]]: A list containing k_partitions lists. Each inner list contains the
                         original indices of the items assigned to that partition. The indices
                         within each partition list are sorted.

    Raises:
        AssertionError: If len(seqlen_list) < k_partitions.
        AssertionError: If equal_size is True and len(seqlen_list) is not divisible by k_partitions.
        AssertionError: If any resulting partition is empty.
    """
    assert (
        len(seqlen_list) >= k_partitions
    ), f"number of items:[{len(seqlen_list)}] < k_partitions:[{k_partitions}]"

    def _check_and_sort_partitions(partitions):
        assert len(partitions) == k_partitions, f"{len(partitions)} != {k_partitions}"
        seen_idx = set()
        sorted_partitions = [None] * k_partitions
        for i, partition in enumerate(partitions):
            assert len(partition) > 0, f"the {i}-th partition is empty"
            for idx in partition:
                seen_idx.add(idx)
            sorted_partitions[i] = sorted(partition)
        assert seen_idx == set(range(len(seqlen_list)))
        return sorted_partitions

    partitions = karmarkar_karp(
        seqlen_list=seqlen_list, k_partitions=k_partitions, equal_size=equal_size
    )
    return _check_and_sort_partitions(partitions)


def ceildiv(a, b):
    return -(a // -b)


# Modified based on: https://github.com/volcengine/verl/blob/main/verl/utils/seqlen_balancing.py#L251
def rearrange_mini_batches(
    batch,
    seq_len_effective: list[int],
    max_token_len: int,
    dp_group=None,
    same_mini_num_in_dp=True,
    min_num_mini_batch=None,
    use_dynamic_bsz_balance=True,
    ddp_comm: HighAvailabilitylNccl = None,
):
    """
    Split a batch into mini-batches by total token count, with optional DP sync and padding.

    Args:
        batch (TensorDict): mini-batch data to be split into mini-batches.
        seq_len_effective (List[int]): list of effective sequence lengths for each item in the batch.
        max_token_len (int): max sum of effective tokens per mini-batch.
        dp_group (optional): torch.distributed group for data-parallel sync.
        same_mini_num_in_dp (bool): if True and dp_group set, pad all ranks to the same count.
        min_num_mini_batch (int, optional): force at least this many splits (pads empty ones).
        use_dynamic_bsz_balance (bool, optional): balance the computational workload between mini-batches.
        ddp_comm: HighAvailabilitylNccl = None, optional DDP communicator for distributed operations.
    Returns:
        List[List[Any]]: the mini-batches after rearrangement.
        List[List[int]]: index lists mapping each mini-batch back to original positions.
    """
    # this is per local mini_bsz
    max_seq_len = max(seq_len_effective)
    if max_token_len < max_seq_len:
        logger.warning(
            f"max_token_len[{max_token_len}] < max_seq_len[{max_seq_len}], "
            f"setting max_token_len = max_seq_len"
        )
        max_token_len = max_seq_len
    total_seqlen = sum(seq_len_effective)
    num_mini_batches = min(len(seq_len_effective), ceildiv(total_seqlen, max_token_len))
    if min_num_mini_batch is not None:
        num_mini_batches = max(min_num_mini_batch, num_mini_batches)
    if same_mini_num_in_dp:
        num_mini_batches = max(
            dist_util.all_gather_object_cpu(num_mini_batches, group=dp_group)
        )

    if ddp_comm is not None:
        num_mini_batches_tensor = torch.tensor(num_mini_batches, device="cuda")
        ddp_comm.allreduce(
            num_mini_batches_tensor,
            num_mini_batches_tensor,
            op=torch.distributed.ReduceOp.MAX,
        )
        num_mini_batches = num_mini_batches_tensor.item()

    assert num_mini_batches <= len(seq_len_effective)
    mini_bsz_idx = get_seqlen_balanced_partitions(
        seq_len_effective, num_mini_batches, equal_size=False
    )

    if use_dynamic_bsz_balance:
        # Use the sum of squared sequence lengths to approximate attention computation workload
        mini_bsz_idx.sort(
            key=lambda partition: (
                sum(seq_len_effective[idx] ** 2 for idx in partition),
                min(partition) if partition else 0,
            ),
            reverse=True,
        )

    mini_batches = []

    for partition in mini_bsz_idx:
        curr_mini_batch = []
        for idx in partition:
            curr_mini_batch.append(batch[idx])
        mini_batches.append(curr_mini_batch)

    return mini_batches, mini_bsz_idx

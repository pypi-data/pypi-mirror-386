import copy
import json
import logging
import random
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Mapping, Optional, Sequence, Tuple

import numpy as np

from ..actions import MbagAction, MbagActionTuple, MbagActionType
from ..blocks import MinecraftBlocks
from ..config import ItemDict, MbagConfigDict
from ..types import WorldLocation
from .ai_actions import (
    MalmoAIAction,
    MalmoGiveAIAction,
    MalmoMoveAIAction,
    MalmoPlaceBreakAIAction,
    get_state_diffs_for_ai_action,
)
from .malmo_client import INVENTORY_SLOT_NAMES, MalmoClient, MalmoObservationDict
from .malmo_state import (
    BlockDiff,
    InventoryDiff,
    LocationDiff,
    MalmoState,
    MalmoStateDiff,
    ReadOnlyDict,
    ReadOnlyList,
    get_initial_malmo_state,
    update_malmo_state,
)
from .thread_utils import wrap_thread_to_handle_exceptions

logger = logging.getLogger(__name__)


def _get_human_actions_from_block_diff(
    new_state: MalmoState,
    state_diff: BlockDiff,
    prev_blocks_on_ground: Sequence[Mapping[int, int]],
    palette_x: Optional[int],
    env_config: MbagConfigDict,
) -> Tuple[List[Tuple[int, MbagActionTuple]], Sequence[Mapping[int, int]]]:
    num_players = env_config["num_players"]

    new_blocks_on_ground = [
        defaultdict(int, blocks_on_ground) for blocks_on_ground in prev_blocks_on_ground
    ]

    action_type: Optional[MbagActionType] = None
    if (
        new_state.player_last_breaking[state_diff.location] != -1
        and state_diff.new_block == MinecraftBlocks.AIR
    ):
        player_index = new_state.player_last_breaking[state_diff.location]
        action_type = MbagAction.BREAK_BLOCK
        assert state_diff.prev_block != MinecraftBlocks.AIR
        new_blocks_on_ground[player_index][state_diff.prev_block] += 1
    if (
        state_diff.new_block != MinecraftBlocks.AIR
        and state_diff.location[0] != palette_x
    ):
        player_index = new_state.player_last_placing[state_diff.location]
        if player_index == -1:
            # If there is no player recorded as last placing a block here, then
            # use heuristic to figure out who placed it. Heuristic is:
            #  - remove non-human players from consideration
            #  - pick the nearest human player

            closest_squared_distance = float("inf")
            for possible_player_index in range(num_players):
                player_x, player_y, player_z = new_state.player_locations[
                    possible_player_index
                ]
                block_x, block_y, block_z = state_diff.location
                squared_distance = (
                    (player_x - block_x) ** 2
                    + (player_y - block_y) ** 2
                    + (player_z - block_z) ** 2
                )
                if squared_distance < closest_squared_distance:
                    closest_squared_distance = squared_distance
                    player_index = possible_player_index

        if player_index != -1:
            action_type = MbagAction.PLACE_BLOCK
            new_blocks_on_ground[player_index][state_diff.new_block] -= 1

    if action_type is not None:
        world_size = new_state.blocks.size
        block_location_index = int(
            np.ravel_multi_index(state_diff.location, world_size)
        )
        human_actions: List[Tuple[int, MbagActionTuple]] = [
            (
                player_index,
                (action_type, block_location_index, state_diff.new_block),
            )
        ]
        return human_actions, new_blocks_on_ground
    else:
        return [], new_blocks_on_ground


def _get_human_actions_from_location_diff(
    state_diff: LocationDiff,
) -> List[Tuple[int, MbagActionTuple]]:
    human_actions: List[Tuple[int, MbagActionTuple]] = []

    current_x, current_y, current_z = state_diff.prev_location
    current_x, current_y, current_z = int(current_x), int(current_y), int(current_z)
    new_x, new_y, new_z = state_diff.new_location
    new_x, new_y, new_z = int(new_x), int(new_y), int(new_z)

    while current_x < new_x:
        human_actions.append((state_diff.player_index, (MbagAction.MOVE_POS_X, 0, 0)))
        current_x += 1
    while current_x > new_x:
        human_actions.append((state_diff.player_index, (MbagAction.MOVE_NEG_X, 0, 0)))
        current_x -= 1
    while current_y < new_y:
        human_actions.append((state_diff.player_index, (MbagAction.MOVE_POS_Y, 0, 0)))
        current_y += 1
    while current_y > new_y:
        human_actions.append((state_diff.player_index, (MbagAction.MOVE_NEG_Y, 0, 0)))
        current_y -= 1
    while current_z < new_z:
        human_actions.append((state_diff.player_index, (MbagAction.MOVE_POS_Z, 0, 0)))
        current_z += 1
    while current_z > new_z:
        human_actions.append((state_diff.player_index, (MbagAction.MOVE_NEG_Z, 0, 0)))
        current_z -= 1

    return human_actions


def _get_human_actions_from_inventory_diff(
    new_state: MalmoState,
    state_diff: InventoryDiff,
    prev_blocks_on_ground: Sequence[Mapping[int, int]],
    env_config: MbagConfigDict,
) -> Tuple[List[Tuple[int, MbagActionTuple]], Sequence[Mapping[int, int]]]:
    num_players = env_config["num_players"]

    human_actions: List[Tuple[int, MbagActionTuple]] = []
    new_blocks_on_ground = [
        defaultdict(int, blocks_on_ground) for blocks_on_ground in prev_blocks_on_ground
    ]

    # Update the number of blocks this player has on the ground based on the
    # change in their inventory.
    new_blocks_on_ground[state_diff.player_index][state_diff.block_id] += (
        state_diff.prev_count - state_diff.new_count
    )

    # If they have negative blocks on the ground, this means they picked up more
    # than they "own". This leads to GIVE_BLOCK actions from other players.
    if (
        not env_config["abilities"]["inf_blocks"]
        and new_blocks_on_ground[state_diff.player_index][state_diff.block_id] < 0
    ):
        player_x, player_y, player_z = new_state.player_locations[
            state_diff.player_index
        ]
        player_x, player_y, player_z = int(player_x), int(player_y), int(player_z)
        player_location_index = int(
            np.ravel_multi_index((player_x, player_y, player_z), new_state.blocks.size)
        )
        other_player_indices = [
            other_player_index
            for other_player_index in range(num_players)
            if other_player_index != state_diff.player_index
        ]
        for other_player_index in other_player_indices:
            while (
                new_blocks_on_ground[other_player_index][state_diff.block_id] > 0
                and new_blocks_on_ground[state_diff.player_index][state_diff.block_id]
                < 0
            ):
                human_actions.append(
                    (
                        other_player_index,
                        (
                            MbagAction.GIVE_BLOCK,
                            player_location_index,
                            state_diff.block_id,
                        ),
                    )
                )
                new_blocks_on_ground[other_player_index][state_diff.block_id] -= 1
                new_blocks_on_ground[state_diff.player_index][state_diff.block_id] += 1

    if (
        not env_config["abilities"]["inf_blocks"]
        and new_blocks_on_ground[state_diff.player_index][state_diff.block_id] < 0
    ):
        block_str = MinecraftBlocks.ID2NAME[state_diff.block_id]
        logger.warning(
            f"player {state_diff.player_index} unexpectedly has "
            f"{new_blocks_on_ground[state_diff.player_index][state_diff.block_id]} "
            f"{block_str} blocks on the ground"
        )

    return human_actions, new_blocks_on_ground


def get_human_actions(
    new_state: MalmoState,
    state_diff: MalmoStateDiff,
    prev_blocks_on_ground: Sequence[Mapping[int, int]],
    env_config: MbagConfigDict,
    palette_x: Optional[int],
) -> Tuple[List[Tuple[int, MbagActionTuple]], Sequence[Mapping[int, int]]]:
    """
    Given the updated Malmo state and one state diff that led to that update, returns:
        - a list of (player_index, action) tuples representing human actions that
            correspond to the given state diff
        - the updated blocks_on_ground list
    """

    if isinstance(state_diff, BlockDiff):
        return _get_human_actions_from_block_diff(
            new_state,
            state_diff,
            prev_blocks_on_ground,
            palette_x,
            env_config,
        )
    elif isinstance(state_diff, LocationDiff):
        human_actions = _get_human_actions_from_location_diff(state_diff)
        return (human_actions, prev_blocks_on_ground)
    elif isinstance(state_diff, InventoryDiff):
        return _get_human_actions_from_inventory_diff(
            new_state, state_diff, prev_blocks_on_ground, env_config
        )


class MalmoInterface:
    _malmo_state: MalmoState
    """The current state of the Malmo environment."""

    _expected_state_diffs: List[MalmoStateDiff]
    """
    These are state diffs that are expected to be seen in the Malmo observations
    because of AI actions.
    """

    _expected_state_diffs_lock: threading.Lock

    _human_action_queue: List[Tuple[int, MbagActionTuple]]
    """Queue of human actions that have been detected in the Malmo observations."""

    _malmo_state_and_human_actions_lock: threading.Lock

    _ai_action_queue: List[Tuple[int, MalmoAIAction]]
    """Queue of AI actions that need to be executed in Malmo."""

    _palette_x: Optional[int]

    _malmo_observations_lock: threading.Lock
    _malmo_observations: List[Tuple[datetime, int, MalmoObservationDict]]
    """
    List of (timestamp, player_index, malmo_observation) tuples. These are emptied and
    put into info dicts returned from MbagEnv.step.
    """

    _items_players_should_always_have: List[List[ItemDict]]

    def __init__(self, env_config: MbagConfigDict):
        self._env_config = env_config

        self._ai_action_queue = []
        self._ai_action_lock = threading.Condition()
        self._running_ai_actions = False
        self._running_ai_actions_lock = threading.Lock()

        self._human_action_queue = []
        self._malmo_state_and_human_actions_lock = threading.Lock()
        self._malmo_client = MalmoClient()
        self._malmo_lock = threading.Lock()

        self._expected_state_diffs_lock = threading.Lock()

        self._malmo_observations = []
        self._malmo_observations_lock = threading.Lock()

        self.episode_running = False

        if self._env_config["abilities"]["inf_blocks"]:
            self._palette_x = None
        else:
            self._palette_x = self._env_config["world_size"][0] - 1

    def _setup_malmo_mission(
        self,
        current_blocks: MinecraftBlocks,
        goal_blocks: MinecraftBlocks,
        player_locations: List[WorldLocation],
    ):
        with self._malmo_lock:
            self._malmo_client.start_mission(
                self._env_config, current_blocks, goal_blocks
            )
            time.sleep(1)  # Wait a second for the environment to load.

            self._items_players_should_always_have = []

            # Pre-episode setup in Malmo.
            for player_index in range(self._env_config["num_players"]):
                player_config = self._env_config["players"][player_index]
                if not player_config["is_human"]:
                    # Make players fly.
                    for _ in range(2):
                        self._malmo_client.send_command(player_index, "jump 1")
                        time.sleep(0.1)
                        self._malmo_client.send_command(player_index, "jump 0")
                        time.sleep(0.1)
                self._malmo_client.send_command(
                    player_index,
                    "tp " + " ".join(map(str, player_locations[player_index])),
                )
                time.sleep(0.1)

                items_player_should_always_have = list(player_config["give_items"])
                if (
                    self._env_config["abilities"]["inf_blocks"]
                    and player_config["is_human"]
                ):
                    for block_id, block_name in enumerate(MinecraftBlocks.ID2NAME):
                        if block_id in MinecraftBlocks.PLACEABLE_BLOCK_IDS:
                            items_player_should_always_have.append(
                                {
                                    "id": block_name,
                                    "count": 1,
                                    "enchantments": [],
                                }
                            )
                self._items_players_should_always_have.append(
                    items_player_should_always_have
                )

                # Give items to players.
                for item in items_player_should_always_have:
                    self._malmo_client.send_command(
                        player_index,
                        f"chat {self._get_give_command(player_index, item)}",
                    )
                    time.sleep(0.2)

            # Convert players to survival mode.
            for player_index in range(self._env_config["num_players"]):
                if self._env_config["players"][player_index]["is_human"]:
                    self._malmo_client.send_command(player_index, "chat /gamemode 0")

                # Disable chat messages from the palette
                self._malmo_client.send_command(
                    player_index, "chat /gamerule sendCommandFeedback false"
                )

            # Wait for everything to run.
            time.sleep(1)

    def _get_give_command(self, player_index: int, item: ItemDict) -> str:
        if "enchantments" not in item:
            item["enchantments"] = []

        for enchantment in item["enchantments"]:
            assert "id" in enchantment
            if "level" not in enchantment:
                enchantment["level"] = 32767

        give_args: List[str] = [
            self._malmo_client.get_player_name(player_index, self._env_config),
            item["id"],
            str(item["count"]),
            "0",
        ]

        if item["enchantments"]:
            enchantments_str = ",".join(
                [
                    "{{id: {}, lvl: {}}}".format(
                        enchantment["id"], enchantment["level"]
                    )
                    for enchantment in item["enchantments"]
                ]
            )
            give_args.append(f"{{ench: [{enchantments_str}]}}")

        return f"/give {' '.join(give_args)}"

    def reset(
        self,
        current_blocks: MinecraftBlocks,
        goal_blocks: MinecraftBlocks,
        player_locations: List[WorldLocation],
    ):
        self._malmo_state = get_initial_malmo_state(
            current_blocks,
            player_locations,
            self._env_config,
        )

        self._expected_state_diffs: List[MalmoStateDiff] = []

        self._setup_malmo_mission(
            current_blocks,
            goal_blocks,
            player_locations,
        )

        if self._palette_x is not None:
            self.copy_palette_from_goal()

        # Start both AI action and human action thread
        self._episode_done = threading.Event()

        self._ai_action_queue.clear()
        self._ai_actions_thread = threading.Thread(
            target=wrap_thread_to_handle_exceptions(self._run_ai_actions)
        )
        self._ai_actions_thread.start()

        self._human_action_queue.clear()
        self._human_action_detection_thread = threading.Thread(
            target=wrap_thread_to_handle_exceptions(self._run_human_action_detection)
        )
        self._human_action_detection_thread.start()

        if self._env_config["malmo"]["use_spectator"]:
            self._spectator_thread: Optional[threading.Thread] = threading.Thread(
                target=wrap_thread_to_handle_exceptions(self._run_spectator)
            )
            self._spectator_thread.start()
        else:
            self._spectator_thread = None

        # TODO: Do the palette here
        time.sleep(self._env_config["malmo"]["action_delay"])

        self.episode_running = True

    def end_episode(self):
        if not self.episode_running:
            return

        # Wait for a second for the final block to place and then end mission.
        logger.info("ending episode")

        time.sleep(self._env_config["malmo"]["action_delay"])

        self._episode_done.set()

        with self._ai_action_lock:
            self._ai_action_lock.notify()

        self._ai_actions_thread.join()
        self._human_action_detection_thread.join()
        if self._spectator_thread is not None:
            self._spectator_thread.join()

        with self._malmo_lock:
            time.sleep(1)
            self._malmo_client.end_mission()

        self.episode_running = False
        logger.info("successfully ended episode")

    def _fetch_malmo_observations(
        self, *, save: bool
    ) -> List[Tuple[int, MalmoObservationDict]]:
        """
        Gets the latest observations from Malmo. Returns a list of tuples of
        (player_index, observation_dict) sorted by the time the observation was
        generated.
        """

        malmo_observations_with_timestamps: List[
            Tuple[datetime, int, MalmoObservationDict]
        ] = []

        with self._malmo_lock:
            for player_index in range(self._env_config["num_players"]):
                malmo_player_observations = self._malmo_client.get_observations(
                    player_index
                )
                for timestamp, malmo_observation in malmo_player_observations:
                    malmo_observations_with_timestamps.append(
                        (timestamp, player_index, malmo_observation)
                    )

        malmo_observations_with_timestamps.sort(key=lambda x: x[0])

        if save:
            with self._malmo_observations_lock:
                self._malmo_observations.extend(malmo_observations_with_timestamps)

        return [
            (player_index, malmo_observation)
            for _, player_index, malmo_observation in malmo_observations_with_timestamps
        ]

    def _run_human_action_detection(self):
        # Clear any observations created during env reset.
        self._fetch_malmo_observations(save=False)

        player_blocks_on_ground: ReadOnlyList[ReadOnlyDict[int, int]] = ReadOnlyList(
            [ReadOnlyDict({}) for _ in range(self._env_config["num_players"])]
        )
        """
        This keeps track of blocks that are on the ground but "owned" by each player. This
        can happen when a block is broken or dropped by a player. Picking up the block
        does not generate an action in MBAG if the block is already "owned" by the player.
        If it is not owned by the player, then a GIVE_BLOCK action is generated for the
        owner.

        The number can also go temporarily negative if a player has just placed a block.
        Placing a block is considered as first dropping the block and then placing it.
        Thus, if the place block is registered first, the number will go negative until
        the inventory diff is registered as well.
        """

        latest_player_malmo_observations: List[Optional[MalmoObservationDict]] = [
            None for _ in range(self._env_config["num_players"])
        ]
        last_replace_missing_items_time = time.time()
        missing_items: List[List[Tuple[datetime, ItemDict]]] = [
            [] for _ in range(self._env_config["num_players"])
        ]

        while not self._episode_done.is_set():
            malmo_observations = self._fetch_malmo_observations(save=True)

            for player_index, malmo_observation in malmo_observations:
                latest_player_malmo_observations[player_index] = malmo_observation

                with self._malmo_state_and_human_actions_lock:
                    malmo_state = self._malmo_state

                new_state, state_diffs = update_malmo_state(
                    malmo_state,
                    player_index,
                    malmo_observation,
                    self._env_config,
                )

                new_human_actions: List[Tuple[int, MbagActionTuple]] = []
                for state_diff in state_diffs:
                    with self._expected_state_diffs_lock:
                        if state_diff in self._expected_state_diffs:
                            self._expected_state_diffs.remove(state_diff)
                            continue

                    human_actions, new_blocks_on_ground = get_human_actions(
                        new_state,
                        state_diff,
                        player_blocks_on_ground,
                        self._env_config,
                        self._palette_x,
                    )
                    player_blocks_on_ground = ReadOnlyList(
                        [
                            ReadOnlyDict(blocks_on_ground)
                            for blocks_on_ground in new_blocks_on_ground
                        ]
                    )

                    new_human_actions.extend(human_actions)

                with self._malmo_state_and_human_actions_lock:
                    self._malmo_state = new_state
                    self._human_action_queue.extend(new_human_actions)

            if time.time() - last_replace_missing_items_time >= 0:
                last_replace_missing_items_time = time.time()
                for player_index, latest_malmo_observation in enumerate(
                    latest_player_malmo_observations
                ):
                    if latest_malmo_observation is not None:
                        self._replace_missing_items(
                            player_index,
                            latest_malmo_observation,
                            missing_items[player_index],
                        )

            time.sleep(0.03)

    def _replace_missing_items(
        self,
        player_index: int,
        latest_malmo_observation: MalmoObservationDict,
        missing_items: List[Tuple[datetime, ItemDict]],
    ):
        items_player_should_always_have = self._items_players_should_always_have[
            player_index
        ]

        new_missing_items = {
            item["id"]: copy.deepcopy(item) for item in items_player_should_always_have
        }
        for slot in INVENTORY_SLOT_NAMES:
            item_name = latest_malmo_observation[f"InventorySlot_{slot}_item"]  # type: ignore
            if item_name is None:
                continue
            item_count = latest_malmo_observation[f"InventorySlot_{slot}_size"]  # type: ignore
            if item_name in new_missing_items:
                missing_item = new_missing_items[item_name]
                missing_item["count"] -= item_count
                if missing_item["count"] <= 0:
                    del new_missing_items[item_name]

        now = datetime.now()

        old_missing_items = list(missing_items)
        missing_items.clear()
        items_to_give: List[ItemDict] = []

        # Remove any items that aren't still missing, and move any items that have
        # been missing long enough to items_to_give.
        for timestamp, item in old_missing_items:
            if item["id"] in new_missing_items:
                if now - timestamp >= timedelta(seconds=0.1):
                    items_to_give.append(item)
                else:
                    missing_items.append((timestamp, item))
                del new_missing_items[item["id"]]
        # Add newly missing items.
        for item in new_missing_items.values():
            missing_items.append((now, item))

        with self._malmo_lock:
            for item in items_to_give:
                self._malmo_client.send_command(
                    player_index,
                    f"chat {self._get_give_command(player_index, item)}",
                )

    def get_malmo_observations(
        self,
    ) -> List[Tuple[datetime, int, MalmoObservationDict]]:
        with self._malmo_observations_lock:
            malmo_observations = self._malmo_observations
            self._malmo_observations = []
        return malmo_observations

    def get_human_actions_and_malmo_state(
        self,
    ) -> Tuple[List[Tuple[int, MbagActionTuple]], MalmoState]:
        """
        Get the human actions that have been detected in the Malmo observations since
        the last time this method was called. Also returns the latest Malmo state.

        IMPORTANT: the reason these are returned together are to avoid race conditions
        if the human actions and Malmo state are queried separately. For instance,
        consider this sequence of events:
          * Get human actions returns nothing.
          * A human action is detected and the Malmo state is updated.
          * Get Malmo state returns the updated state, which is used to sync the
            environment since it seems no human actions are pending.
        However, in this case human actions are pending!
        """

        with self._malmo_state_and_human_actions_lock:
            human_actions = list(self._human_action_queue)
            self._human_action_queue.clear()
            return human_actions, self._malmo_state

    def queue_ai_action(self, player_index: int, action: MalmoAIAction):
        with self._ai_action_lock:
            self._ai_action_queue.append((player_index, action))
            self._ai_action_lock.notify()

    def _handle_ai_move_action(self, player_index: int, ai_action: MalmoMoveAIAction):
        with self._malmo_lock:
            self._malmo_client.send_command(
                player_index, "tp " + " ".join(map(str, ai_action.new_location))
            )

    def _handle_ai_give_action(self, player_index: int, ai_action: MalmoGiveAIAction):
        block_name = MinecraftBlocks.ID2NAME[ai_action.action.block_id]
        giver_player_index = player_index
        giver_player_name = self._malmo_client.get_player_name(
            giver_player_index, self._env_config
        )
        recipient_player_index = ai_action.recipient_player_index
        recipient_player_name = self._malmo_client.get_player_name(
            recipient_player_index, self._env_config
        )

        with self._malmo_lock:
            self._malmo_client.send_command(
                giver_player_index,
                f"chat /clear {giver_player_name} {block_name} 0 "
                f"{ai_action.blocks_to_give}",
            )
            self._malmo_client.send_command(
                recipient_player_index,
                f"chat /give {recipient_player_name} {block_name} "
                f"{ai_action.blocks_to_give}",
            )

    NON_SILK_TOUCH_BLOCK_DROPS: Mapping[int, int] = {
        MinecraftBlocks.NAME2ID["air"]: MinecraftBlocks.NAME2ID["air"],
        MinecraftBlocks.NAME2ID["bedrock"]: MinecraftBlocks.NAME2ID["bedrock"],
        MinecraftBlocks.NAME2ID["dirt"]: MinecraftBlocks.NAME2ID["dirt"],
        MinecraftBlocks.NAME2ID["cobblestone"]: MinecraftBlocks.NAME2ID["cobblestone"],
        MinecraftBlocks.NAME2ID["glass"]: MinecraftBlocks.NAME2ID["air"],
        MinecraftBlocks.NAME2ID["log"]: MinecraftBlocks.NAME2ID["log"],
        MinecraftBlocks.NAME2ID["planks"]: MinecraftBlocks.NAME2ID["planks"],
        MinecraftBlocks.NAME2ID["stone"]: MinecraftBlocks.NAME2ID["cobblestone"],
        MinecraftBlocks.NAME2ID["stonebrick"]: MinecraftBlocks.NAME2ID["stonebrick"],
        MinecraftBlocks.NAME2ID["wool"]: MinecraftBlocks.NAME2ID["wool"],
    }

    def _handle_ai_place_break_action(
        self, player_index: int, ai_action: MalmoPlaceBreakAIAction
    ):
        # Ensure the player's inventory is correctly organized when inf_blocks=True.
        self._ensure_inventory_is_correctly_organized(player_index)

        with self._malmo_lock:
            if ai_action.player_location is not None:
                assert self._env_config["abilities"]["teleportation"]
                self._malmo_client.send_command(
                    player_index,
                    "tp " + " ".join(map(str, ai_action.player_location)),
                )

            self._malmo_client.send_command(player_index, f"setYaw {ai_action.yaw}")
            self._malmo_client.send_command(player_index, f"setPitch {ai_action.pitch}")

            if ai_action.action.action_type == MbagAction.PLACE_BLOCK:
                if self._env_config["abilities"]["inf_blocks"]:
                    self._malmo_client.send_command(
                        player_index,
                        f"swapInventoryItems 0 {ai_action.action.block_id}",
                    )
                    hotbar_slot = 0
                else:
                    with self._malmo_state_and_human_actions_lock:
                        player_inventory = self._malmo_state.player_inventories[
                            player_index
                        ]
                    for inventory_slot, (block_id, count) in enumerate(
                        player_inventory
                    ):
                        if block_id == ai_action.action.block_id and count > 0:
                            break
                    if inventory_slot < 9:
                        hotbar_slot = inventory_slot
                    else:
                        # Block is not in hotbar, need to swap it in.
                        hotbar_slot = random.randrange(9)
                        self._malmo_client.send_command(
                            player_index,
                            f"swapInventoryItems {hotbar_slot} {inventory_slot}",
                        )

                self._malmo_client.send_command(
                    player_index, f"hotbar.{hotbar_slot + 1} 1"
                )
                self._malmo_client.send_command(
                    player_index, f"hotbar.{hotbar_slot + 1} 0"
                )
                time.sleep(0.1)  # Give time to swap item to hand and teleport.
                self._malmo_client.send_command(player_index, "use 1")
                time.sleep(0.1)  # Give time to place block.
                if self._env_config["abilities"]["inf_blocks"]:
                    self._malmo_client.send_command(
                        player_index,
                        f"swapInventoryItems 0 {ai_action.action.block_id}",
                    )
                else:
                    # Since the player is in creative mode, the block will not be
                    # consumed, so we need to remove it back in the inventory
                    # manually.
                    self._malmo_client.send_command(
                        player_index,
                        f"chat /clear @p {MinecraftBlocks.ID2NAME[ai_action.action.block_id]} 0 1",
                    )
            else:
                # with self._malmo_state_and_human_actions_lock:
                #     block_id = self._malmo_state.blocks.blocks[
                #         ai_action.action.block_location
                #     ]
                #     block_drop = self.NON_SILK_TOUCH_BLOCK_DROPS[block_id]

                time.sleep(0.1)  # Give time to teleport.
                self._malmo_client.send_command(player_index, "attack 1")

                # Some blocks don't drop themselves when broken (e.g., stone drops
                # cobblestone). We need to check if the block dropped is the same as
                # the block broken, and if not, fix it.
                # if block_drop != block_id:
                #     self._malmo_client.send_command(
                #         player_index,
                #         f"chat /clear @p {MinecraftBlocks.ID2NAME[block_drop]} 0 1",
                #     )
                #     self._malmo_client.send_command(
                #         player_index,
                #         f"chat /give @p {MinecraftBlocks.ID2NAME[block_id]} 1",
                #     )

                # In case we accidentally broke a bedrock or barrier block, make sure
                # it gets regenerated.
                self._ensure_env_boundaries(player_index)
                # Also make sure the player doesn't have it in their inventory because
                # if they place it the human won't be able to break it.
                self._ensure_no_bedrock_or_barrier_blocks_in_inventory(player_index)

    def running_ai_actions(self) -> bool:
        with self._running_ai_actions_lock:
            return self._running_ai_actions

    def _run_ai_actions(self):
        while not self._episode_done.is_set():
            with self._ai_action_lock:
                self._ai_action_lock.wait_for(
                    lambda: len(self._ai_action_queue) > 0
                    or self._episode_done.is_set()
                )
                if self._episode_done.is_set():
                    break
                player_index, ai_action = self._ai_action_queue.pop(0)

            assert not self._env_config["players"][player_index]["is_human"]
            logger.info(f"running AI action {ai_action}")

            with self._malmo_state_and_human_actions_lock:
                malmo_state = self._malmo_state
            expected_state_diffs = get_state_diffs_for_ai_action(
                malmo_state, player_index, ai_action, self._env_config
            )
            with self._expected_state_diffs_lock:
                self._expected_state_diffs.extend(expected_state_diffs)

            with self._running_ai_actions_lock:
                self._running_ai_actions = True
            if isinstance(ai_action, MalmoPlaceBreakAIAction):
                self._handle_ai_place_break_action(player_index, ai_action)
            elif isinstance(ai_action, MalmoMoveAIAction):
                self._handle_ai_move_action(player_index, ai_action)
            elif isinstance(ai_action, MalmoGiveAIAction):
                self._handle_ai_give_action(player_index, ai_action)

            # Wait for actions to complete.
            time.sleep(0.2)
            with self._running_ai_actions_lock:
                self._running_ai_actions = False

            # By now, all expected state diffs should have been seen; warn if there are
            # still some we're waiting for.
            with self._expected_state_diffs_lock:
                for state_diff in self._expected_state_diffs:
                    logger.warning(
                        f"expected state diff from AI action not seen: {state_diff}"
                    )
                self._expected_state_diffs.clear()

    def _ensure_inventory_is_correctly_organized(self, player_index: int):
        with self._malmo_state_and_human_actions_lock:
            malmo_inventory = self._malmo_state.player_inventories[player_index]
        if self._env_config["abilities"]["inf_blocks"]:
            for block_id in MinecraftBlocks.PLACEABLE_BLOCK_IDS:
                if malmo_inventory[block_id, 0] != block_id:
                    logger.warning(
                        f"inventory discrepancy at slot {block_id}: "
                        f"expected {MinecraftBlocks.ID2NAME[block_id]} "
                        "but received "
                        f"{MinecraftBlocks.ID2NAME[malmo_inventory[block_id, 0]]} "
                        "from Malmo"
                    )
                    malmo_inventory_block_types: List[int] = malmo_inventory[
                        :, 0
                    ].tolist()
                    while block_id not in malmo_inventory_block_types:
                        # Somehow the AI player lost this block type, so give
                        # it a new one.
                        player_name = self._malmo_client.get_player_name(
                            player_index, self._env_config
                        )
                        with self._malmo_lock:
                            self._malmo_client.send_command(
                                player_index,
                                f"chat /give {player_name} {MinecraftBlocks.ID2NAME[block_id]} 1",
                            )
                        time.sleep(0.1)
                        with self._malmo_state_and_human_actions_lock:
                            malmo_inventory = self._malmo_state.player_inventories[
                                player_index
                            ]
                        malmo_inventory_block_types = malmo_inventory[:, 0].tolist()

                    swap_slot = malmo_inventory_block_types.index(block_id)
                    with self._malmo_lock:
                        self._malmo_client.send_command(
                            player_index,
                            f"swapInventoryItems {block_id} {swap_slot}",
                        )
                    time.sleep(0.1)

    def _ensure_no_bedrock_or_barrier_blocks_in_inventory(self, player_index: int):
        self._malmo_client.send_command(player_index, "chat /clear @p barrier")
        self._malmo_client.send_command(player_index, "chat /clear @p bedrock")

    def _ensure_env_boundaries(self, player_index: int):
        """
        Sometimes, errant AI actions can accidentally break the bedrock floor
        or the barrier walls. This method ensures that these boundaries are
        regenerated if this happens.

        IMPORTANT: this method should be called with self._malmo_lock already held.
        """

        assert self._malmo_lock.locked()

        width, height, depth = self._env_config["world_size"]

        self._malmo_client.send_command(
            player_index,
            f"chat /fill 0 0 0 {width - 1} 0 {depth - 1} bedrock",
        )

        if self._env_config["malmo"]["restrict_players"]:
            self._malmo_client.send_command(
                player_index,
                f"chat /fill {width} 2 -1 {width} {height} {depth} bedrock",
            )
            self._malmo_client.send_command(
                player_index,
                f"chat /fill -1 2 -1 -1 {height} {depth} barrier",
            )
            self._malmo_client.send_command(
                player_index,
                f"chat /fill -1 2 -1 {width} {height} -1 barrier",
            )
            self._malmo_client.send_command(
                player_index,
                f"chat /fill -1 2 {depth} {width} {height} {depth} barrier",
            )
            self._malmo_client.send_command(
                player_index,
                f"chat /fill -1 {height + 1} -1 {width} {height + 1} {depth} barrier",
            )

    def copy_palette_from_goal(self):
        # Sync with Malmo.
        with self._malmo_lock:
            width, height, depth = self._env_config["world_size"]
            assert self._palette_x is not None
            goal_palette_x = self._palette_x + width + 1

            self._malmo_client.send_command(
                0,
                f"chat /clone {goal_palette_x} 0 0 "
                f"{goal_palette_x} {height - 1} {depth - 1} "
                f"{self._palette_x} 0 0",
            )
            time.sleep(0.1)

    def update_goal_percentage(self, goal_percentage: float):
        with self._malmo_lock:
            percent = int(goal_percentage * 100)
            title_json = {
                "text": f"Goal completion: {percent}%",
                "fadeIn": "0s",
                "stay": "2s",
                "fadeOut": "0s",
            }
            for agent_index in range(
                self._malmo_client._get_num_agents(self._env_config)
            ):
                if (
                    agent_index < self._env_config["num_players"]
                    and not self._env_config["players"][agent_index]["goal_visible"]
                ):
                    continue
                self._malmo_client.send_command(
                    agent_index, f"chat /title @p actionbar {json.dumps(title_json)}"
                )

    def _run_spectator(self):
        """
        Run any spectator actions that need to be done, e.g., flying the spectator
        around the environment if rotate_spectator is True.
        """

        agent_index = self._malmo_client._get_spectator_agent_index(self._env_config)
        assert agent_index is not None

        with self._malmo_lock:
            self._malmo_client.send_command(
                agent_index, "chat /gamerule sendCommandFeedback false"
            )
            self._malmo_client.send_command(agent_index, "chat /gamemode spectator")

        # To start, we need to make the spectator fly by double tapping the jump key.
        for jump_on in [1, 0, 1, 0]:
            with self._malmo_lock:
                self._malmo_client.send_command(agent_index, f"jump {jump_on}")
            time.sleep(0.1)

        width, height, depth = self._env_config["world_size"]

        # The specatator should be consistently rotating about and looking at this point.
        # center_x, center_y, center_z = width, height / 2, depth / 2
        center_x, center_y, center_z = width / 2, height / 2, depth / 2

        # The spectator rotates in an ellipsis around the center of the environment.
        # x_axis_length = width + depth / 2
        # z_axis_length = depth / 2 + width
        x_axis_length = width / 2 + depth / 3
        z_axis_length = depth / 2 + width / 3

        min_x = center_x - x_axis_length
        max_x = center_x + x_axis_length

        rad_per_second = 0.1 if self._env_config["malmo"]["rotate_spectator"] else 0

        start_time = time.time()

        while not self._episode_done.is_set():
            time_elapsed = time.time() - start_time
            x = center_x + x_axis_length * np.sin(rad_per_second * time_elapsed)
            y = center_y + 2
            z = center_z + z_axis_length * -np.cos(rad_per_second * time_elapsed)

            # We adjust y and x so that the spectator rises up as it goes over the
            # wall between the current blocks and the goal.
            u = (x - min_x) / (max_x - min_x)
            x -= u * (x_axis_length - width / 2)
            y += u * (height / 2)

            pitch = np.rad2deg(
                np.arctan(
                    (y - center_y) / np.sqrt((x - center_x) ** 2 + (z - center_z) ** 2)
                )
            )
            yaw = np.rad2deg(np.arctan2(x - center_x, center_z - z))

            # Don't think we need to lock here because no other threads interact with
            # the spectator AgentHost.
            self._malmo_client.send_command(agent_index, f"tp {x} {y} {z}")
            self._malmo_client.send_command(agent_index, f"setPitch {pitch}")
            self._malmo_client.send_command(agent_index, f"setYaw {yaw}")

            if rad_per_second == 0:
                # No point in continuing to loop if we're not rotating the spectator.
                break

            time.sleep(0.03)

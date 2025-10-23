import functools
import glob
import itertools
import json
import logging
import os
import random
from typing import Dict, List, Optional, Tuple

import numpy as np
from typing_extensions import TypedDict

from ..blocks import MinecraftBlocks
from ..types import WorldSize
from .goal_generator import GoalGenerator

logger = logging.getLogger(__name__)


class CraftAssistGoalConfig(TypedDict):
    data_dir: str
    subset: str
    house_id: Optional[str]


DEFAULT_CONFIG: CraftAssistGoalConfig = {
    "data_dir": "data/craftassist",
    "subset": "train",
    "house_id": None,
}


class CraftAssistStats(TypedDict):
    size: WorldSize
    placed: int
    broken: int
    net_placed: int
    player_minutes: Dict[str, float]


class CraftAssistGoalGenerator(GoalGenerator):
    config: CraftAssistGoalConfig
    house_ids: List[str]
    last_house_id: Optional[str]
    block_map: Dict[str, Optional[Tuple[str, Optional[str]]]]

    def __init__(self, config: dict):
        config = {
            **DEFAULT_CONFIG,
            **config,
        }
        super().__init__(config)
        self._load_block_map()
        self._load_house_ids()
        self.last_house_id = None

    def _load_block_map(self):
        block_map_fname = os.path.join(
            os.path.dirname(__file__), "craftassist_block_map.json"
        )
        with open(block_map_fname, "r") as block_map_file:
            self.block_map = json.load(block_map_file)

        limited_block_map_fname = os.path.join(
            os.path.dirname(__file__), "limited_block_map.json"
        )
        with open(limited_block_map_fname, "r") as block_map_file:
            limited_block_map: Dict[str, str] = json.load(block_map_file)

        for key, value in self.block_map.items():
            if value is not None:
                self.block_map[key] = limited_block_map[value[0]], value[1]

    def _load_house_ids(self):
        self.house_ids = []
        for house_dir in glob.glob(
            os.path.join(
                self.config["data_dir"],
                "houses",
                self.config["subset"],
                "*",
            )
        ):
            house_id = os.path.split(house_dir)[-1]
            if self.config["house_id"] is None or self.config["house_id"] == house_id:
                self.house_ids.append(house_id)

    @functools.lru_cache
    def _minecraft_ids_to_block_variant(
        self, minecraft_id: int, minecraft_data: int
    ) -> Optional[Tuple[str, Optional[str]]]:
        minecraft_combined_id = f"{minecraft_id}:{minecraft_data}"
        return self.block_map[minecraft_combined_id]

    def generate_goal(self, size: WorldSize) -> MinecraftBlocks:
        success = False
        while not success:
            success = True

            house_id = random.choice(self.house_ids)
            schematic_fname = os.path.join(
                self.config["data_dir"],
                "houses",
                self.config["subset"],
                house_id,
                "schematic.npy",
            )
            if not os.path.exists(schematic_fname):
                success = False
                continue
            house_data = np.load(schematic_fname, "r").transpose((1, 0, 2, 3))

            # Strip air from around house to get down to the minimum size.
            house_is_air = np.zeros(house_data.shape[:3], dtype=bool)
            for x in range(house_data.shape[0]):
                for y in range(house_data.shape[1]):
                    for z in range(house_data.shape[2]):
                        minecraft_id, minecraft_data = house_data[x, y, z]
                        minecraft_combined_id = f"{minecraft_id}:{minecraft_data}"
                        try:
                            house_is_air[x, y, z] = (
                                self._minecraft_ids_to_block_variant(
                                    minecraft_id,
                                    minecraft_data,
                                )
                            )
                        except KeyError:
                            house_is_air[x, y, z] = False
            # Count dirt as air also.
            house_is_air |= (house_data[..., 0] == 2) | (house_data[..., 0] == 3)

            x_air_slices = np.all(house_is_air, axis=(1, 2))
            x_air_start, x_air_end = x_air_slices.argmin(), x_air_slices[::-1].argmin()
            y_air_slices = np.all(house_is_air, axis=(0, 2))
            y_air_start, y_air_end = y_air_slices.argmin(), y_air_slices[::-1].argmin()
            z_air_slices = np.all(house_is_air, axis=(0, 1))
            z_air_start, z_air_end = z_air_slices.argmin(), z_air_slices[::-1].argmin()
            # logger.info(house_data.shape[:3])
            house_data = house_data[
                x_air_start : -x_air_end or None,
                y_air_start : -y_air_end or None,
                z_air_start : -z_air_end or None,
            ]
            self.last_house_data = house_data
            # logger.info(
            #     " ".join(
            #         map(
            #             str,
            #             [
            #                 x_air_start,
            #                 x_air_end,
            #                 y_air_start,
            #                 y_air_end,
            #                 z_air_start,
            #                 z_air_end,
            #             ],
            #         )
            #     )
            # )
            # logger.info(house_data.shape[:3])

            # First, check if structure is too big.
            structure_size = house_data.shape[:3]
            if (
                structure_size[0] > size[0]
                or structure_size[1] > size[1]
                or structure_size[2] > size[2]
            ):
                success = False
                continue

            # Next, make sure all blocks are valid.
            structure = MinecraftBlocks(structure_size)
            structure.blocks[:] = MinecraftBlocks.AIR
            structure.block_states[:] = 0
            for x, y, z in itertools.product(
                range(structure_size[0]),
                range(structure_size[1]),
                range(structure_size[2]),
            ):
                minecraft_id, minecraft_data = house_data[x, y, z]
                try:
                    block_variant = self._minecraft_ids_to_block_variant(
                        minecraft_id, minecraft_data
                    )
                except KeyError:
                    logger.warning(f"no map entry for {minecraft_combined_id}")
                    success = False
                else:
                    if block_variant is None:
                        block_name, variant_name = "air", None
                    else:
                        block_name, variant_name = block_variant
                    block_id = MinecraftBlocks.NAME2ID.get(block_name)
                    if block_id is not None:
                        structure.blocks[x, y, z] = block_id
                    else:
                        success = False

            self._fill_auto_with_real_blocks(structure)
            if np.any(structure.blocks == MinecraftBlocks.AUTO):
                success = False

        logger.info(f"chose house {house_id}")
        self.last_house_id = house_id

        return structure

import contextlib
import copy
from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    ContextManager,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

import numpy as np
import torch
import torch.nn.functional as F  # noqa: N812
from gymnasium import spaces
from ray.rllib.models.catalog import ModelCatalog
from ray.rllib.models.modelv2 import restore_original_dimensions
from ray.rllib.models.preprocessors import get_preprocessor
from ray.rllib.models.torch.torch_modelv2 import TorchModelV2
from ray.rllib.policy.rnn_sequencing import add_time_dimension
from ray.rllib.policy.sample_batch import SampleBatch
from ray.rllib.policy.torch_policy import TorchPolicy
from ray.rllib.policy.torch_policy_v2 import TorchPolicyV2
from ray.rllib.policy.view_requirement import ViewRequirement
from ray.rllib.utils.exploration.exploration import Exploration
from ray.rllib.utils.numpy import convert_to_numpy
from ray.rllib.utils.torch_utils import convert_to_torch_tensor
from ray.rllib.utils.typing import AlgorithmConfigDict, TensorType
from torch import nn
from typing_extensions import TypedDict

from mbag.agents.action_distributions import MbagActionDistribution
from mbag.environment.actions import MbagAction
from mbag.environment.blocks import MinecraftBlocks
from mbag.environment.mbag_env import DEFAULT_CONFIG as DEFAULT_ENV_CONFIG
from mbag.environment.mbag_env import MbagConfigDict
from mbag.environment.types import (
    CURRENT_BLOCKS,
    CURRENT_PLAYER,
    GOAL_BLOCKS,
    LAST_INTERACTED,
    NO_ONE,
    PLAYER_LOCATIONS,
    WorldSize,
)

ACTION_MASK = "action_mask"
PREV_OBS = "prev_obs"
PREV_OTHER_AGENT_ACTIONS = "prev_other_agent_actions"


class Conv3d1x1x1(nn.Module):
    """
    A 1x1x1 convolution layer.
    """

    bias: Optional[nn.Parameter]

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()

        conv = nn.Conv3d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=1,
        )
        self.weight = nn.Parameter(conv.weight.data)
        assert self.weight.size() == (out_channels, in_channels, 1, 1, 1)
        if conv.bias is None:
            self.bias = None
        else:
            self.bias = nn.Parameter(conv.bias.data)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        n, c_in, d, h, w = x.size()
        c_out = self.weight.size()[0]
        return (
            F.linear(
                x.permute(0, 2, 3, 4, 1).reshape(-1, c_in),
                self.weight[:, :, 0, 0, 0],
                self.bias,
            )
            .reshape(n, d, h, w, c_out)
            .permute(0, 4, 1, 2, 3)
        )


class MbagModel(ABC, TorchModelV2):
    """
    A model to be used with MbagAutoregressiveActionDistribution.
    """

    @abstractmethod
    def block_id_model(  # noqa: E704
        self,
        inputs: torch.Tensor,
    ) -> torch.Tensor: ...


class MbagModelConfig(TypedDict, total=False):
    env_config: MbagConfigDict
    """Environment configuration."""
    num_inventory_obs: int
    """Number of inventory observations to input to the model."""
    embedding_size: int
    """Block ID embedding size."""
    use_extra_features: bool
    """Use extra hand-designed features as input to the network."""
    use_fc_after_embedding: bool
    """Use a fully connected layer after the observation embedding."""
    mask_goal: bool
    """Remove goal information from observations before passing into the network."""
    mask_other_players: bool
    """
    Remove other players from observations (locations, inventories, last interacted)
    before passing into the network.
    """
    fake_state: bool
    """Whether to add fake state to this model so that it's treated as recurrent."""
    hidden_size: int
    """Size of hidden layers."""
    num_action_layers: int
    """Number of extra layers for the action head."""
    num_value_layers: int
    """Number of extra layers for the value head."""
    num_lstm_layers: int
    """Number of LSTM layers."""
    mask_action_distribution: bool
    """Mask invalid actions in the output action distribution."""
    line_of_sight_masking: bool
    """
    Mask place/break actions which are not in the line of sight of the player.
    See MbagActionDistribution.get_mask for more details.
    """
    scale_obs: bool
    """Scale inventory and timestep observations."""
    vf_scale: float
    """Scale the value function output by this amount."""
    use_prev_blocks: bool
    """Whether to input the last different value of each block type to the network."""
    use_prev_action: bool
    """Whether to input the last action taken to the network."""
    use_prev_other_agent_action: bool
    """Whether to input the last action taken by other agents to the network."""


DEFAULT_CONFIG: MbagModelConfig = {
    "env_config": DEFAULT_ENV_CONFIG,
    "num_inventory_obs": 1,
    "embedding_size": 8,
    "use_extra_features": False,
    "use_fc_after_embedding": False,
    "mask_goal": False,
    "mask_other_players": True,
    "fake_state": False,
    "hidden_size": 16,
    "num_action_layers": 1,
    "num_value_layers": 1,
    "num_lstm_layers": 1,
    "mask_action_distribution": True,
    "line_of_sight_masking": False,
    "scale_obs": False,
    "vf_scale": 1.0,
    "use_prev_blocks": False,
    "use_prev_action": False,
    "use_prev_other_agent_action": False,
}


class MbagTorchModel(TorchModelV2, nn.Module, ABC):
    """
    This base class implements common functionality for PyTorch MBAG models such
    as block type embedding, separate policy and value networks and the value head.
    """

    MASK_LOGIT = -1e8

    _logits: torch.Tensor
    _mask: torch.Tensor

    def __init__(
        self,
        obs_space: spaces.Space,
        action_space: spaces.Space,
        num_outputs: int,
        model_config,
        name,
        **kwargs,
    ):
        TorchModelV2.__init__(
            self, obs_space, action_space, num_outputs, model_config, name
        )
        nn.Module.__init__(self)

        if hasattr(obs_space, "original_space"):
            obs_space = cast(Any, obs_space).original_space
        self.preprocessor = get_preprocessor(obs_space)(obs_space)
        if isinstance(obs_space, spaces.Dict):
            obs_space = obs_space.spaces["obs"]
        assert isinstance(obs_space, spaces.Tuple)
        world_obs_space = obs_space[0]
        assert isinstance(world_obs_space, spaces.Box)
        self.world_obs_space: spaces.Box = world_obs_space
        self.world_size = cast(WorldSize, self.world_obs_space.shape[-3:])
        inventory_obs_space = obs_space[1]
        assert isinstance(inventory_obs_space, spaces.Box)
        self.inventory_obs_space: spaces.Box = inventory_obs_space

        extra_config = copy.deepcopy(DEFAULT_CONFIG)
        if "env_config" in kwargs:
            extra_config["num_inventory_obs"] = kwargs["env_config"]["num_players"]
        extra_config.update(cast(MbagModelConfig, kwargs))
        self.env_config = extra_config["env_config"]
        self.num_inventory_obs = extra_config["num_inventory_obs"]
        self.embedding_size = extra_config["embedding_size"]
        self.use_extra_features = extra_config["use_extra_features"]
        self.use_fc_after_embedding = extra_config["use_fc_after_embedding"]
        self.mask_goal = extra_config["mask_goal"]
        self.mask_other_players = extra_config["mask_other_players"]
        self.fake_state: bool = extra_config["fake_state"]
        self.hidden_size = extra_config["hidden_size"]
        self.num_action_layers = extra_config["num_action_layers"]
        self.num_value_layers = extra_config["num_value_layers"]
        self.use_per_location_lstm = extra_config.get("use_per_location_lstm", False)
        self.lstm_depth = extra_config.get("lstm_depth", None)
        self.num_lstm_layers = extra_config.get("num_lstm_layers", 1)
        self.mask_action_distribution = extra_config["mask_action_distribution"]
        self.line_of_sight_masking = extra_config["line_of_sight_masking"]
        self.scale_obs = extra_config["scale_obs"]
        self.vf_scale = extra_config["vf_scale"]
        self.use_prev_blocks = extra_config["use_prev_blocks"]
        self.use_prev_action = extra_config["use_prev_action"]
        self.use_prev_other_agent_action = extra_config["use_prev_other_agent_action"]

        self.action_mapping = torch.from_numpy(
            MbagActionDistribution.get_action_mapping(self.env_config)
        )

        self.block_id_embedding = nn.Embedding(
            num_embeddings=len(MinecraftBlocks.ID2NAME),
            embedding_dim=self.embedding_size,
        )
        self.player_id_embedding = nn.Embedding(
            # Assume there are no more than 16 players, could be an issue down the line?
            num_embeddings=16,
            embedding_dim=self.embedding_size,
        )

        if self.use_fc_after_embedding:
            self.fc_after_embedding: nn.Module = Conv3d1x1x1(
                self._get_embedding_channels(), self.hidden_size
            )

        self.vf_share_layers: bool = model_config["vf_share_layers"]
        if self.vf_share_layers:
            self.backbone = self._construct_backbone()
        else:
            self.action_backbone = self._construct_backbone()
            self.value_backbone = self._construct_backbone(is_value_network=True)

        self.action_head = self._construct_action_head()
        self.value_head = self._construct_value_head()
        self.goal_head = self._construct_goal_head()

        if self.use_per_location_lstm:
            assert self.vf_share_layers
            assert not self.model_config.get("_time_major", False)
            self.per_location_lstm = nn.LSTM(
                input_size=self.hidden_size,
                hidden_size=self.hidden_size,
                num_layers=self.num_lstm_layers,
                batch_first=True,
            )

        if self.use_prev_blocks:
            self.view_requirements[PREV_OBS] = ViewRequirement(
                data_col=SampleBatch.OBS,
                space=self.view_requirements[SampleBatch.OBS].space,
                shift=-1,
            )

    @property
    def device(self) -> torch.device:
        return self.block_id_embedding.weight.device

    def _get_embedding_planes(self) -> int:
        """
        Return how many "planes" of data of size embedding_size are present in the
        embedded observation.
        """

        # We always have in-planes for current blocks, player locations, and
        # last interacted.
        planes = 3
        if not self.mask_goal:
            planes += 1
        if self.use_prev_blocks:
            planes += 1
        return planes

    def _get_embedding_channels(self) -> int:
        """Get the number of channels in the embedded observation."""
        in_channels = self._get_embedding_planes() * self.embedding_size
        # Add inventory observation as extra input channels.
        in_channels += MinecraftBlocks.NUM_BLOCKS * self.num_inventory_obs
        # Timestep observation
        in_channels += 1
        if self.use_extra_features:
            in_channels += 1
        if self.use_prev_action:
            in_channels += MbagActionDistribution.NUM_CHANNELS
        if self.use_prev_other_agent_action:
            in_channels += MbagActionDistribution.NUM_CHANNELS
        return in_channels

    def _get_backbone_in_channels(self) -> int:
        """Get the number of channels input to the backbone."""

        if self.use_fc_after_embedding:
            return self.hidden_size
        else:
            return self._get_embedding_channels()

    def _get_head_in_channels(self) -> int:
        """
        Get the number of channels output from the backbone which are used as input to
        the value and block ID heads.
        """

        return self.hidden_size

    def _construct_backbone(self, is_value_network=False) -> nn.Module:
        """
        Construct the main backbone of the model. This takes as input the result of
        _get_embedded_obs and should output a tensor of shape
            (batch_size, self._get_head_in_channels()) + self.world_size.
        When vf_share_layers is True, this is called once; when vf_share_layers is
        False, it is called twice, and the value backbone is passed
        is_value_network=True.
        """

        raise NotImplementedError()

    def _construct_action_head(self) -> nn.Module:
        """
        Construct the head which outputs the action distribution logits.
        """

        action_head_layers: List[nn.Module] = []
        for layer_index in range(self.num_action_layers):
            action_head_layers.append(
                Conv3d1x1x1(
                    (
                        self._get_head_in_channels()
                        if layer_index == 0
                        else self.hidden_size
                    ),
                    (
                        MbagActionDistribution.NUM_CHANNELS
                        if layer_index == self.num_action_layers - 1
                        else self.hidden_size
                    ),
                )
            )
            if layer_index < self.num_action_layers - 1:
                action_head_layers.append(nn.LeakyReLU())

        return nn.Sequential(*action_head_layers)

    def _construct_value_head(self) -> nn.Module:
        """
        Construct the head which takes in the output of the value backbone and
        outputs a one-dimensional value estimate.
        """

        value_head_layers: List[nn.Module] = [
            nn.AdaptiveAvgPool3d(1),
            nn.Flatten(),
        ]
        for layer_index in range(self.num_value_layers):
            value_head_layers.append(
                nn.Linear(
                    (
                        self._get_head_in_channels()
                        if layer_index == 0
                        else self.hidden_size
                    ),
                    1 if layer_index == self.num_value_layers - 1 else self.hidden_size,
                )
            )
            if layer_index < self.num_value_layers - 1:
                value_head_layers.append(nn.LeakyReLU())
        return nn.Sequential(*value_head_layers)

    def _construct_goal_head(self) -> nn.Module:
        """
        Construct the head which takes in the output of the value backbone and
        outputs a goal estimate.
        """

        return nn.Sequential(
            Conv3d1x1x1(self._get_head_in_channels(), self.hidden_size),
            nn.LeakyReLU(),
            Conv3d1x1x1(self.hidden_size, MinecraftBlocks.NUM_BLOCKS),
        )

    def _get_embedded_actions(
        self,
        actions: torch.Tensor,
    ):
        """
        Transform a raw tensor of actions into the input for the network backbone.
        actions can either be of shape (batch_size,) for flat actions or
        (batch_size, 3).
        """

        batch_size = actions.size()[0]
        width, height, depth = self.world_size

        if actions.ndim == 1:
            flat_actions = actions
        else:
            self.action_mapping = self.action_mapping.to(actions.device)
            flat_actions = torch.all(
                self.action_mapping[None, :, :] == actions[:, None, :],
                dim=2,
            ).nonzero()[:, 1]

        # A trick that gets reasonable action embeddings by taking the gradient of each
        # actions' probability with respect to arbitrary action distribution
        # probabilities.
        with torch.enable_grad():
            dummy_probs = torch.zeros(
                batch_size,
                MbagActionDistribution.NUM_CHANNELS,
                width,
                height,
                depth,
                device=actions.device,
            ).requires_grad_(True)
            dummy_flat_probs = MbagActionDistribution.to_flat_torch(
                self.env_config, dummy_probs
            )
            dummy_flat_probs[
                torch.arange(batch_size),
                flat_actions,
            ].sum().backward()
            assert dummy_probs.grad is not None
            embedded_actions = dummy_probs.grad.permute(0, 2, 3, 4, 1)

        return embedded_actions

    def _get_embedded_obs(
        self,
        world_obs: torch.Tensor,
        inventory_obs: torch.Tensor,
        timestep: torch.Tensor,
        prev_blocks: Optional[torch.Tensor] = None,
        prev_actions: Optional[torch.Tensor] = None,
        prev_other_agent_actions: Optional[torch.Tensor] = None,
        include_last_interacted: bool = True,
    ):
        """
        Transform a raw observation into the input for the network backbone.
        """

        embedded_blocks = self.block_id_embedding(world_obs[:, CURRENT_BLOCKS])
        embedded_obs_pieces = [embedded_blocks]
        if not self.mask_goal:
            embedded_goal_blocks = self.block_id_embedding(world_obs[:, GOAL_BLOCKS])
            embedded_obs_pieces.append(embedded_goal_blocks)
        if self.use_prev_blocks:
            assert prev_blocks is not None
            embedded_prev_blocks = self.block_id_embedding(prev_blocks)
            embedded_obs_pieces.append(embedded_prev_blocks)

        player_locations = world_obs[:, PLAYER_LOCATIONS].clone()
        if self.mask_other_players:
            player_locations[player_locations != CURRENT_PLAYER] = NO_ONE

        embedded_player_locations = self.player_id_embedding(player_locations)
        embedded_obs_pieces.append(embedded_player_locations)

        if self.mask_other_players and inventory_obs.ndim > 2:
            assert self.num_inventory_obs == 1
            flat_inventory_obs = inventory_obs[:, 0]
        else:
            inventory_obs = inventory_obs.flatten(start_dim=1)
            flat_inventory_obs = torch.zeros(
                inventory_obs.size()[0],
                MinecraftBlocks.NUM_BLOCKS * self.num_inventory_obs,
                device=inventory_obs.device,
            )
            flat_inventory_obs[:, : inventory_obs.size()[1]] = inventory_obs

        inventory_piece = flat_inventory_obs[:, None, None, None, :].expand(
            *embedded_obs_pieces[0].size()[:-1], -1
        )
        if self.scale_obs:
            inventory_piece = inventory_piece / 64
        embedded_obs_pieces.append(inventory_piece)
        timestep_piece = timestep[:, None, None, None, None].expand(
            *embedded_obs_pieces[0].size()[:-1], 1
        )
        if self.scale_obs:
            timestep_piece = timestep_piece / 1000
        embedded_obs_pieces.append(timestep_piece)
        if self.use_extra_features:
            # Feature for if goal block is the same as the current block at each
            # location.
            embedded_obs_pieces.append(
                (world_obs[:, 0] == world_obs[:, 2]).float()[..., None]
            )

        if include_last_interacted:
            last_interacted = world_obs[:, LAST_INTERACTED].clone()
            if self.mask_other_players:
                last_interacted[last_interacted > CURRENT_PLAYER] = CURRENT_PLAYER
            embedded_last_interacted = self.player_id_embedding(last_interacted)
            embedded_obs_pieces.append(embedded_last_interacted)

        if self.use_prev_action:
            if prev_actions is None:
                raise ValueError(
                    "prev_actions must be provided if use_prev_action is True"
                )
            embedded_prev_actions = self._get_embedded_actions(prev_actions)
            embedded_obs_pieces.append(embedded_prev_actions)
        if self.use_prev_other_agent_action:
            if prev_other_agent_actions is None:
                raise ValueError(
                    "prev_other_agent_actions must be provided if use_prev_other_agent_action is True"
                )
            embedded_prev_other_agent_actions = self._get_embedded_actions(
                prev_other_agent_actions
            )
            embedded_obs_pieces.append(embedded_prev_other_agent_actions)

        embedded_obs = torch.cat(embedded_obs_pieces, dim=-1)

        return embedded_obs.permute(0, 4, 1, 2, 3)

    def _run_lstm(
        self, backbone_out: torch.Tensor, state_in: List[torch.Tensor], seq_lens
    ) -> Tuple[torch.Tensor, List[torch.Tensor]]:
        flat_backbone_out = backbone_out.flatten(start_dim=1)
        flat_backone_out_with_time: torch.Tensor = add_time_dimension(
            flat_backbone_out,
            seq_lens=seq_lens,
            framework="torch",
            time_major=False,
        )
        # Should be of size (batch_size, max_seq_len, hidden_size, width, height, depth).
        backbone_out_with_time = flat_backone_out_with_time.reshape(
            *flat_backone_out_with_time.size()[:2],
            *backbone_out.size()[1:],
        )
        batch_size, max_seq_len = backbone_out_with_time.size()[:2]
        assert (
            backbone_out_with_time.size()[2:] == (self.hidden_size,) + self.world_size
        )
        backbone_out_per_location = backbone_out_with_time.permute(
            0, 3, 4, 5, 1, 2
        ).flatten(end_dim=3)
        # State in should be of size (batch_size, hidden_size, width, height, depth).
        state_in_per_location = tuple(
            state.permute(0, 2, 3, 4, 1).flatten(end_dim=3)[None].contiguous()
            for state in state_in
        )

        lstm_out_per_location: torch.Tensor
        state_out_per_location: torch.Tensor
        lstm_out_per_location, state_out_per_location = self.per_location_lstm(
            backbone_out_per_location, state_in_per_location
        )
        lstm_out_with_time = lstm_out_per_location.reshape(
            batch_size,
            *self.world_size,
            max_seq_len,
            self.hidden_size,
        ).permute(0, 4, 5, 1, 2, 3)
        state_out = [
            state.reshape(batch_size, *self.world_size, self.hidden_size).permute(
                0, 4, 1, 2, 3
            )
            for state in state_out_per_location
        ]

        lstm_out = lstm_out_with_time.flatten(end_dim=1)

        return lstm_out, state_out

    def forward(self, input_dict, state, seq_lens, mask_logits=True):
        obs = input_dict[SampleBatch.OBS]
        self._world_obs, self._inventory_obs, self._timestep = obs
        self._world_obs = self._world_obs.to(self.device).long()
        self._inventory_obs = self._inventory_obs.to(self.device).long()
        self._timestep = self._timestep.to(self.device)

        if seq_lens is not None:
            # Fix RLlib issue where sometimes seq_lens is too long.
            if self._world_obs.size()[0] == 1:
                seq_lens = torch.ones(
                    1, dtype=torch.long, device=self._world_obs.device
                )

        state = [
            state_var.to(self.device) if state_var is not None else None
            for state_var in state
        ]

        prev_blocks: Optional[torch.Tensor] = None
        if self.use_prev_blocks:
            start_prev_blocks: torch.Tensor
            state, start_prev_blocks = state[:-1], state[-1]
            start_prev_blocks = start_prev_blocks.long()  # Size (B, W, H, D)
            current_blocks_with_time: torch.Tensor = (  # Size (B, T, W, H, D)
                add_time_dimension(
                    self._world_obs[:, CURRENT_BLOCKS],
                    seq_lens=seq_lens,
                    framework="torch",
                    time_major=False,
                ).long()
            )
            prev_blocks = torch.concatenate(
                [start_prev_blocks[:, None], current_blocks_with_time[:, :-1]],
                dim=1,
            ).flatten(end_dim=1)
            end_current_blocks = current_blocks_with_time[:, -1]

        self._prev_actions: Optional[torch.Tensor] = None
        if SampleBatch.PREV_ACTIONS in input_dict:
            self._prev_actions = input_dict[SampleBatch.PREV_ACTIONS].to(self.device)
        self._prev_other_agent_actions: Optional[torch.Tensor] = None
        if PREV_OTHER_AGENT_ACTIONS in input_dict:
            self._prev_other_agent_actions = input_dict[PREV_OTHER_AGENT_ACTIONS].to(
                self.device
            )

        self._embedded_obs = self._get_embedded_obs(
            self._world_obs,
            self._inventory_obs,
            self._timestep,
            prev_blocks,
            self._prev_actions,
            self._prev_other_agent_actions,
        )
        if self.use_fc_after_embedding:
            self._backbone_in = self.fc_after_embedding(self._embedded_obs)
        else:
            self._backbone_in = self._embedded_obs

        self._amp_or_nothing: ContextManager = contextlib.nullcontext()
        if self.device.type == "cuda" and torch.cuda.is_bf16_supported():
            self._amp_or_nothing = torch.autocast("cuda", dtype=torch.bfloat16)

        with self._amp_or_nothing:
            backbone = self.backbone if self.vf_share_layers else self.action_backbone

            if isinstance(backbone, InterleavedBackbone):
                assert not self.use_per_location_lstm
                self._backbone_out, state = backbone(self._backbone_in, state, seq_lens)
            else:
                self._backbone_out = backbone(self._backbone_in)

            self._backbone_out_shape = self._backbone_out.size()[1:]
            assert self._backbone_out_shape[0] == self._get_head_in_channels()

            self._logits = self.action_head(self._backbone_out)
            self._flat_logits = MbagActionDistribution.to_flat_torch_logits(
                self.env_config, self._logits
            )

        self._logits = self._logits.float()
        self._flat_logits = self._flat_logits.float()
        state = [state_var.float() for state_var in state]

        if self.use_prev_blocks:
            state.append(end_current_blocks.clone())

        if mask_logits and self.mask_action_distribution:
            if ACTION_MASK in input_dict and torch.any(input_dict[ACTION_MASK]):
                self._mask = input_dict[ACTION_MASK]
            else:
                numpy_mask = MbagActionDistribution.get_mask_flat(
                    self.env_config,
                    convert_to_numpy(obs),
                    line_of_sight_masking=self.line_of_sight_masking,
                )
                self._mask = torch.from_numpy(numpy_mask).to(self._flat_logits.device)
            self._flat_logits[~self._mask] = MbagTorchModel.MASK_LOGIT
        else:
            self._mask = torch.ones_like(self._flat_logits, dtype=torch.bool)

        return self._flat_logits, state

    @property
    def logits(self) -> torch.Tensor:
        return self._flat_logits

    def action_mask(self):
        return self._mask

    def block_id_model(self, head_input: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError()

    def value_function(self):
        with self._amp_or_nothing:
            if self.vf_share_layers:
                vf = self.value_head(self._backbone_out).squeeze(1)
            else:
                vf = self.value_head(self.value_backbone(self._backbone_in)).squeeze(1)
        return vf.float() * self.vf_scale

    def goal_predictor(self) -> torch.Tensor:
        with self._amp_or_nothing:
            goal_preds: torch.Tensor = self.goal_head(self._backbone_out)
        return goal_preds.float()

    def get_initial_state(self):
        state: List[TensorType]
        if self.use_per_location_lstm:
            state = [
                torch.zeros((self.hidden_size, *self.world_size)) for _ in range(2)
            ]
        else:
            if self.fake_state:
                state = [torch.zeros(1)]
            else:
                state = super().get_initial_state()
        if self.use_prev_blocks:
            state.append(self._get_prev_blocks_initial_state())
        return state

    def _get_prev_blocks_initial_state(self):
        return torch.zeros(self.world_size, dtype=torch.uint8)

    def compute_priors_and_value(
        self, obs, state_in=[], action_mask=None, prev_actions=None
    ):
        batch_size = len(obs)
        obs = convert_to_torch_tensor(
            np.stack([self.preprocessor.transform(o) for o in obs], axis=0)
        )
        input_dict = {
            SampleBatch.OBS: restore_original_dimensions(obs, self.obs_space, "torch"),
        }
        tensor_state_in = [
            (
                torch.from_numpy(state).to(self.device)
                if isinstance(state, np.ndarray)
                else state
            )
            for state in state_in
        ]

        if action_mask is not None:
            action_mask = convert_to_torch_tensor(action_mask)
            input_dict[ACTION_MASK] = action_mask

        if prev_actions is not None:
            prev_actions = convert_to_torch_tensor(prev_actions)
            input_dict[SampleBatch.PREV_ACTIONS] = prev_actions

        with torch.no_grad():
            logits, state_out = self.forward(
                input_dict,
                tensor_state_in,
                np.ones(batch_size, dtype=int),
                mask_logits=False,
            )
            value = self.value_function()
            priors = logits.softmax(dim=-1)

            priors = priors.cpu().numpy()
            value = value.cpu().numpy()

            return priors, value, [state.detach() for state in state_out]

    def load_state_dict(self, state_dict, *args, **kwargs):
        if self.use_fc_after_embedding and (
            cast(torch.Tensor, self.fc_after_embedding.weight).size()
            != state_dict["fc_after_embedding.weight"].size()
        ):
            # This can happen if the loaded state dict was trained with a different
            # number of inventory inputs.

            # Figure out where the inventory observation starts in the embedded obs.
            embedded_obs = self._get_embedded_obs(
                torch.zeros(
                    (1,) + self.world_obs_space.shape,
                    dtype=torch.long,
                    device=self.device,
                ),
                torch.full(
                    (1,) + self.inventory_obs_space.shape,
                    np.nan,
                    device=self.device,
                ),
                torch.zeros(1, dtype=torch.long, device=self.device),
            )
            inventory_obs_indices = torch.nonzero(
                torch.isnan(embedded_obs[0, :, 0, 0, 0])
            )[:, 0]
            inventory_obs_end = inventory_obs_indices[-1] + 1 - embedded_obs.size()[1]

            # Resize the weight and bias tensors to match the new size.
            fc_weight = state_dict["fc_after_embedding.weight"]
            resized_fc_weight = cast(
                nn.Parameter, self.fc_after_embedding.weight
            ).data.clone()
            size_diff = resized_fc_weight.size()[1] - fc_weight.size()[1]
            if size_diff > 0:
                resized_fc_weight[:, : inventory_obs_end - size_diff] = fc_weight[
                    :, :inventory_obs_end
                ]
                resized_fc_weight[:, inventory_obs_end:] = fc_weight[
                    :, inventory_obs_end:
                ]
            else:
                resized_fc_weight[:, :inventory_obs_end] = fc_weight[
                    :, : inventory_obs_end - size_diff
                ]
                resized_fc_weight[:, inventory_obs_end:] = fc_weight[
                    :, inventory_obs_end:
                ]

            state_dict = {
                **state_dict,
                "fc_after_embedding.weight": resized_fc_weight,
            }
        return super().load_state_dict(state_dict, *args, **kwargs)


class ResidualBlock(nn.Module):
    """
    Implements a residual network block with two 3D convolutions, batch norm,
    and ReLU.
    """

    bn1: nn.Module
    bn2: nn.Module

    def __init__(
        self,
        channels: int,
        filter_size: int = 3,
        use_bn: bool = True,
        use_groupnorm: bool = False,
        dropout: float = 0.0,
        use_skip_connection: bool = True,
    ):
        super().__init__()

        self.conv1 = nn.Conv3d(
            in_channels=channels,
            out_channels=channels,
            kernel_size=filter_size,
            stride=1,
            padding=(filter_size - 1) // 2,
        )
        self.relu1 = nn.ReLU()

        self.conv2 = nn.Conv3d(
            in_channels=channels,
            out_channels=channels,
            kernel_size=filter_size,
            stride=1,
            padding=(filter_size - 1) // 2,
        )
        self.relu2 = nn.ReLU()

        if use_bn:
            assert not use_groupnorm
            self.bn1 = nn.BatchNorm3d(channels)
            self.bn2 = nn.BatchNorm3d(channels)
        elif use_groupnorm:
            self.bn1 = nn.GroupNorm(16, channels)
            self.bn2 = nn.GroupNorm(16, channels)
        else:
            self.bn1 = nn.Identity()
            self.bn2 = nn.Identity()

        self.dropout = nn.Dropout3d(dropout)

        self.use_skip_connection = use_skip_connection

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out: torch.Tensor = self.relu1(self.bn1(self.conv1(x)))
        out = self.dropout(out)
        out = self.bn2(self.conv2(out))
        if self.use_skip_connection:
            out = out + x
        out = self.relu2(out)
        return out


class MbagConvolutionalModelConfig(MbagModelConfig, total=False):
    num_conv_1_layers: int
    """Number of 1x1x1 convolutions before the main backbone."""
    num_layers: int
    use_resnet: bool
    filter_size: int
    hidden_channels: int
    use_groupnorm: bool
    dropout: float
    interleave_lstm_every: int
    lstm_size: Optional[int]


CONV_DEFAULT_CONFIG: MbagConvolutionalModelConfig = {
    "env_config": DEFAULT_CONFIG["env_config"],
    "embedding_size": DEFAULT_CONFIG["embedding_size"],
    "use_extra_features": DEFAULT_CONFIG["use_extra_features"],
    "mask_goal": DEFAULT_CONFIG["mask_goal"],
    "hidden_size": DEFAULT_CONFIG["hidden_size"],
    "num_action_layers": DEFAULT_CONFIG["num_action_layers"],
    "num_value_layers": DEFAULT_CONFIG["num_value_layers"],
    "fake_state": DEFAULT_CONFIG["fake_state"],
    "num_conv_1_layers": 0,
    "num_layers": 3,
    "use_resnet": False,
    "filter_size": 3,
    "hidden_channels": 32,
    "use_groupnorm": False,
    "dropout": 0.0,
    "interleave_lstm_every": -1,
    "lstm_size": None,
}


class MbagConvolutionalModel(MbagTorchModel):
    """
    Has an all-convolutional backbone and separate heads for each part of the
    autoregressive action distribution.
    """

    def __init__(
        self,
        obs_space: spaces.Space,
        action_space: spaces.Space,
        num_outputs: int,
        model_config,
        name,
        **kwargs,
    ):
        extra_config: MbagConvolutionalModelConfig = copy.deepcopy(CONV_DEFAULT_CONFIG)
        extra_config.update(cast(MbagConvolutionalModelConfig, kwargs))
        self.num_conv_1_layers = extra_config["num_conv_1_layers"]
        self.num_layers = extra_config["num_layers"]
        self.use_resnet = extra_config["use_resnet"]
        self.filter_size = extra_config["filter_size"]
        self.hidden_channels = extra_config["hidden_channels"]
        self.use_groupnorm = extra_config["use_groupnorm"]
        self.dropout = extra_config["dropout"]
        self.interleave_lstm_every = extra_config["interleave_lstm_every"]
        self.lstm_size = extra_config.get("lstm_size") or self.hidden_channels

        super().__init__(
            obs_space, action_space, num_outputs, model_config, name, **kwargs
        )

    def get_initial_state(self):
        if self.interleave_lstm_every > 0:
            assert isinstance(self.backbone, InterleavedBackbone)
            state = self.backbone.get_initial_state(world_size=self.world_size)
            if self.use_prev_blocks:
                state.append(self._get_prev_blocks_initial_state())
            return state
        else:
            return super().get_initial_state()

    def _construct_backbone(self, is_value_network=False) -> nn.Module:
        def layer_creator(layer_index: int) -> nn.Module:
            if layer_index < self.num_conv_1_layers:
                filter_size = 1
            else:
                filter_size = self.filter_size
            if layer_index == 0:
                in_channels = self._get_backbone_in_channels()
            else:
                in_channels = self.hidden_channels

            if self.use_resnet and in_channels == self.hidden_channels:
                return ResidualBlock(
                    channels=self.hidden_channels,
                    filter_size=filter_size,
                    use_bn=not self.use_groupnorm,
                    use_groupnorm=self.use_groupnorm,
                    dropout=self.dropout,
                )
            else:
                return nn.Sequential(
                    nn.Conv3d(
                        in_channels=in_channels,
                        out_channels=self.hidden_channels,
                        kernel_size=filter_size,
                        stride=1,
                        padding=(filter_size - 1) // 2,
                    ),
                    nn.LeakyReLU(),
                )

        return InterleavedBackbone(
            num_layers=self.num_layers,
            layer_creator=layer_creator,
            interleave_lstm_every=self.interleave_lstm_every,
            hidden_size=self.hidden_channels,
            lstm_size=self.lstm_size,
        )


ModelCatalog.register_custom_model("mbag_convolutional_model", MbagConvolutionalModel)


class MbagUNetModelConfig(MbagModelConfig, total=False):
    hidden_channels: int
    attention_resolutions: Sequence[int]
    num_res_blocks: int
    channel_mult: Sequence[int]
    num_heads: int
    use_scale_shift_norm: bool
    resblock_updown: bool
    use_lstm: int
    lstm_size: Optional[int]


UNET_DEFAULT_CONFIG: MbagUNetModelConfig = {
    "env_config": DEFAULT_CONFIG["env_config"],
    "embedding_size": DEFAULT_CONFIG["embedding_size"],
    "use_extra_features": DEFAULT_CONFIG["use_extra_features"],
    "mask_goal": DEFAULT_CONFIG["mask_goal"],
    "hidden_size": DEFAULT_CONFIG["hidden_size"],
    "num_action_layers": DEFAULT_CONFIG["num_action_layers"],
    "num_value_layers": DEFAULT_CONFIG["num_value_layers"],
    "fake_state": DEFAULT_CONFIG["fake_state"],
    "hidden_channels": DEFAULT_CONFIG["hidden_size"],
    "attention_resolutions": (),
    "num_res_blocks": 1,
    "channel_mult": (1, 2, 4),
    "num_heads": 4,
    "use_scale_shift_norm": True,
    "resblock_updown": True,
    "use_lstm": False,
    "lstm_size": None,
}


class Unpad3d(nn.Module):
    def __init__(self, padding: Tuple[int, int, int, int, int, int]):
        super().__init__()
        self.padding = padding

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x[
            :,
            :,
            self.padding[0] : -self.padding[1],
            self.padding[2] : -self.padding[3],
            self.padding[4] : -self.padding[5],
        ]


class MbagUNetModel(MbagTorchModel):
    """
    Backbone is based on the UNet architecture from Stable Diffusion.
    """

    def __init__(
        self,
        obs_space: spaces.Space,
        action_space: spaces.Space,
        num_outputs: int,
        model_config,
        name,
        **kwargs,
    ):
        extra_config: MbagUNetModelConfig = copy.deepcopy(UNET_DEFAULT_CONFIG)
        extra_config.update(cast(MbagUNetModelConfig, kwargs))
        self.hidden_channels = extra_config["hidden_channels"]
        self.attention_resolutions = extra_config["attention_resolutions"]
        self.num_res_blocks = extra_config["num_res_blocks"]
        self.channel_mult = extra_config["channel_mult"]
        self.num_heads = extra_config["num_heads"]
        self.use_scale_shift_norm = extra_config["use_scale_shift_norm"]
        self.resblock_updown = extra_config["resblock_updown"]
        self.use_lstm = extra_config["use_lstm"]
        self.lstm_size = extra_config.get("lstm_size") or self.hidden_channels

        super().__init__(
            obs_space, action_space, num_outputs, model_config, name, **kwargs
        )

    def get_initial_state(self):
        if self.use_lstm:
            assert isinstance(self.backbone, InterleavedBackbone)
            state = self.backbone.get_initial_state(world_size=self.world_size)
            if self.use_prev_blocks:
                state.append(self._get_prev_blocks_initial_state())
            return state
        else:
            return super().get_initial_state()

    def _construct_backbone(self, is_value_network=False) -> nn.Module:
        from .models.openai_unet import UNetModel

        width, height, depth = self.world_size

        pad_multiple = 2 ** (len(self.channel_mult) - 1)
        padded_width = ((width - 1) // pad_multiple + 1) * pad_multiple
        padded_height = ((height - 1) // pad_multiple + 1) * pad_multiple
        padded_depth = ((depth - 1) // pad_multiple + 1) * pad_multiple
        padding_left = (padded_width - width) // 2
        padding_right = (padded_width - width + 1) // 2
        padding_top = (padded_height - height) // 2
        padding_bottom = (padded_height - height + 1) // 2
        padding_front = (padded_depth - depth) // 2
        padding_back = (padded_depth - depth + 1) // 2

        def layer_creator(layer_index: int) -> nn.Module:
            assert layer_index == 0
            return nn.Sequential(
                nn.ZeroPad3d(
                    (
                        padding_front,
                        padding_back,
                        padding_top,
                        padding_bottom,
                        padding_left,
                        padding_right,
                    )
                ),
                UNetModel(
                    dims=3,
                    image_size=(padded_width, padded_height, padded_depth),
                    in_channels=self.hidden_channels,
                    out_channels=self.hidden_channels,
                    model_channels=self.hidden_channels,
                    attention_resolutions=self.attention_resolutions,
                    num_res_blocks=self.num_res_blocks,
                    channel_mult=self.channel_mult,
                    num_heads=self.num_heads,
                    use_scale_shift_norm=self.use_scale_shift_norm,
                    resblock_updown=self.resblock_updown,
                    use_checkpoint=True,
                ),
                Unpad3d(
                    (
                        padding_left,
                        padding_right,
                        padding_top,
                        padding_bottom,
                        padding_front,
                        padding_back,
                    )
                ),
            )

        return InterleavedBackbone(
            num_layers=3 if self.use_lstm else 1,
            layer_creator=layer_creator,
            lstm_layer_indices=[0, 2] if self.use_lstm else [],
            hidden_size=self.hidden_channels,
            lstm_size=self.lstm_size,
            use_checkpointing=False,
        )


ModelCatalog.register_custom_model("mbag_unet_model", MbagUNetModel)


class OtherAgentActionPredictorMixin(MbagTorchModel):
    def __init__(
        self,
        obs_space: spaces.Space,
        action_space: spaces.Space,
        num_outputs: int,
        model_config,
        name,
        **kwargs,
    ):
        super().__init__(
            obs_space, action_space, num_outputs, model_config, name, **kwargs
        )

        self.other_agent_action_prediction_head = self._construct_action_head()

    def predict_other_agent_action(self) -> torch.Tensor:
        with self._amp_or_nothing:
            logits: torch.Tensor = self.other_agent_action_prediction_head(
                self._backbone_out
            )
        flat_logits = MbagActionDistribution.to_flat_torch_logits(
            self.env_config, logits
        )
        return flat_logits.float()


class MbagConvolutionalAlphaZeroModel(
    MbagConvolutionalModel, OtherAgentActionPredictorMixin
):
    pass


ModelCatalog.register_custom_model(
    "mbag_convolutional_alpha_zero_model", MbagConvolutionalAlphaZeroModel
)


class MbagUNetAlphaZeroModel(MbagUNetModel, OtherAgentActionPredictorMixin):
    pass


ModelCatalog.register_custom_model(
    "mbag_unet_alpha_zero_model",
    MbagUNetAlphaZeroModel,
)


class View(nn.Module):
    def __init__(self, *shape: int):
        super().__init__()
        self.shape = shape

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x.view(*self.shape)


class Permute(nn.Module):
    def __init__(self, *dims: int):
        super().__init__()
        self.dims = dims

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x.permute(*self.dims)


class SeparatedTransformerEncoderLayer(nn.TransformerEncoderLayer):
    def __init__(
        self,
        d_model: int,
        nhead: int,
        dim_feedforward: int = 2048,
        dropout: float = 0.1,
        activation: Union[str, Callable[[torch.Tensor], torch.Tensor]] = F.relu,
        layer_norm_eps: float = 1e-5,
        batch_first: bool = True,
        norm_first: bool = False,
        bias: bool = True,
        device=None,
        dtype=None,
        *,
        n_spatial_dims,
        spatial_dim,
    ) -> None:
        super().__init__(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation=activation,
            layer_norm_eps=layer_norm_eps,
            batch_first=batch_first,
            norm_first=norm_first,
            bias=bias,
            device=device,
            dtype=dtype,
        )
        self.n_spatial_dims = n_spatial_dims
        self.spatial_dim = spatial_dim

    def _batched_forward(self, x: torch.Tensor) -> torch.Tensor:
        # PyTorch only supports batch sizes up to 2 ** 16 - 1, so we need to split
        # the batch into smaller chunks.
        batch_size = x.size()[0]
        if batch_size <= 2**16 - 1:
            return super().forward(x)
        else:
            minibatch_size = 2**15
            num_minibatches = (batch_size + minibatch_size - 1) // minibatch_size
            minibatch_outputs = []
            for i in range(num_minibatches):
                minibatch_outputs.append(
                    super().forward(x[i * minibatch_size : (i + 1) * minibatch_size])
                )
            return torch.cat(minibatch_outputs, dim=0)

    def forward(
        self,
        src: torch.Tensor,
        src_mask: Optional[torch.Tensor] = None,
        src_key_padding_mask: Optional[torch.Tensor] = None,
        is_causal: bool = False,
    ) -> torch.Tensor:
        assert src_mask is None
        assert src_key_padding_mask is None
        assert not is_causal
        x = src

        permutation = (
            (0,)
            + tuple(
                other_spatial_dim + 2
                for other_spatial_dim in range(self.n_spatial_dims)
                if other_spatial_dim != self.spatial_dim
            )
            + (self.spatial_dim + 2, 1)
        )
        inverse_permutation = tuple(
            permutation.index(dim) for dim in range(len(x.size()))
        )
        x_permuted = x.permute(*permutation)
        layer_input = x_permuted.flatten(end_dim=-3)
        # We use the default (math) kernel for attention b/c the sequence lengths are
        # super short, so it ends up being faster.
        if hasattr(torch.backends.cuda, "sdp_kernel"):
            with torch.backends.cuda.sdp_kernel(
                enable_flash=False, enable_mem_efficient=False
            ):
                layer_output = self._batched_forward(layer_input)
        else:
            layer_output = self._batched_forward(layer_input)
        x = layer_output.reshape(x_permuted.size()).permute(*inverse_permutation)
        return x


class ProjectedLSTM(nn.Module):
    def __init__(
        self,
        hidden_size: int,
        lstm_size: int,
    ):
        super().__init__()
        self.down_projection = nn.Linear(hidden_size, lstm_size)
        self.lstm = nn.LSTM(
            input_size=lstm_size,
            hidden_size=lstm_size,
            num_layers=1,
            batch_first=True,
        )
        self.up_projection = nn.Linear(lstm_size, hidden_size)

    def forward(
        self, x: torch.Tensor, state_in: Sequence[torch.Tensor]
    ) -> Tuple[torch.Tensor, Sequence[torch.Tensor]]:
        x = self.down_projection(x)
        pre_lstm_dtype = x.dtype
        x, state_out = self.lstm(x.float(), state_in)
        x = self.up_projection(x.to(pre_lstm_dtype))
        return x, state_out


class InterleavedBackbone(nn.Module):
    def __init__(
        self,
        num_layers: int,
        layer_creator: Callable[[int], nn.Module],
        interleave_lstm_every: int = -1,
        lstm_layer_indices: Optional[List[int]] = None,
        hidden_size: int = 64,
        lstm_size: int = 64,
        norm_first: bool = False,
        use_checkpointing: bool = False,
    ):
        super().__init__()

        self.num_layers = num_layers
        self.hidden_size = hidden_size
        self.lstm_size = lstm_size
        self.norm_first = norm_first
        self.use_checkpointing = use_checkpointing

        assert not (
            interleave_lstm_every > 1 and lstm_layer_indices is not None
        ), "Cannot specify both interleave_lstm_every and lstm_layer_indices."
        if interleave_lstm_every > 0:
            self.lstm_layer_indices = [
                layer_index
                for layer_index in range(num_layers)
                if (layer_index + 1) % interleave_lstm_every == 0
            ]
        else:
            self.lstm_layer_indices = lstm_layer_indices or []

        self.pre_lstm_layer_norms = nn.ModuleList()
        self.layers: List[nn.Module] = []
        num_non_lstm_layers = 0
        for layer_index in range(num_layers):
            layer: nn.Module
            if layer_index in self.lstm_layer_indices:
                if self.lstm_size == self.hidden_size:
                    layer = nn.LSTM(
                        input_size=self.lstm_size,
                        hidden_size=self.lstm_size,
                        num_layers=1,
                        batch_first=True,
                    )
                else:
                    layer = ProjectedLSTM(
                        hidden_size=self.hidden_size,
                        lstm_size=self.lstm_size,
                    )
                if self.norm_first:
                    pre_lstm_layer_norm = nn.LayerNorm(self.hidden_size)
                    self.pre_lstm_layer_norms.append(pre_lstm_layer_norm)
            else:
                # layer = nn.TransformerEncoderLayer(
                #     d_model=d_model,
                #     nhead=nhead,
                #     dim_feedforward=dim_feedforward,
                #     batch_first=True,
                #     norm_first=norm_first,
                # )
                layer = layer_creator(num_non_lstm_layers)
                num_non_lstm_layers += 1
            self.add_module(f"layer_{layer_index}", layer)
            self.layers.append(layer)

        if self.norm_first:
            self.post_layer_norm = nn.LayerNorm(self.hidden_size)

    def _run_layer(
        self, layer_index: int, x: torch.Tensor, state: List[torch.Tensor], seq_lens
    ) -> Tuple[torch.Tensor, List[torch.Tensor]]:
        layer = self.layers[layer_index]

        if isinstance(layer, (nn.LSTM, ProjectedLSTM)):
            lstm_index = self.lstm_layer_indices.index(layer_index)
            lstm_state = state[2 * lstm_index : 2 * (lstm_index + 1)]
            x, state = self._run_lstm(
                layer,
                x,
                lstm_state,
                seq_lens,
                pre_layer_norm=(
                    cast(nn.LayerNorm, self.pre_lstm_layer_norms[lstm_index])
                    if self.norm_first
                    else None
                ),
            )
        else:
            x = layer(x)
            state = []

        if x.device.type == "cuda" and torch.cuda.is_bf16_supported():
            x = x.bfloat16()

        return x, state

    def _run_lstm(
        self,
        lstm: Union[nn.LSTM, ProjectedLSTM],
        x: torch.Tensor,
        state_in: List[torch.Tensor],
        seq_lens,
        pre_layer_norm: Optional[nn.LayerNorm] = None,
    ) -> Tuple[torch.Tensor, List[torch.Tensor]]:
        x = x.float()
        world_size = x.size()[2:]
        flat_x = x.flatten(start_dim=1)
        flat_backone_out_with_time: torch.Tensor = add_time_dimension(
            flat_x,
            seq_lens=seq_lens,
            framework="torch",
            time_major=False,
        )
        # Should be of size (batch_size, max_seq_len, hidden_size, width, height, depth).
        x_with_time = flat_backone_out_with_time.reshape(
            *flat_backone_out_with_time.size()[:2],
            *x.size()[1:],
        )
        batch_size, max_seq_len = x_with_time.size()[:2]
        assert x_with_time.size()[2:] == (self.hidden_size,) + world_size
        # Should be of size (batch_size * width * height * depth, max_seq_len, hidden_size).
        x_per_location = x_with_time.permute(0, 3, 4, 5, 1, 2).flatten(end_dim=3)
        if pre_layer_norm:
            x_per_location = pre_layer_norm(x_per_location)
        # State in should be of size (batch_size, hidden_size, width, height, depth).
        state_in_per_location = tuple(
            state.permute(0, 2, 3, 4, 1).flatten(end_dim=3)[None].contiguous()
            for state in state_in
        )

        lstm_out_per_location: torch.Tensor
        state_out_per_location: torch.Tensor
        lstm_out_per_location, state_out_per_location = lstm(
            x_per_location, state_in_per_location
        )
        lstm_out_with_time = lstm_out_per_location.reshape(
            batch_size,
            *world_size,
            max_seq_len,
            self.hidden_size,
        ).permute(0, 4, 5, 1, 2, 3)
        state_out = [
            state.reshape(batch_size, *world_size, self.lstm_size).permute(
                0, 4, 1, 2, 3
            )
            for state in state_out_per_location
        ]

        lstm_out = lstm_out_with_time.flatten(end_dim=1)

        out = lstm_out + x  # Residual connection.

        return out, state_out

    def forward(
        self,
        x: torch.Tensor,
        state: List[torch.Tensor] = [],
        seq_lens=None,
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, List[torch.Tensor]]]:
        # input shape: (batch_size, channels, spatial_dim_1, spatial_dim_2...)

        state_out: List[torch.Tensor] = []
        for layer_index in range(self.num_layers):
            if self.training and self.use_checkpointing:
                from torch.utils.checkpoint import checkpoint

                x, layer_state = checkpoint(
                    lambda x, state, seq_lens, layer_index=layer_index: self._run_layer(
                        layer_index, x, state, seq_lens
                    ),
                    x,
                    state,
                    seq_lens,
                )
            else:
                x, layer_state = self._run_layer(layer_index, x, state, seq_lens)
            state_out.extend(layer_state)

        if self.norm_first:
            x = self.post_layer_norm(x.permute(0, 2, 3, 4, 1)).permute(0, 4, 1, 2, 3)

        return x, state_out

    def get_initial_state(self, world_size: WorldSize) -> List[torch.Tensor]:
        num_lstm_layers = len(self.lstm_layer_indices)
        if num_lstm_layers > 0:
            return [
                torch.zeros((self.lstm_size, *world_size))
                for _ in range(2 * num_lstm_layers)
            ]
        else:
            return []


class MbagTransformerModelConfig(MbagModelConfig, total=False):
    position_embedding_size: int
    position_embedding_angle: float
    num_layers: int
    dim_feedforward: int
    num_heads: int
    dropout: float
    norm_first: bool
    use_separated_transformer: bool
    interleave_lstm: bool


TRANSFORMER_DEFAULT_CONFIG: MbagTransformerModelConfig = {
    "env_config": DEFAULT_CONFIG["env_config"],
    "embedding_size": DEFAULT_CONFIG["embedding_size"],
    "use_extra_features": DEFAULT_CONFIG["use_extra_features"],
    "mask_goal": DEFAULT_CONFIG["mask_goal"],
    "hidden_size": DEFAULT_CONFIG["hidden_size"],
    "num_action_layers": DEFAULT_CONFIG["num_action_layers"],
    "num_value_layers": DEFAULT_CONFIG["num_value_layers"],
    "fake_state": DEFAULT_CONFIG["fake_state"],
    "position_embedding_size": 12,
    "position_embedding_angle": 10000.0,
    "num_layers": 3,
    "dim_feedforward": DEFAULT_CONFIG["hidden_size"],
    "num_heads": 2,
    "dropout": 0.1,
    "norm_first": False,
    "use_separated_transformer": False,
    "interleave_lstm": False,
}


class MbagTransformerModel(MbagTorchModel):
    """
    Model which uses a transformer encoder as the backbone.
    """

    def __init__(
        self,
        obs_space: spaces.Space,
        action_space: spaces.Space,
        num_outputs: int,
        model_config,
        name,
        **kwargs,
    ):
        if "hidden_size" in kwargs:
            kwargs.setdefault("dim_feedforward", kwargs["hidden_size"])
        extra_config: MbagTransformerModelConfig = copy.deepcopy(
            TRANSFORMER_DEFAULT_CONFIG
        )
        extra_config.update(cast(MbagTransformerModelConfig, kwargs))
        self.position_embedding_size = extra_config["position_embedding_size"]
        self.position_embedding_angle = extra_config["position_embedding_angle"]
        self.num_layers = extra_config["num_layers"]
        self.dim_feedforward = extra_config["dim_feedforward"]
        self.num_heads = extra_config["num_heads"]
        self.dropout = extra_config["dropout"]
        self.norm_first = extra_config["norm_first"]
        self.use_separated_transformer = extra_config["use_separated_transformer"]
        self.interleave_lstm = extra_config["interleave_lstm"]

        super().__init__(
            obs_space, action_space, num_outputs, model_config, name, **kwargs
        )

        assert self._get_backbone_in_channels() <= self.hidden_size

        # Initialize positional embeddings along each dimension.
        self.position_embedding = nn.Parameter(
            torch.zeros(self.world_size + (self.position_embedding_size,))
        )
        dim_embedding_size = self.position_embedding_size // 6 * 2
        self.position_embedding.data[..., :dim_embedding_size] = (
            self._get_position_embedding(
                self.position_embedding.size()[0],
                dim_embedding_size,
                self.position_embedding_angle,
            )[:, None, None]
        )
        self.position_embedding.data[
            ..., dim_embedding_size : dim_embedding_size * 2
        ] = self._get_position_embedding(
            self.position_embedding.size()[1],
            dim_embedding_size,
            self.position_embedding_angle,
        )[
            None, :, None
        ]
        self.position_embedding.data[
            ..., dim_embedding_size * 2 : dim_embedding_size * 3
        ] = self._get_position_embedding(
            self.position_embedding.size()[2],
            dim_embedding_size,
            self.position_embedding_angle,
        )[
            None, None, :
        ]

    def _get_embedding_channels(self) -> int:
        return super()._get_embedding_channels() + self.position_embedding_size

    def _get_position_embedding(
        self, seq_len: int, size: int, angle: float = 10000.0
    ) -> torch.Tensor:
        """
        Get an initial positional embedding of shape (seq_len, size) by using
        the sin/cos embedding.
        """

        embedding = torch.zeros(seq_len, size)
        position = torch.arange(0, seq_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, size, 2).float() * (-np.log(angle) / size))
        embedding[:, 0::2] = torch.sin(position * div_term)
        embedding[:, 1::2] = torch.cos(position * div_term)
        return embedding

    def _pad_to_hidden_size(self, x: torch.Tensor) -> torch.Tensor:
        """
        Pads the last dimension of the given tensor so that it is self.hidden_size.
        """

        return F.pad(x, [0, self.hidden_size - x.size()[-1]])

    def _construct_backbone(self, is_value_network=False) -> nn.Module:
        if self.use_separated_transformer:

            def layer_creator(layer_index: int) -> nn.Module:
                return SeparatedTransformerEncoderLayer(
                    d_model=self.hidden_size,
                    nhead=self.num_heads,
                    dim_feedforward=self.dim_feedforward,
                    batch_first=True,
                    dropout=self.dropout,
                    norm_first=self.norm_first,
                    n_spatial_dims=3,
                    spatial_dim=layer_index % 3,
                )

        else:

            def layer_creator(layer_index: int) -> nn.Module:
                return nn.Sequential(
                    View(-1, self.hidden_size, np.prod(self.world_size)),
                    Permute(0, 2, 1),
                    nn.TransformerEncoderLayer(
                        d_model=self.hidden_size,
                        nhead=self.num_heads,
                        dim_feedforward=self.dim_feedforward,
                        batch_first=True,
                        dropout=self.dropout,
                        norm_first=self.norm_first,
                    ),
                    View(-1, *self.world_size, self.hidden_size),
                    Permute(0, 4, 1, 2, 3),
                )

        return InterleavedBackbone(
            num_layers=self.num_layers,
            layer_creator=layer_creator,
            interleave_lstm_every=4 if self.interleave_lstm else -1,
            hidden_size=self.hidden_size,
            lstm_size=self.hidden_size,
            norm_first=self.norm_first,
            use_checkpointing=True,
        )

    def _get_embedded_obs(
        self,
        world_obs: torch.Tensor,
        inventory_obs: torch.Tensor,
        timestep: torch.Tensor,
        prev_blocks: Optional[torch.Tensor] = None,
        prev_actions: Optional[torch.Tensor] = None,
        prev_other_agent_actions: Optional[torch.Tensor] = None,
        include_last_interacted=True,
    ):
        embedded_obs = super()._get_embedded_obs(
            world_obs,
            inventory_obs,
            timestep,
            prev_blocks,
            prev_actions,
            prev_other_agent_actions,
            include_last_interacted,
        )
        batch_size = embedded_obs.size()[0]
        embedded_obs = torch.cat(
            [
                embedded_obs.permute(0, 2, 3, 4, 1),
                self.position_embedding[None].expand(batch_size, -1, -1, -1, -1),
            ],
            dim=4,
        )
        if not self.use_fc_after_embedding:
            embedded_obs = self._pad_to_hidden_size(embedded_obs)

        embedded_obs = embedded_obs.permute(0, 4, 1, 2, 3)

        return embedded_obs

    def get_initial_state(self):
        if self.interleave_lstm:
            assert isinstance(self.backbone, InterleavedBackbone)
            state = self.backbone.get_initial_state(world_size=self.world_size)
            if self.use_prev_blocks:
                state.append(self._get_prev_blocks_initial_state())
            return state
        else:
            return super().get_initial_state()


ModelCatalog.register_custom_model("mbag_transformer_model", MbagTransformerModel)


class MbagTransformerAlphaZeroModel(
    MbagTransformerModel, OtherAgentActionPredictorMixin
):
    pass


ModelCatalog.register_custom_model(
    "mbag_transformer_alpha_zero_model", MbagTransformerAlphaZeroModel
)


class ModelWithDiscriminator(TorchModelV2, nn.Module, ABC):
    @abstractmethod
    def discriminator(  # noqa: E704
        self, input_dict: Dict[str, TensorType]
    ) -> torch.Tensor: ...


class DiscriminatorMixin(MbagTorchModel, ModelWithDiscriminator):
    def __init__(
        self,
        obs_space: spaces.Space,
        action_space: spaces.Space,
        num_outputs: int,
        model_config,
        name,
        **kwargs,
    ):
        super().__init__(
            obs_space, action_space, num_outputs, model_config, name, **kwargs
        )

        self.discriminator_backbone = self._construct_backbone()
        self.discriminator_head = self._construct_discriminator_head()

    def _get_discriminator_module_names(self) -> List[str]:
        return ["discriminator_backbone", "discriminator_head"]

    def _get_embedded_obs_and_actions(
        self,
        world_obs: torch.Tensor,
        inventory_obs: torch.Tensor,
        timestep: torch.Tensor,
        actions: torch.Tensor,
        prev_blocks: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        raise NotImplementedError()

    def _construct_discriminator_head(self) -> nn.Module:
        return nn.Sequential(
            nn.AdaptiveAvgPool3d(1),
            nn.Flatten(),
            nn.Linear(self.hidden_size, 1),
        )

    def discriminator(self, input_dict: Dict[str, TensorType]) -> torch.Tensor:
        if self.model_config.get("_disable_preprocessor_api"):
            obs = cast(
                Tuple[torch.Tensor, torch.Tensor, torch.Tensor],
                input_dict[SampleBatch.OBS],
            )
        else:
            obs = cast(
                Tuple[torch.Tensor, torch.Tensor, torch.Tensor],
                restore_original_dimensions(
                    input_dict[SampleBatch.OBS], self.obs_space, self.framework
                ),
            )

        world_obs, inventory_obs, timestep = obs
        world_obs = world_obs.to(self.device).long()
        inventory_obs = inventory_obs.to(self.device).long()
        timestep = timestep.to(self.device)
        actions = (
            cast(torch.Tensor, input_dict[SampleBatch.ACTIONS]).to(self.device).long()
        )

        embedded_obs = self._get_embedded_obs_and_actions(
            world_obs, inventory_obs, timestep, actions
        )

        with self._amp_or_nothing:
            backbone_out: torch.Tensor
            if isinstance(self.discriminator_backbone, InterleavedBackbone):
                backbone_out, _ = self.discriminator_backbone(embedded_obs)
            else:
                backbone_out = self.discriminator_backbone(embedded_obs)
            logits: torch.Tensor = self.discriminator_head(backbone_out).squeeze(1)

        return logits.float()

    def load_state_dict(self, state_dict: Mapping[str, Any], strict=True, assign=False):
        # Allow loading existing model weights that don't include the discriminator
        # weights.
        new_state_dict = dict(state_dict)
        current_state_dict = self.state_dict()
        for key in current_state_dict:
            if any(
                key.startswith(module_name + ".")
                for module_name in self._get_discriminator_module_names()
            ):
                new_state_dict.setdefault(key, current_state_dict[key])

        super().load_state_dict(new_state_dict)


class MbagTransformerModelWithDiscriminator(MbagTransformerModel, DiscriminatorMixin):
    def __init__(
        self,
        obs_space: spaces.Space,
        action_space: spaces.Space,
        num_outputs: int,
        model_config,
        name,
        **kwargs,
    ):
        super().__init__(
            obs_space, action_space, num_outputs, model_config, name, **kwargs
        )

        self.discriminator_first_layer = nn.Conv3d(
            in_channels=self._get_embedding_channels()
            - self.embedding_size
            + MbagActionDistribution.NUM_CHANNELS,
            out_channels=self.hidden_size,
            kernel_size=1,
            stride=1,
            padding=0,
        )

    def _get_discriminator_module_names(self):
        return super()._get_discriminator_module_names() + ["discriminator_first_layer"]

    def _get_embedded_obs_and_actions(
        self,
        world_obs: torch.Tensor,
        inventory_obs: torch.Tensor,
        timestep: torch.Tensor,
        actions: torch.Tensor,
        prev_blocks: Optional[torch.Tensor] = None,
    ):
        # Ignore LAST_INTERACTED channel in the discriminator.
        embedded_obs = MbagTorchModel._get_embedded_obs(
            self,
            world_obs,
            inventory_obs,
            timestep,
            prev_blocks,
            include_last_interacted=False,
        )

        batch_size, _, width, height, depth = world_obs.size()
        embedded_actions = torch.zeros(
            (batch_size, MbagActionDistribution.NUM_CHANNELS, width, height, depth),
            dtype=embedded_obs.dtype,
            device=embedded_obs.device,
        )

        flat_action_start = 0
        for channel, (action_type, block_id) in enumerate(
            MbagActionDistribution.CHANNELS
        ):
            channel_embedded_actions = embedded_actions[:, channel].view(batch_size, -1)
            if action_type in MbagAction.BLOCK_LOCATION_ACTION_TYPES:
                flat_action_end = flat_action_start + width * height * depth

                actions_in_channel_mask = (actions >= flat_action_start) & (
                    actions < flat_action_end
                )
                channel_embedded_actions[
                    torch.arange(batch_size, device=embedded_obs.device)[
                        actions_in_channel_mask
                    ],
                    actions[actions_in_channel_mask] - flat_action_start,
                ] = 1
            else:
                actions_in_channel_mask = actions == flat_action_start
                channel_embedded_actions[actions_in_channel_mask, :] = 1
                flat_action_end = flat_action_start + 1

            flat_action_start = flat_action_end

        assert torch.any(embedded_actions.flatten(start_dim=1), dim=1).all()

        batch_size = embedded_obs.size()[0]
        embedded_obs_and_actions = torch.cat(
            [
                embedded_obs,
                embedded_actions,
                self.position_embedding[None]
                .expand(batch_size, -1, -1, -1, -1)
                .permute(0, 4, 1, 2, 3),
            ],
            dim=1,
        )
        embedded_obs_and_actions = self.discriminator_first_layer(
            embedded_obs_and_actions
        )

        if self.use_separated_transformer:
            return embedded_obs_and_actions
        else:
            return embedded_obs_and_actions.flatten(start_dim=2).transpose(1, 2)


ModelCatalog.register_custom_model(
    "mbag_transformer_with_discriminator_model", MbagTransformerModelWithDiscriminator
)


def _optimizer(
    config: Optional[AlgorithmConfigDict],
    model: Optional[TorchModelV2],
    exploration: Optional[Exploration],
) -> Union[List[torch.optim.Optimizer], torch.optim.Optimizer]:
    """Customize the local PyTorch optimizer(s) to use.

    Args:
        config: The Policy's config dict.
        model: PyTorch policy module. Given observations as
            input, this module must return a list of outputs where the
            first item is action logits, and the rest can be any value.
        exploration: The Policy's exploration strategy.

    Returns:
        The local PyTorch optimizer(s) to use for this Policy.

    Raises:
        ValueError: If the model is None.
        ValueError: If the model does not inherit from torch.nn.Module.
    """
    if model is None:
        raise ValueError("Model is required to create optimizer.")
    if not isinstance(model, nn.Module):
        raise ValueError(
            "Model must be an instance of torch.nn.Module to create optimizer."
        )
    module = cast(nn.Module, model)

    if config is not None:
        optimizer: torch.optim.Optimizer = torch.optim.Adam(
            module.parameters(),
            lr=config["lr"],
            **config.get("optimizer", {}),
        )
    else:
        optimizer = torch.optim.Adam(module.parameters())
    optimizers = [optimizer]
    if exploration:
        optimizers = exploration.get_exploration_optimizer(optimizers)

    return optimizers


class OptimizerMixin(TorchPolicy):

    def optimizer(
        self,
    ) -> Union[List[torch.optim.Optimizer], torch.optim.Optimizer]:
        """Customize the local PyTorch optimizer(s) to use.

        Returns:
            The local PyTorch optimizer(s) to use for this Policy.
        """
        return _optimizer(getattr(self, "config", None), self.model, self.exploration)


class OptimizerMixinV2(TorchPolicyV2):

    def optimizer(
        self,
    ) -> Union[List[torch.optim.Optimizer], torch.optim.Optimizer]:
        """Customize the local PyTorch optimizer(s) to use.

        Returns:
            The local PyTorch optimizer(s) to use for this Policy.
        """
        return _optimizer(getattr(self, "config", None), self.model, self.exploration)

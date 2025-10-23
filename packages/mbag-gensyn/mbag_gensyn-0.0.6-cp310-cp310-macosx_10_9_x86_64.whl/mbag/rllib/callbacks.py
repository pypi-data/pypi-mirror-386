from typing import Dict, Optional, Union, cast

import numpy as np
from ray.rllib.algorithms.algorithm import Algorithm
from ray.rllib.algorithms.alpha_zero.alpha_zero import AlphaZeroDefaultCallbacks
from ray.rllib.env.base_env import BaseEnv
from ray.rllib.evaluation.episode import Episode
from ray.rllib.evaluation.episode_v2 import EpisodeV2
from ray.rllib.evaluation.rollout_worker import RolloutWorker
from ray.rllib.policy.policy import Policy
from ray.rllib.utils.typing import AgentID, PolicyID

from mbag.agents.action_distributions import MbagActionDistribution
from mbag.environment.actions import MBAG_ACTION_BREAK_PALETTE_NAME, MbagAction
from mbag.environment.types import MbagInfoDict
from mbag.rllib.alpha_zero import EXPECTED_OWN_REWARDS, EXPECTED_REWARDS
from mbag.rllib.rllib_env import unwrap_mbag_env


class MbagCallbacks(AlphaZeroDefaultCallbacks):
    def _get_last_info(
        self, episode: Union[Episode, EpisodeV2], agent_id: AgentID
    ) -> MbagInfoDict:
        if isinstance(episode, Episode):
            return cast(MbagInfoDict, episode.last_info_for(agent_id))
        else:
            return cast(MbagInfoDict, episode._last_infos[agent_id])

    def on_train_result(self, *, algorithm: Algorithm, result: Dict, **kwargs) -> None:

        def update_worker_envs_global_timestep(worker: RolloutWorker):
            def update_env_global_timestep(env):
                if worker.global_vars is not None:
                    unwrap_mbag_env(env).update_global_timestep(
                        worker.global_vars["timestep"]
                    )

            worker.foreach_env(update_env_global_timestep)

        assert algorithm.workers is not None
        algorithm.workers.foreach_worker(update_worker_envs_global_timestep)

        super().on_train_result(algorithm=algorithm, result=result, **kwargs)

    def on_episode_start(
        self,
        worker: "RolloutWorker",
        base_env: BaseEnv,
        policies: Dict[PolicyID, Policy],
        episode: Union[Episode, EpisodeV2],
        env_index: Optional[int] = None,
        **kwargs,
    ) -> None:
        super().on_episode_start(
            worker=worker,
            base_env=base_env,
            policies=policies,
            episode=episode,
            **kwargs,
        )

        env = base_env.get_sub_environments()[env_index or 0]
        state = env.get_state()
        episode.user_data["state"] = state
        episode.user_data["valid_actions"] = (
            MbagActionDistribution.get_valid_action_types(unwrap_mbag_env(env).config)
        )

    def _initialize_episode_metrics_if_necessary(
        self,
        episode: Union[Episode, EpisodeV2],
        base_env: BaseEnv,
        env_index: Optional[int],
        policy_id: PolicyID,
    ) -> None:
        for valid_action_type in episode.user_data["valid_actions"]:
            action_type_name = MbagAction.ACTION_TYPE_NAMES[valid_action_type]
            action_key = f"{policy_id}/num_{action_type_name.lower()}"
            episode.custom_metrics.setdefault(action_key, 0)

            if valid_action_type in [
                MbagAction.BREAK_BLOCK,
                MbagAction.PLACE_BLOCK,
            ]:
                episode.custom_metrics.setdefault(
                    f"{policy_id}/num_correct_{action_type_name.lower()}", 0
                )

        episode.custom_metrics.setdefault(f"{policy_id}/num_unintentional_noop", 0)
        episode.custom_metrics.setdefault(f"{policy_id}/own_reward", 0)
        episode.custom_metrics.setdefault(f"{policy_id}/goal_dependent_reward", 0)
        episode.custom_metrics.setdefault(f"{policy_id}/goal_independent_reward", 0)

        env = unwrap_mbag_env(base_env.get_sub_environments()[env_index or 0])
        width, height, depth = env.config["world_size"]
        if not env.config["abilities"]["inf_blocks"]:
            episode.custom_metrics.setdefault(
                f"{policy_id}/num_{MBAG_ACTION_BREAK_PALETTE_NAME}", 0
            )

    def on_episode_step(
        self,
        *,
        worker: "RolloutWorker",
        base_env: BaseEnv,
        policies: Optional[Dict[PolicyID, Policy]] = None,
        episode: Union[Episode, EpisodeV2],
        env_index: Optional[int] = None,
        **kwargs,
    ) -> None:
        assert policies is not None

        env = base_env.get_sub_environments()[env_index or 0]
        state = env.get_state()
        episode.user_data["state"] = state

        for player_index, agent_id in enumerate(episode.get_agents()):
            policy_id = worker.policy_mapping_fn(agent_id, episode, worker)
            self._initialize_episode_metrics_if_necessary(
                episode, base_env, env_index, policy_id
            )

            info_dict = self._get_last_info(episode, agent_id)
            episode.custom_metrics[f"{policy_id}/own_reward"] += info_dict["own_reward"]
            episode.custom_metrics[f"{policy_id}/goal_dependent_reward"] += info_dict[
                "goal_dependent_reward"
            ]
            episode.custom_metrics[f"{policy_id}/goal_independent_reward"] += info_dict[
                "goal_independent_reward"
            ]

            # Log what action the agent made
            action = info_dict["action"]
            if action.action_type == MbagAction.BREAK_BLOCK and action.is_palette(
                env.config["abilities"]["inf_blocks"]
            ):
                action_type_name = MBAG_ACTION_BREAK_PALETTE_NAME
            else:
                action_type_name = MbagAction.ACTION_TYPE_NAMES[action.action_type]
            episode.custom_metrics[f"{policy_id}/num_{action_type_name.lower()}"] += 1

            if (
                info_dict["attempted_action"].action_type != MbagAction.NOOP
                and info_dict["action"].action_type == MbagAction.NOOP
            ):
                episode.custom_metrics[f"{policy_id}/num_unintentional_noop"] += 1

            if info_dict["action_correct"]:
                episode.custom_metrics[
                    f"{policy_id}/num_correct_{action_type_name.lower()}"
                ] += 1

            expected_reward: Optional[float] = episode.user_data.get(
                EXPECTED_REWARDS, {}
            ).get(player_index)
            if expected_reward is not None:
                episode.custom_metrics.setdefault(f"{policy_id}/expected_reward", 0)
                episode.custom_metrics[
                    f"{policy_id}/expected_reward"
                ] += expected_reward
            expected_own_reward: Optional[float] = episode.user_data.get(
                EXPECTED_OWN_REWARDS, {}
            ).get(player_index)
            if expected_own_reward is not None:
                episode.custom_metrics.setdefault(f"{policy_id}/expected_own_reward", 0)
                episode.custom_metrics[
                    f"{policy_id}/expected_own_reward"
                ] += expected_own_reward

        if isinstance(episode, EpisodeV2):
            env_config = unwrap_mbag_env(env).config
            total_seconds = (
                episode.total_env_steps * env_config["malmo"]["action_delay"]
            )
            rounded_minutes = int(total_seconds // 60)
            if rounded_minutes > 0:
                goal_percentage_key = f"goal_percentage_{rounded_minutes}_min"
                if goal_percentage_key not in episode.custom_metrics:
                    info_dict = self._get_last_info(episode, "player_0")
                    episode.custom_metrics[goal_percentage_key] = info_dict[
                        "goal_percentage"
                    ]

            for agent_id in episode.get_agents():
                policy_id = worker.policy_mapping_fn(agent_id, episode, worker)
                for metric_key in list(episode.custom_metrics.keys()):
                    if not (
                        metric_key.startswith(f"{policy_id}/")
                        and not metric_key.startswith(
                            f"{policy_id}/per_minute_metrics/"
                        )
                    ):
                        continue
                    metric_name = metric_key[len(f"{policy_id}/") :]
                    if rounded_minutes > 0:
                        metric_min_key = f"{policy_id}/per_minute_metrics/{metric_name}_{rounded_minutes}_min"
                        if metric_min_key not in episode.custom_metrics:
                            episode.custom_metrics[metric_min_key] = (
                                episode.custom_metrics[metric_key]
                            )

    def on_episode_end(
        self,
        *,
        worker: RolloutWorker,
        base_env: BaseEnv,
        policies: Dict[PolicyID, Policy],
        episode: Union[Episode, EpisodeV2],
        env_index: Optional[int] = None,
        **kwargs,
    ) -> None:
        super().on_episode_end(
            worker=worker,
            base_env=base_env,
            policies=policies,
            episode=episode,
            env_index=env_index,
            **kwargs,
        )

        info_dict = self._get_last_info(episode, "player_0")
        episode.custom_metrics["goal_similarity"] = info_dict["goal_similarity"]
        episode.custom_metrics["goal_percentage"] = info_dict["goal_percentage"]
        env = unwrap_mbag_env(base_env.get_sub_environments()[env_index or 0])
        width, height, depth = env.config["world_size"]
        episode.custom_metrics["goal_distance"] = (
            width * height * depth - info_dict["goal_similarity"]
        )

        horizon_seconds = env.config["horizon"] * env.config["malmo"]["action_delay"]
        horizon_rounded_minutes = int(horizon_seconds // 60)
        for rounded_minutes in range(1, horizon_rounded_minutes + 1):
            goal_percentage_key = f"goal_percentage_{rounded_minutes}_min"
            episode.custom_metrics.setdefault(
                goal_percentage_key, episode.custom_metrics["goal_percentage"]
            )

            for agent_id in episode.get_agents():
                policy_id = worker.policy_mapping_fn(agent_id, episode, worker)
                for metric_key in list(episode.custom_metrics.keys()):
                    if not (
                        metric_key.startswith(f"{policy_id}/")
                        and not metric_key.startswith(
                            f"{policy_id}/per_minute_metrics/"
                        )
                    ):
                        continue
                    metric_name = metric_key[len(f"{policy_id}/") :]
                    if rounded_minutes > 0:
                        metric_min_key = f"{policy_id}/per_minute_metrics/{metric_name}_{rounded_minutes}_min"
                        if metric_min_key not in episode.custom_metrics:
                            episode.custom_metrics.setdefault(
                                metric_min_key, episode.custom_metrics[metric_key]
                            )

        for agent_id in episode.get_agents():
            policy_id = worker.policy_mapping_fn(agent_id, episode, worker)
            info_dict, self._get_last_info(episode, agent_id)
            episode.custom_metrics[f"{policy_id}/own_reward_prop"] = info_dict[
                "own_reward_prop"
            ]

            action_type_names = [
                MbagAction.ACTION_TYPE_NAMES[action_type]
                for action_type in [
                    MbagAction.BREAK_BLOCK,
                    MbagAction.PLACE_BLOCK,
                ]
            ]
            for action_type_name in action_type_names:
                num_correct = episode.custom_metrics.get(
                    f"{policy_id}/num_correct_{action_type_name.lower()}", 0
                )
                total = episode.custom_metrics.get(
                    f"{policy_id}/num_{action_type_name.lower()}", 0
                )
                percent_correct = num_correct / total if total != 0 else np.nan
                episode.custom_metrics[
                    f"{policy_id}/{action_type_name.lower()}_accuracy"
                ] = percent_correct

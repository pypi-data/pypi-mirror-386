from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Generator, List

import numpy as np
import torch
import torch as th
from gymnasium import spaces
from stable_baselines3.common.buffers import RolloutBuffer
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.on_policy_algorithm import OnPolicyAlgorithm
from stable_baselines3.common.utils import obs_as_tensor
from stable_baselines3.common.vec_env import VecEnv
from stable_baselines3.common.vec_env.base_vec_env import VecEnvObs

from async_gym_agents.agents.injector import AsyncAgentInjector


@dataclass
class Transition:
    actions: np.ndarray
    values: torch.Tensor
    log_probs: torch.Tensor
    last_obs: VecEnvObs
    new_obs: VecEnvObs
    rewards: np.ndarray
    dones: np.ndarray
    last_dones: np.ndarray
    infos: list[Dict]
    index: int


class OnPolicyAlgorithmInjector(AsyncAgentInjector, OnPolicyAlgorithm):
    def __init__(self, *args, max_episodes_in_buffer: int = 8, **kwargs) -> None:
        super().__init__(max_episodes_in_buffer)
        super(AsyncAgentInjector, self).__init__(*args, **kwargs)

    def train(self, *args, **kwargs) -> None:
        # update self.training_policy
        with self.training_policy_lock:
            super().train()
        self.training_policy_version += 1

    def _excluded_save_params(self) -> List[str]:
        return [
            *super()._excluded_save_params(),
            *super(AsyncAgentInjector, self)._excluded_save_params(),
        ]

    def _episode_generator(self, index: int) -> Generator[list, None, None]:
        """
        Continuously plays the game and returns episodes of Transitions
        """
        env = self.get_indexable_env()
        last_obs = env.reset(index=index)
        last_dones = np.ones((1,), dtype=bool)

        episode = []

        while self.running:
            with th.no_grad():
                # Convert to pytorch tensor or to TensorDict
                obs_tensor = obs_as_tensor(last_obs, self.device)
                actions, values, log_probs = self.policy(obs_tensor)
            actions = actions.cpu().numpy()

            # Rescale and perform action
            clipped_actions = actions

            if isinstance(self.action_space, spaces.Box):
                if self.policy.squash_output:
                    # Unscale the actions to match env bounds
                    # if they were previously squashed (scaled in [-1, 1])
                    clipped_actions = self.policy.unscale_action(clipped_actions)
                else:
                    # Otherwise, clip the actions to avoid out-of-bound error
                    # as we are sampling from an unbounded Gaussian distribution
                    clipped_actions = np.clip(
                        actions, self.action_space.low, self.action_space.high
                    )

            new_obs, rewards, dones, infos = env.step(clipped_actions, index=index)

            if isinstance(self.action_space, spaces.Discrete):
                # Reshape in case of discrete action
                actions = actions.reshape(-1, 1)

            # Store transition
            episode.append(
                Transition(
                    actions,
                    values,
                    log_probs,
                    deepcopy(last_obs),
                    deepcopy(new_obs),
                    rewards,
                    dones,
                    last_dones,
                    infos,
                    index,
                )
            )
            last_obs = new_obs
            last_dones = dones

            # Start a new episode
            if any(dones):
                yield episode
                episode = []
                self.sync_training_policy_to_rollout_policy_weights_only(index)

    def collect_rollouts(
        self,
        env: VecEnv,
        callback: BaseCallback,
        rollout_buffer: RolloutBuffer,
        n_rollout_steps: int,
    ) -> bool:
        """
        Collect experiences using the current policy and fill a ``RolloutBuffer``.
        The term rollout here refers to the model-free notion and should not
        be used with the concept of rollout used in model-based RL or planning.

        :param env: The training environment.
        :param callback: Callback that will be called at each step.
            (and at the beginning and end of the rollout)
        :param rollout_buffer: Buffer to fill with rollouts.
        :param n_rollout_steps: Number of experiences to collect per environment.
        :return: True if the function returned with at least `n_rollout_steps`.
            Collected, False if callback terminated rollout prematurely.
        """
        assert self._last_obs is not None, "No previous observation was provided"

        # Switch to eval mode (this affects batch norm / dropout)
        self.policy.set_training_mode(False)

        n_steps = 0
        rollout_buffer.reset()

        # Sample new weights for the state-dependent exploration
        if self.use_sde:
            self.policy.reset_noise(1)

        if not self.initialized:
            self._initialize_threads()

        callback.on_rollout_start()

        new_obs = None
        dones = None
        while n_steps < n_rollout_steps:
            if (
                self.use_sde
                and self.sde_sample_freq > 0
                and n_steps % self.sde_sample_freq == 0
            ):
                # Sample a new noise matrix
                self.policy.reset_noise(1)

            # Fetch transitions from workers
            transition: Transition = self.fetch_transition()

            # Make locals available for callbacks
            new_obs = transition.new_obs
            self._last_obs = transition.last_obs
            actions = transition.actions
            rewards = transition.rewards
            self._last_episode_starts = transition.last_dones
            values = transition.values
            log_probs = transition.log_probs
            dones = transition.dones
            infos = transition.infos

            self.num_timesteps += 1

            # Give access to local variables
            callback.update_locals(locals())
            if not callback.on_step():
                return False

            self._update_info_buffer(infos, dones)
            n_steps += 1

            # Handle timeout by bootstrapping with value function
            # see GitHub issue #633
            for idx, done in enumerate(dones):
                if (
                    done
                    and infos[idx].get("terminal_observation") is not None
                    and infos[idx].get("TimeLimit.truncated", False)
                ):
                    terminal_obs = self.policy.obs_to_tensor(
                        infos[idx]["terminal_observation"]
                    )[0]
                    with th.no_grad():
                        terminal_value = self.policy.predict_values(terminal_obs)[0]
                    rewards[idx] += self.gamma * terminal_value

            rollout_buffer.add(
                self._last_obs,
                actions,
                rewards,
                self._last_episode_starts,
                values,
                log_probs,
            )

        with th.no_grad():
            # Compute value for the last timestep
            values = self.policy.predict_values(obs_as_tensor(new_obs, self.device))

        rollout_buffer.compute_returns_and_advantage(last_values=values, dones=dones)

        callback.update_locals(locals())

        callback.on_rollout_end()

        return True

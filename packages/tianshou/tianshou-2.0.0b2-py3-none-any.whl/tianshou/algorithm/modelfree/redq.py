from dataclasses import dataclass
from typing import Any, Literal, TypeVar, cast

import gymnasium as gym
import numpy as np
import torch
from torch.distributions import Independent, Normal

from tianshou.algorithm.modelfree.ddpg import (
    ActorCriticOffPolicyAlgorithm,
    ContinuousPolicyWithExplorationNoise,
    DDPGTrainingStats,
)
from tianshou.algorithm.modelfree.sac import Alpha
from tianshou.algorithm.optim import OptimizerFactory
from tianshou.data import Batch
from tianshou.data.types import (
    DistLogProbBatchProtocol,
    ObsBatchProtocol,
    RolloutBatchProtocol,
)
from tianshou.exploration import BaseNoise
from tianshou.utils.net.continuous import ContinuousActorProbabilistic


@dataclass
class REDQTrainingStats(DDPGTrainingStats):
    """A data structure for storing loss statistics of the REDQ learn step."""

    alpha: float | None = None
    alpha_loss: float | None = None


TREDQTrainingStats = TypeVar("TREDQTrainingStats", bound=REDQTrainingStats)


class REDQPolicy(ContinuousPolicyWithExplorationNoise):
    def __init__(
        self,
        *,
        actor: torch.nn.Module | ContinuousActorProbabilistic,
        exploration_noise: BaseNoise | Literal["default"] | None = None,
        action_space: gym.spaces.Space,
        deterministic_eval: bool = True,
        action_scaling: bool = True,
        action_bound_method: Literal["clip"] | None = "clip",
        observation_space: gym.Space | None = None,
    ):
        """
        :param actor: The actor network following the rules (s -> model_output)
        :param action_space: the environment's action_space.
        :param deterministic_eval: flag indicating whether the policy should use deterministic
            actions (using the mode of the action distribution) instead of stochastic ones
            (using random sampling) during evaluation.
            When enabled, the policy will always select the most probable action according to
            the learned distribution during evaluation phases, while still using stochastic
            sampling during training. This creates a clear distinction between exploration
            (training) and exploitation (evaluation) behaviors.
            Deterministic actions are generally preferred for final deployment and reproducible
            evaluation as they provide consistent behavior, reduce variance in performance
            metrics, and are more interpretable for human observers.
            Note that this parameter only affects behavior when the policy is not within a
            training step. When collecting rollouts for training, actions remain stochastic
            regardless of this setting to maintain proper exploration behaviour.
        :param observation_space: the environment's observation space
        :param action_scaling: flag indicating whether, for continuous action spaces, actions
            should be scaled from the standard neural network output range [-1, 1] to the
            environment's action space range [action_space.low, action_space.high].
            This applies to continuous action spaces only (gym.spaces.Box) and has no effect
            for discrete spaces.
            When enabled, policy outputs are expected to be in the normalized range [-1, 1]
            (after bounding), and are then linearly transformed to the actual required range.
            This improves neural network training stability, allows the same algorithm to work
            across environments with different action ranges, and standardizes exploration
            strategies.
            Should be disabled if the actor model already produces outputs in the correct range.
        :param action_bound_method: the method used for bounding actions in continuous action spaces
            to the range [-1, 1] before scaling them to the environment's action space (provided
            that `action_scaling` is enabled).
            This applies to continuous action spaces only (`gym.spaces.Box`) and should be set to None
            for discrete spaces.
            When set to "clip", actions exceeding the [-1, 1] range are simply clipped to this
            range. When set to "tanh", a hyperbolic tangent function is applied, which smoothly
            constrains outputs to [-1, 1] while preserving gradients.
            The choice of bounding method affects both training dynamics and exploration behavior.
            Clipping provides hard boundaries but may create plateau regions in the gradient
            landscape, while tanh provides smoother transitions but can compress sensitivity
            near the boundaries.
            Should be set to None if the actor model inherently produces bounded outputs.
            Typically used together with `action_scaling=True`.
        """
        super().__init__(
            exploration_noise=exploration_noise,
            action_space=action_space,
            observation_space=observation_space,
            action_scaling=action_scaling,
            action_bound_method=action_bound_method,
        )
        self.actor = actor
        self.deterministic_eval = deterministic_eval
        self._eps = np.finfo(np.float32).eps.item()

    def forward(  # type: ignore
        self,
        batch: ObsBatchProtocol,
        state: dict | Batch | np.ndarray | None = None,
        **kwargs: Any,
    ) -> DistLogProbBatchProtocol:
        (loc_B, scale_B), h_BH = self.actor(batch.obs, state=state, info=batch.info)
        dist = Independent(Normal(loc_B, scale_B), 1)
        if self.deterministic_eval and not self.is_within_training_step:
            act_B = dist.mode
        else:
            act_B = dist.rsample()
        log_prob = dist.log_prob(act_B).unsqueeze(-1)
        # apply correction for Tanh squashing when computing logprob from Gaussian
        # You can check out the original SAC paper (arXiv 1801.01290): Eq 21.
        # in appendix C to get some understanding of this equation.
        squashed_action = torch.tanh(act_B)
        log_prob = log_prob - torch.log((1 - squashed_action.pow(2)) + self._eps).sum(
            -1,
            keepdim=True,
        )
        result = Batch(
            logits=(loc_B, scale_B),
            act=squashed_action,
            state=h_BH,
            dist=dist,
            log_prob=log_prob,
        )
        return cast(DistLogProbBatchProtocol, result)


class REDQ(ActorCriticOffPolicyAlgorithm[REDQPolicy, DistLogProbBatchProtocol]):
    """Implementation of REDQ. arXiv:2101.05982."""

    def __init__(
        self,
        *,
        policy: REDQPolicy,
        policy_optim: OptimizerFactory,
        critic: torch.nn.Module,
        critic_optim: OptimizerFactory,
        ensemble_size: int = 10,
        subset_size: int = 2,
        tau: float = 0.005,
        gamma: float = 0.99,
        alpha: float | Alpha = 0.2,
        n_step_return_horizon: int = 1,
        actor_delay: int = 20,
        deterministic_eval: bool = True,
        target_mode: Literal["mean", "min"] = "min",
    ) -> None:
        """
        :param policy: the policy
        :param policy_optim: the optimizer factory for the policy's model.
        :param critic: the critic network. (s, a -> Q(s, a))
        :param critic_optim: the optimizer factory for the critic network.
        :param ensemble_size: the total number of critic networks in the ensemble.
            This parameter implements the randomized ensemble approach described in REDQ.
            The algorithm maintains `ensemble_size` different critic networks that all share the same
            architecture. During target value computation, a random subset of these networks (determined
            by `subset_size`) is used.
            Larger values increase the diversity of the ensemble but require more memory and computation.
            The original paper recommends a value of 10 for most tasks, balancing performance and
            computational efficiency.
        :param subset_size: the number of critic networks randomly selected from the ensemble for
            computing target Q-values.
            During each update, the algorithm samples `subset_size` networks from the ensemble of
            `ensemble_size` networks without replacement.
            The target Q-value is then calculated as either the minimum or mean (based on `target_mode`)
            of the predictions from this subset.
            Smaller values increase randomization and sample efficiency but may introduce more variance.
            Larger values provide more stable estimates but reduce the benefits of randomization.
            The REDQ paper recommends a value of 2 for optimal sample efficiency.
            Must satisfy 0 < subset_size <= ensemble_size.
        :param tau: the soft update coefficient for target networks, controlling the rate at which
            target networks track the learned networks.
            When the parameters of the target network are updated with the current (source) network's
            parameters, a weighted average is used: target = tau * source + (1 - tau) * target.
            Smaller values (closer to 0) create more stable but slower learning as target networks
            change more gradually. Higher values (closer to 1) allow faster learning but may reduce
            stability.
            Typically set to a small value (0.001 to 0.01) for most reinforcement learning tasks.
        :param gamma: the discount factor in [0, 1] for future rewards.
            This determines how much future rewards are valued compared to immediate ones.
            Lower values (closer to 0) make the agent focus on immediate rewards, creating "myopic"
            behavior. Higher values (closer to 1) make the agent value long-term rewards more,
            potentially improving performance in tasks where delayed rewards are important but
            increasing training variance by incorporating more environmental stochasticity.
            Typically set between 0.9 and 0.99 for most reinforcement learning tasks
        :param alpha: the entropy regularization coefficient, which balances exploration and exploitation.
            This coefficient controls how much the agent values randomness in its policy versus
            pursuing higher rewards.
            Higher values (e.g., 0.5-1.0) strongly encourage exploration by rewarding the agent
            for maintaining diverse action choices, even if this means selecting some lower-value actions.
            Lower values (e.g., 0.01-0.1) prioritize exploitation, allowing the policy to become
            more focused on the highest-value actions.
            A value of 0 would completely remove entropy regularization, potentially leading to
            premature convergence to suboptimal deterministic policies.
            Can be provided as a fixed float (0.2 is a reasonable default) or as an instance of,
            in particular, class `AutoAlpha` for automatic tuning during training.
        :param n_step_return_horizon: the number of future steps (> 0) to consider when computing temporal
            difference (TD) targets. Controls the balance between TD learning and Monte Carlo methods:
            higher values reduce bias (by relying less on potentially inaccurate value estimates)
            but increase variance (by incorporating more environmental stochasticity and reducing
            the averaging effect). A value of 1 corresponds to standard TD learning with immediate
            bootstrapping, while very large values approach Monte Carlo-like estimation that uses
            complete episode returns.
        :param actor_delay: the number of critic updates performed before each actor update.
            The actor network is only updated once for every actor_delay critic updates, implementing
            a delayed policy update strategy similar to TD3.
            Larger values stabilize training by allowing critics to become more accurate before policy updates.
            Smaller values allow the policy to adapt more quickly but may lead to less stable learning.
            The REDQ paper recommends a value of 20 for most tasks.
        :param target_mode: the method used to aggregate Q-values from the subset of critic networks.
            Can be either "min" or "mean".
            If "min", uses the minimum Q-value across the selected subset of critics for each state-action pair.
            If "mean", uses the average Q-value across the selected subset of critics.
            Using "min" helps prevent overestimation bias but may lead to more conservative value estimates.
            Using "mean" provides more optimistic value estimates but may suffer from overestimation bias.
            Default is "min" following the conservative value estimation approach common in recent Q-learning
            algorithms.
        """
        if target_mode not in ("min", "mean"):
            raise ValueError(f"Unsupported target_mode: {target_mode}")
        if not 0 < subset_size <= ensemble_size:
            raise ValueError(
                f"Invalid choice of ensemble size or subset size. "
                f"Should be 0 < {subset_size=} <= {ensemble_size=}",
            )
        super().__init__(
            policy=policy,
            policy_optim=policy_optim,
            critic=critic,
            critic_optim=critic_optim,
            tau=tau,
            gamma=gamma,
            n_step_return_horizon=n_step_return_horizon,
        )
        self.ensemble_size = ensemble_size
        self.subset_size = subset_size

        self.target_mode = target_mode
        self.critic_gradient_step = 0
        self.actor_delay = actor_delay
        self.deterministic_eval = deterministic_eval
        self.__eps = np.finfo(np.float32).eps.item()

        self._last_actor_loss = 0.0  # only for logging purposes

        self.alpha = Alpha.from_float_or_instance(alpha)

    def _target_q_compute_value(
        self, obs_batch: Batch, act_batch: DistLogProbBatchProtocol
    ) -> torch.Tensor:
        a_ = act_batch.act
        sample_ensemble_idx = np.random.choice(self.ensemble_size, self.subset_size, replace=False)
        qs = self.critic_old(obs_batch.obs, a_)[sample_ensemble_idx, ...]
        if self.target_mode == "min":
            target_q, _ = torch.min(qs, dim=0)
        elif self.target_mode == "mean":
            target_q = torch.mean(qs, dim=0)
        else:
            raise ValueError(f"Invalid target_mode: {self.target_mode}")

        target_q -= self.alpha.value * act_batch.log_prob

        return target_q

    def _update_with_batch(self, batch: RolloutBatchProtocol) -> REDQTrainingStats:  # type: ignore
        # critic ensemble
        weight = getattr(batch, "weight", 1.0)
        current_qs = self.critic(batch.obs, batch.act).flatten(1)
        target_q = batch.returns.flatten()
        td = current_qs - target_q
        critic_loss = (td.pow(2) * weight).mean()
        self.critic_optim.step(critic_loss)
        batch.weight = torch.mean(td, dim=0)  # prio-buffer
        self.critic_gradient_step += 1

        alpha_loss = None
        # actor
        if self.critic_gradient_step % self.actor_delay == 0:
            obs_result = self.policy(batch)
            a = obs_result.act
            current_qa = self.critic(batch.obs, a).mean(dim=0).flatten()
            actor_loss = (self.alpha.value * obs_result.log_prob.flatten() - current_qa).mean()
            self.policy_optim.step(actor_loss)

            # The entropy of a Gaussian policy can be expressed as -log_prob + a constant (which we ignore)
            entropy = -obs_result.log_prob.detach()
            alpha_loss = self.alpha.update(entropy)

            self._last_actor_loss = actor_loss.item()

        self._update_lagged_network_weights()

        return REDQTrainingStats(
            actor_loss=self._last_actor_loss,
            critic_loss=critic_loss.item(),
            alpha=self.alpha.value,
            alpha_loss=alpha_loss,
        )

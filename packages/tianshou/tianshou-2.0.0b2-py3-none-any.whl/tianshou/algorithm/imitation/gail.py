from dataclasses import dataclass

import numpy as np
import torch
import torch.nn.functional as F

from tianshou.algorithm.modelfree.a2c import A2CTrainingStats
from tianshou.algorithm.modelfree.ppo import PPO
from tianshou.algorithm.modelfree.reinforce import ProbabilisticActorPolicy
from tianshou.algorithm.optim import OptimizerFactory
from tianshou.data import (
    ReplayBuffer,
    SequenceSummaryStats,
    to_numpy,
    to_torch,
)
from tianshou.data.types import LogpOldProtocol, RolloutBatchProtocol
from tianshou.utils.net.common import ModuleWithVectorOutput
from tianshou.utils.net.continuous import ContinuousCritic
from tianshou.utils.net.discrete import DiscreteCritic
from tianshou.utils.torch_utils import torch_device


@dataclass(kw_only=True)
class GailTrainingStats(A2CTrainingStats):
    disc_loss: SequenceSummaryStats
    acc_pi: SequenceSummaryStats
    acc_exp: SequenceSummaryStats


class GAIL(PPO):
    """Implementation of Generative Adversarial Imitation Learning. arXiv:1606.03476."""

    def __init__(
        self,
        *,
        policy: ProbabilisticActorPolicy,
        critic: torch.nn.Module | ContinuousCritic | DiscreteCritic,
        optim: OptimizerFactory,
        expert_buffer: ReplayBuffer,
        disc_net: torch.nn.Module,
        disc_optim: OptimizerFactory,
        disc_update_num: int = 4,
        eps_clip: float = 0.2,
        dual_clip: float | None = None,
        value_clip: bool = False,
        advantage_normalization: bool = True,
        recompute_advantage: bool = False,
        vf_coef: float = 0.5,
        ent_coef: float = 0.01,
        max_grad_norm: float | None = None,
        gae_lambda: float = 0.95,
        max_batchsize: int = 256,
        gamma: float = 0.99,
        return_scaling: bool = False,
    ) -> None:
        """
        :param policy: the policy (which must use an actor with known output dimension, i.e.
            any Tianshou `Actor` implementation or other subclass of `ModuleWithVectorOutput`).
        :param critic: the critic network. (s -> V(s))
        :param optim: the optimizer factory for the actor and critic networks.
        :param expert_buffer: the replay buffer containing expert experience.
        :param disc_net: the discriminator neural network that distinguishes between expert and policy behaviors.
            Takes concatenated state-action pairs [obs, act] as input and outputs an unbounded logit value.
            The raw output is transformed in the algorithm using sigmoid functions: o(output) for expert
            probability and -log(1-o(-output)) for policy rewards.
            Positive output values indicate the discriminator believes the behavior is from an expert.
            Negative output values indicate the discriminator believes the behavior is from the policy.
            The network architecture should end with a linear layer of output size 1 without any
            activation function, as sigmoid operations are applied separately.
        :param disc_optim: the optimizer factory for the discriminator network.
        :param disc_update_num: the number of discriminator update steps performed for each policy update step.
            Controls the learning dynamics between the policy and the discriminator.
            Higher values strengthen the discriminator relative to the policy, potentially improving
            the quality of the reward signal but slowing down training.
            Lower values allow faster policy updates but may result in a weaker discriminator that fails
            to properly distinguish between expert and policy behaviors.
            Typical values range from 1 to 10, with the original GAIL paper using multiple discriminator
            updates per policy update.
        :param eps_clip: determines the range of allowed change in the policy during a policy update:
            The ratio of action probabilities indicated by the new and old policy is
            constrained to stay in the interval [1 - eps_clip, 1 + eps_clip].
            Small values thus force the new policy to stay close to the old policy.
            Typical values range between 0.1 and 0.3, the value of 0.2 is recommended
            in the original PPO paper.
            The optimal value depends on the environment; more stochastic environments may
            need larger values.
        :param dual_clip: a clipping parameter (denoted as c in the literature) that prevents
            excessive pessimism in policy updates for negative-advantage actions.
            Excessive pessimism occurs when the policy update too strongly reduces the probability
            of selecting actions that led to negative advantages, potentially eliminating useful
            actions based on limited negative experiences.
            When enabled (c > 1), the objective for negative advantages becomes:
            max(min(r(θ)A, clip(r(θ), 1-ε, 1+ε)A), c*A), where min(r(θ)A, clip(r(θ), 1-ε, 1+ε)A)
            is the original single-clipping objective determined by `eps_clip`.
            This creates a floor on negative policy gradients, maintaining some probability
            of exploring actions despite initial negative outcomes.
            Larger values (e.g., 2.0 to 5.0) maintain more exploration, while values closer
            to 1.0 provide less protection against pessimistic updates.
            Set to None to disable dual clipping.
        :param value_clip: flag indicating whether to enable clipping for value function updates.
            When enabled, restricts how much the value function estimate can change from its
            previous prediction, using the same clipping range as the policy updates (eps_clip).
            This stabilizes training by preventing large fluctuations in value estimates,
            particularly useful in environments with high reward variance.
            The clipped value loss uses a pessimistic approach, taking the maximum of the
            original and clipped value errors:
            max((returns - value)², (returns - v_clipped)²)
            Setting to True often improves training stability but may slow convergence.
            Implementation follows the approach mentioned in arXiv:1811.02553v3 Sec. 4.1.
        :param advantage_normalization: whether to do per mini-batch advantage
            normalization.
        :param recompute_advantage: whether to recompute advantage every update
            repeat according to https://arxiv.org/pdf/2006.05990.pdf Sec. 3.5.
        :param vf_coef: coefficient that weights the value loss relative to the actor loss in
            the overall loss function.
            Higher values prioritize accurate value function estimation over policy improvement.
            Controls the trade-off between policy optimization and value function fitting.
            Typically set between 0.5 and 1.0 for most actor-critic implementations.
        :param ent_coef: coefficient that weights the entropy bonus relative to the actor loss.
            Controls the exploration-exploitation trade-off by encouraging policy entropy.
            Higher values promote more exploration by encouraging a more uniform action distribution.
            Lower values focus more on exploitation of the current policy's knowledge.
            Typically set between 0.01 and 0.05 for most actor-critic implementations.
        :param max_grad_norm: the maximum L2 norm threshold for gradient clipping.
            When not None, gradients will be rescaled using to ensure their L2 norm does not
            exceed this value. This prevents exploding gradients and stabilizes training by
            limiting the size of parameter updates.
            Set to None to disable gradient clipping.
        :param gae_lambda: the lambda parameter in [0, 1] for generalized advantage estimation (GAE).
            Controls the bias-variance tradeoff in advantage estimates, acting as a
            weighting factor for combining different n-step advantage estimators. Higher values
            (closer to 1) reduce bias but increase variance by giving more weight to longer
            trajectories, while lower values (closer to 0) reduce variance but increase bias
            by relying more on the immediate TD error and value function estimates. At λ=0,
            GAE becomes equivalent to the one-step TD error (high bias, low variance); at λ=1,
            it becomes equivalent to Monte Carlo advantage estimation (low bias, high variance).
            Intermediate values create a weighted average of n-step returns, with exponentially
            decaying weights for longer-horizon returns. Typically set between 0.9 and 0.99 for
            most policy gradient methods.
        :param max_batchsize: the maximum number of samples to process at once when computing
            generalized advantage estimation (GAE) and value function predictions.
            Controls memory usage by breaking large batches into smaller chunks processed sequentially.
            Higher values may increase speed but require more GPU/CPU memory; lower values
            reduce memory requirements but may increase computation time. Should be adjusted
            based on available hardware resources and total batch size of your training data.
        :param gamma: the discount factor in [0, 1] for future rewards.
            This determines how much future rewards are valued compared to immediate ones.
            Lower values (closer to 0) make the agent focus on immediate rewards, creating "myopic"
            behavior. Higher values (closer to 1) make the agent value long-term rewards more,
            potentially improving performance in tasks where delayed rewards are important but
            increasing training variance by incorporating more environmental stochasticity.
            Typically set between 0.9 and 0.99 for most reinforcement learning tasks
        :param return_scaling: flag indicating whether to enable scaling of estimated returns by
            dividing them by their running standard deviation without centering the mean.
            This reduces the magnitude variation of advantages across different episodes while
            preserving their signs and relative ordering.
            The use of running statistics (rather than batch-specific scaling) means that early
            training experiences may be scaled differently than later ones as the statistics evolve.
            When enabled, this improves training stability in environments with highly variable
            reward scales and makes the algorithm less sensitive to learning rate settings.
            However, it may reduce the algorithm's ability to distinguish between episodes with
            different absolute return magnitudes.
            Best used in environments where the relative ordering of actions is more important
            than the absolute scale of returns.
        """
        super().__init__(
            policy=policy,
            critic=critic,
            optim=optim,
            eps_clip=eps_clip,
            dual_clip=dual_clip,
            value_clip=value_clip,
            advantage_normalization=advantage_normalization,
            recompute_advantage=recompute_advantage,
            vf_coef=vf_coef,
            ent_coef=ent_coef,
            max_grad_norm=max_grad_norm,
            gae_lambda=gae_lambda,
            max_batchsize=max_batchsize,
            gamma=gamma,
            return_scaling=return_scaling,
        )
        self.disc_net = disc_net
        self.disc_optim = self._create_optimizer(self.disc_net, disc_optim)
        self.disc_update_num = disc_update_num
        self.expert_buffer = expert_buffer
        actor = self.policy.actor
        if not isinstance(actor, ModuleWithVectorOutput):
            raise TypeError("GAIL requires the policy to use an actor with known output dimension.")
        self.action_dim = actor.get_output_dim()

    def _preprocess_batch(
        self,
        batch: RolloutBatchProtocol,
        buffer: ReplayBuffer,
        indices: np.ndarray,
    ) -> LogpOldProtocol:
        """Pre-process the data from the provided replay buffer.

        Used in :meth:`update`. Check out :ref:`process_fn` for more information.
        """
        # update reward
        with torch.no_grad():
            batch.rew = to_numpy(-F.logsigmoid(-self.disc(batch)).flatten())
        return super()._preprocess_batch(batch, buffer, indices)

    def disc(self, batch: RolloutBatchProtocol) -> torch.Tensor:
        device = torch_device(self.disc_net)
        obs = to_torch(batch.obs, device=device)
        act = to_torch(batch.act, device=device)
        return self.disc_net(torch.cat([obs, act], dim=1))

    def _update_with_batch(  # type: ignore[override]
        self,
        batch: LogpOldProtocol,
        batch_size: int | None,
        repeat: int,
    ) -> GailTrainingStats:
        # update discriminator
        losses = []
        acc_pis = []
        acc_exps = []
        bsz = len(batch) // self.disc_update_num
        for b in batch.split(bsz, merge_last=True):
            logits_pi = self.disc(b)
            exp_b = self.expert_buffer.sample(bsz)[0]
            logits_exp = self.disc(exp_b)
            loss_pi = -F.logsigmoid(-logits_pi).mean()
            loss_exp = -F.logsigmoid(logits_exp).mean()
            loss_disc = loss_pi + loss_exp
            self.disc_optim.step(loss_disc)
            losses.append(loss_disc.item())
            acc_pis.append((logits_pi < 0).float().mean().item())
            acc_exps.append((logits_exp > 0).float().mean().item())
        # update policy
        ppo_loss_stat = super()._update_with_batch(batch, batch_size, repeat)

        disc_losses_summary = SequenceSummaryStats.from_sequence(losses)
        acc_pi_summary = SequenceSummaryStats.from_sequence(acc_pis)
        acc_exps_summary = SequenceSummaryStats.from_sequence(acc_exps)

        return GailTrainingStats(
            **ppo_loss_stat.__dict__,
            disc_loss=disc_losses_summary,
            acc_pi=acc_pi_summary,
            acc_exp=acc_exps_summary,
        )

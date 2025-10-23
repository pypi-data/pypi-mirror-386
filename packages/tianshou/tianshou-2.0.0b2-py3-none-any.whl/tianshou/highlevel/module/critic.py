from abc import ABC, abstractmethod
from collections.abc import Sequence

import numpy as np
from sensai.util.string import ToStringMixin
from torch import nn

from tianshou.highlevel.env import Environments, EnvType
from tianshou.highlevel.module.actor import ActorFuture
from tianshou.highlevel.module.core import TDevice, init_linear_orthogonal
from tianshou.utils.net import continuous
from tianshou.utils.net.common import Actor, EnsembleLinear, ModuleType, Net
from tianshou.utils.net.continuous import ContinuousCritic
from tianshou.utils.net.discrete import DiscreteCritic


class CriticFactory(ToStringMixin, ABC):
    """Represents a factory for the generation of a critic module."""

    @abstractmethod
    def create_module(
        self,
        envs: Environments,
        device: TDevice,
        use_action: bool,
        discrete_last_size_use_action_shape: bool = False,
    ) -> nn.Module:
        """Creates the critic module.

        :param envs: the environments
        :param device: the torch device
        :param use_action: whether to expect the action as an additional input (in addition to the observations)
        :param discrete_last_size_use_action_shape: whether, for the discrete case, the output dimension shall use the action shape
        :return: the module
        """


class CriticFactoryDefault(CriticFactory):
    """A critic factory which, depending on the type of environment, creates a suitable MLP-based critic."""

    DEFAULT_HIDDEN_SIZES = (64, 64)

    def __init__(
        self,
        hidden_sizes: Sequence[int] = DEFAULT_HIDDEN_SIZES,
        hidden_activation: ModuleType = nn.ReLU,
    ):
        self.hidden_sizes = hidden_sizes
        self.hidden_activation = hidden_activation

    def create_module(
        self,
        envs: Environments,
        device: TDevice,
        use_action: bool,
        discrete_last_size_use_action_shape: bool = False,
    ) -> nn.Module:
        factory: CriticFactory
        env_type = envs.get_type()
        match env_type:
            case EnvType.CONTINUOUS:
                factory = CriticFactoryContinuousNet(
                    self.hidden_sizes,
                    activation=self.hidden_activation,
                )
            case EnvType.DISCRETE:
                factory = CriticFactoryDiscreteNet(
                    self.hidden_sizes,
                    activation=self.hidden_activation,
                )
            case _:
                raise ValueError(f"{env_type} not supported")
        return factory.create_module(
            envs,
            device,
            use_action,
            discrete_last_size_use_action_shape=discrete_last_size_use_action_shape,
        )


class CriticFactoryContinuousNet(CriticFactory):
    def __init__(self, hidden_sizes: Sequence[int], activation: ModuleType = nn.ReLU):
        self.hidden_sizes = hidden_sizes
        self.activation = activation

    def create_module(
        self,
        envs: Environments,
        device: TDevice,
        use_action: bool,
        discrete_last_size_use_action_shape: bool = False,
    ) -> nn.Module:
        action_shape = envs.get_action_shape() if use_action else 0
        net_c = Net(
            state_shape=envs.get_observation_shape(),
            action_shape=action_shape,
            hidden_sizes=self.hidden_sizes,
            concat=use_action,
            activation=self.activation,
        )
        critic = continuous.ContinuousCritic(preprocess_net=net_c).to(device)
        init_linear_orthogonal(critic)
        return critic


class CriticFactoryDiscreteNet(CriticFactory):
    def __init__(self, hidden_sizes: Sequence[int], activation: ModuleType = nn.ReLU):
        self.hidden_sizes = hidden_sizes
        self.activation = activation

    def create_module(
        self,
        envs: Environments,
        device: TDevice,
        use_action: bool,
        discrete_last_size_use_action_shape: bool = False,
    ) -> nn.Module:
        action_shape = envs.get_action_shape() if use_action else 0
        net_c = Net(
            state_shape=envs.get_observation_shape(),
            action_shape=action_shape,
            hidden_sizes=self.hidden_sizes,
            concat=use_action,
            activation=self.activation,
        )
        last_size = (
            int(np.prod(envs.get_action_shape())) if discrete_last_size_use_action_shape else 1
        )
        critic = DiscreteCritic(preprocess_net=net_c, last_size=last_size).to(device)
        init_linear_orthogonal(critic)
        return critic


class CriticFactoryReuseActor(CriticFactory):
    """A critic factory which reuses the actor's preprocessing component.

    This class is for internal use in experiment builders only.

    Reuse of the actor network is supported through the concept of an actor future (:class:`ActorFuture`).
    When the user declares that he wants to reuse the actor for the critic, we use this factory to support this,
    but the actor does not exist yet. So the factory instead receives the future, which will eventually be filled
    when the actor factory is called. When the creation method of this factory is eventually called, it can use the
    then-filled actor to create the critic.
    """

    def __init__(self, actor_future: ActorFuture):
        """:param actor_future: the object, which will hold the actor instance later when the critic is to be created"""
        self.actor_future = actor_future

    def _tostring_excludes(self) -> list[str]:
        return ["actor_future"]

    def create_module(
        self,
        envs: Environments,
        device: TDevice,
        use_action: bool,
        discrete_last_size_use_action_shape: bool = False,
    ) -> nn.Module:
        actor = self.actor_future.actor
        if not isinstance(actor, Actor):
            raise ValueError(
                f"Option critic_use_action can only be used if actor is of type {Actor.__class__.__name__}",
            )
        if envs.get_type().is_discrete():
            # TODO get rid of this prod pattern here and elsewhere
            last_size = (
                int(np.prod(envs.get_action_shape())) if discrete_last_size_use_action_shape else 1
            )
            return DiscreteCritic(
                preprocess_net=actor.get_preprocess_net(),
                last_size=last_size,
            ).to(device)
        elif envs.get_type().is_continuous():
            return ContinuousCritic(
                preprocess_net=actor.get_preprocess_net(),
                apply_preprocess_net_to_obs_only=True,
            ).to(device)
        else:
            raise ValueError


class CriticEnsembleFactory:
    @abstractmethod
    def create_module(
        self,
        envs: Environments,
        device: TDevice,
        ensemble_size: int,
        use_action: bool,
    ) -> nn.Module:
        pass


class CriticEnsembleFactoryDefault(CriticEnsembleFactory):
    """A critic ensemble factory which, depending on the type of environment, creates a suitable MLP-based critic."""

    DEFAULT_HIDDEN_SIZES = (64, 64)

    def __init__(self, hidden_sizes: Sequence[int] = DEFAULT_HIDDEN_SIZES):
        self.hidden_sizes = hidden_sizes

    def create_module(
        self,
        envs: Environments,
        device: TDevice,
        ensemble_size: int,
        use_action: bool,
    ) -> nn.Module:
        env_type = envs.get_type()
        factory: CriticEnsembleFactory
        match env_type:
            case EnvType.CONTINUOUS:
                factory = CriticEnsembleFactoryContinuousNet(self.hidden_sizes)
            case EnvType.DISCRETE:
                raise NotImplementedError("No default is implemented for the discrete case")
            case _:
                raise ValueError(f"{env_type} not supported")
        return factory.create_module(
            envs,
            device,
            ensemble_size,
            use_action,
        )


class CriticEnsembleFactoryContinuousNet(CriticEnsembleFactory):
    def __init__(self, hidden_sizes: Sequence[int]):
        self.hidden_sizes = hidden_sizes

    def create_module(
        self,
        envs: Environments,
        device: TDevice,
        ensemble_size: int,
        use_action: bool,
    ) -> nn.Module:
        def linear_layer(x: int, y: int) -> EnsembleLinear:
            return EnsembleLinear(ensemble_size, x, y)

        action_shape = envs.get_action_shape() if use_action else 0
        net_c = Net(
            state_shape=envs.get_observation_shape(),
            action_shape=action_shape,
            hidden_sizes=self.hidden_sizes,
            concat=use_action,
            activation=nn.Tanh,
            linear_layer=linear_layer,
        )
        critic = continuous.ContinuousCritic(
            preprocess_net=net_c,
            linear_layer=linear_layer,
            flatten_input=False,
        ).to(device)
        init_linear_orthogonal(critic)
        return critic

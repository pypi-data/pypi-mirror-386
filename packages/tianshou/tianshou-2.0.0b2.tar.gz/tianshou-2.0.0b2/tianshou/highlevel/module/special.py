from collections.abc import Sequence

from sensai.util.string import ToStringMixin

from tianshou.highlevel.env import Environments
from tianshou.highlevel.module.core import ModuleFactory, TDevice
from tianshou.highlevel.module.intermediate import IntermediateModuleFactory
from tianshou.utils.net.discrete import ImplicitQuantileNetwork


class ImplicitQuantileNetworkFactory(ModuleFactory, ToStringMixin):
    def __init__(
        self,
        preprocess_net_factory: IntermediateModuleFactory,
        hidden_sizes: Sequence[int] = (),
        num_cosines: int = 64,
    ):
        self.preprocess_net_factory = preprocess_net_factory
        self.hidden_sizes = hidden_sizes
        self.num_cosines = num_cosines

    def create_module(self, envs: Environments, device: TDevice) -> ImplicitQuantileNetwork:
        preprocess_net = self.preprocess_net_factory.create_intermediate_module(envs, device)
        return ImplicitQuantileNetwork(
            preprocess_net=preprocess_net.get_module_with_vector_output(),
            action_shape=envs.get_action_shape(),
            hidden_sizes=self.hidden_sizes,
            num_cosines=self.num_cosines,
        ).to(device)

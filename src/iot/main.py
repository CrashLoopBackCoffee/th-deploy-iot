import pulumi as p
import pulumi_kubernetes as k8s

from iot.config import ComponentConfig
from iot.mosquitto import Mosquitto


def main():
    config = p.Config()
    component_config = ComponentConfig.model_validate(config.get_object('config'))

    stack = p.get_stack()
    org = p.get_organization()
    k8s_stack_ref = p.StackReference(f'{org}/kubernetes/{stack}')

    k8s_provider = k8s.Provider('k8s', kubeconfig=k8s_stack_ref.get_output('kubeconfig'))

    Mosquitto('mosquitto', component_config, k8s_provider)

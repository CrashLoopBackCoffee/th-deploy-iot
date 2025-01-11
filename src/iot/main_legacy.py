import pulumi as p
import pulumi_cloudflare as cloudflare
import pulumi_docker as docker

from iot.config import ComponentConfig
from iot.mosquitto_legacy import create_mosquitto_legacy
from iot.mqtt_exporter_legacy import create_mqtt_prometheus_legacy


def main():
    component_config = ComponentConfig.model_validate(p.Config().get_object('config'))

    docker_provider = docker.Provider('synology', host='ssh://synology')

    opts = p.ResourceOptions(provider=docker_provider)

    cloudflare_provider = cloudflare.Provider(
        'cloudflare',
        api_key=component_config.cloudflare.api_key.value,
        email=component_config.cloudflare.email,
    )

    # Create networks so we don't have to expose all ports on the host
    network = docker.Network('iot', opts=opts)

    create_mosquitto_legacy(component_config, network, cloudflare_provider, opts)
    create_mqtt_prometheus_legacy(component_config, network, opts)

import pulumi as p
import pulumi_cloudflare as cloudflare
import pulumi_docker as docker

from iot.config import ComponentConfig
from iot.mosquitto import create_mosquitto

component_config = ComponentConfig.model_validate(p.Config().get_object('config'))

config = p.Config()
stack = p.get_stack()
org = p.get_organization()
minio_stack_ref = p.StackReference(f'{org}/s3/{stack}')


provider = docker.Provider('synology', host='ssh://synology')

opts = p.ResourceOptions(provider=provider)

cloudflare_provider = cloudflare.Provider(
    'cloudflare',
    api_key=str(component_config.cloudflare.api_key),
    email=component_config.cloudflare.email,
)

# Create networks so we don't have to expose all ports on the host
network = docker.Network('iot', opts=opts)

create_mosquitto(component_config, network, cloudflare_provider, opts)

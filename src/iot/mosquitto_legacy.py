import pulumi as p
import pulumi_cloudflare as cloudflare
import pulumi_command
import pulumi_docker as docker

from iot.cloudflare import create_cloudflare_cname
from iot.config import ComponentConfig
from iot.utils import directory_content, get_assets_path


def create_mosquitto_legacy(
    component_config: ComponentConfig,
    network: docker.Network,
    cloudflare_provider: cloudflare.Provider,
    opts: p.ResourceOptions,
):
    """
    Deploys mosquitto to the target host.
    """
    target_root_dir = component_config.target.root_dir
    target_host = component_config.target.host
    target_user = component_config.target.user

    create_cloudflare_cname('mqtt', component_config.cloudflare.zone, cloudflare_provider)

    # Create mosquitto-config folder
    mosquitto_config_dir_resource = pulumi_command.remote.Command(
        'create-mosquitto-config',
        connection=pulumi_command.remote.ConnectionArgs(host=target_host, user=target_user),
        create=f'mkdir -p {target_root_dir}/mosquitto-config',
    )
    mosquitto_data_dir_resource = pulumi_command.remote.Command(
        'create-mosquitto-data',
        connection=pulumi_command.remote.ConnectionArgs(host=target_host, user=target_user),
        create=f'mkdir -p {target_root_dir}/mosquitto-data',
    )

    local_mosquitto_path = get_assets_path() / 'mosquitto'

    sync_command = (
        f'rsync --rsync-path /bin/rsync -av --delete '
        f'{local_mosquitto_path}/ '
        f'{target_user}@{target_host}:{target_root_dir}/mosquitto-config/'
    )

    mosquitto_config = directory_content(local_mosquitto_path)
    mosquitto_config = pulumi_command.local.Command(
        'mosquitto-config',
        create=sync_command,
        triggers=[mosquitto_config, mosquitto_config_dir_resource.id],
    )

    image = docker.RemoteImage(
        'mosquitto',
        name=f'eclipse-mosquitto:{component_config.mosquitto.version}',
        keep_locally=True,
        opts=opts,
    )

    docker.Container(
        'mosquitto',
        image=image.image_id,
        name='mosquitto',
        ports=[{'internal': 1883, 'external': 1883}],
        volumes=[
            {
                'host_path': f'{target_root_dir}/mosquitto-config',
                'container_path': '/mosquitto/config',
            },
            {'host_path': f'{target_root_dir}/mosquitto-data', 'container_path': '/mosquitto/data'},
        ],
        networks_advanced=[{'name': network.name, 'aliases': ['mosquitto']}],
        restart='always',
        start=True,
        opts=p.ResourceOptions.merge(
            opts,
            p.ResourceOptions(
                depends_on=[
                    mosquitto_config,
                    mosquitto_config_dir_resource,
                    mosquitto_data_dir_resource,
                ]
            ),
        ),
    )

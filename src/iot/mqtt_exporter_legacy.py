import pulumi as p
import pulumi_command
import pulumi_docker as docker

from iot.config import ComponentConfig
from iot.utils import directory_content, get_assets_path


def create_mqtt_prometheus_legacy(
    component_config: ComponentConfig,
    network: docker.Network,
    opts: p.ResourceOptions,
):
    """
    Deploys mqtt exporter to the target host.
    """
    assert component_config.target
    target_root_dir = component_config.target.root_dir
    target_host = component_config.target.host
    target_user = component_config.target.user

    # Create mqtt2prometheus-config folder
    mqtt_prometheus_config_dir_resource = pulumi_command.remote.Command(
        'create-mqtt-prometheus-config',
        connection=pulumi_command.remote.ConnectionArgs(host=target_host, user=target_user),
        create=f'mkdir -p {target_root_dir}/mqtt2prometheus-config',
    )
    mqtt_prometheus_data_dir_resource = pulumi_command.remote.Command(
        'create-mqtt-prometheus-data',
        connection=pulumi_command.remote.ConnectionArgs(host=target_host, user=target_user),
        create=f'mkdir -p {target_root_dir}/mqtt2prometheus-data',
    )

    local_mqtt_exporter_path = get_assets_path() / 'mqtt2prometheus'

    sync_command = (
        f'rsync --rsync-path /bin/rsync -av --delete '
        f'{local_mqtt_exporter_path}/ '
        f'{target_user}@{target_host}:{target_root_dir}/mqtt2prometheus-config/'
    )

    mqtt_prometheus_config = directory_content(local_mqtt_exporter_path)
    mqtt_prometheus_config = pulumi_command.local.Command(
        'mqtt-prometheus-config',
        create=sync_command,
        triggers=[mqtt_prometheus_config, mqtt_prometheus_config_dir_resource.id],
    )

    assert component_config.mqtt2prometheus
    image = docker.RemoteImage(
        'mqtt-prometheus',
        name=f'ghcr.io/hikhvar/mqtt2prometheus:{component_config.mqtt2prometheus.version}',
        keep_locally=True,
        opts=opts,
    )

    docker.Container(
        'mqtt-prometheus',
        image=image.image_id,
        name='mqtt2prometheus',
        ports=[{'internal': 9641, 'external': 9641}],
        envs=[
            p.Output.format(
                'MQTT2PROM_MQTT_USER={}', component_config.mqtt2prometheus.username.value
            ),
            p.Output.format(
                'MQTT2PROM_MQTT_PASSWORD={}', component_config.mqtt2prometheus.password.value
            ),
        ],
        volumes=[
            {
                'host_path': f'{target_root_dir}/mqtt2prometheus-config/config.yaml',
                'container_path': '/config.yaml',
                'read_only': True,
            },
            {
                'host_path': f'{target_root_dir}/mqtt2prometheus-data',
                'container_path': '/var/lib/mqtt2prometheus',
            },
        ],
        networks_advanced=[{'name': network.name, 'aliases': ['mqtt2prometheus']}],
        restart='always',
        start=True,
        opts=p.ResourceOptions.merge(
            opts,
            p.ResourceOptions(
                depends_on=[
                    mqtt_prometheus_config,
                    mqtt_prometheus_config_dir_resource,
                    mqtt_prometheus_data_dir_resource,
                ]
            ),
        ),
    )

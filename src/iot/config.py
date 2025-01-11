import pathlib
import typing as t

import deploy_base.model
import pydantic

REPO_PREFIX = 'deploy-'


def get_pulumi_project():
    repo_dir = pathlib.Path().resolve()

    while not repo_dir.name.startswith(REPO_PREFIX):
        if not repo_dir.parents:
            raise ValueError('Could not find repo root')

        repo_dir = repo_dir.parent
    return repo_dir.name[len(REPO_PREFIX) :]


class StrictBaseModel(pydantic.BaseModel):
    model_config = {'extra': 'forbid'}


class PulumiSecret(StrictBaseModel):
    secure: pydantic.SecretStr

    def __str__(self):
        return str(self.secure)


class MosquittoConfig(StrictBaseModel):
    version: str
    hostname: str | None = None
    passwords: list[str] = []


class MqttPrometheusInstanceConfig(StrictBaseModel):
    name: str
    topic_path: str = pydantic.Field(alias='topic-path')
    device_id_regex: str | None = pydantic.Field(alias='device-id-regex', default=None)
    metrics: list[dict[str, t.Any]] = []


class MqttPrometheusConfig(StrictBaseModel):
    version: str
    username: deploy_base.model.OnePasswordRef
    password: deploy_base.model.OnePasswordRef
    instances: list[MqttPrometheusInstanceConfig] = []


class TargetConfig(StrictBaseModel):
    host: str
    user: str
    root_dir: str


class ComponentConfig(StrictBaseModel):
    target: TargetConfig | None = None
    cloudflare: deploy_base.model.CloudflareConfig | None = None
    mosquitto: MosquittoConfig
    mqtt2prometheus: MqttPrometheusConfig | None = None


class StackConfig(StrictBaseModel):
    model_config = {'alias_generator': lambda field_name: f'{get_pulumi_project()}:{field_name}'}
    config: ComponentConfig


class PulumiConfigRoot(StrictBaseModel):
    config: StackConfig

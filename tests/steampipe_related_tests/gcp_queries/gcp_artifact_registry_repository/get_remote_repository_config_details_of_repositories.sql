select
  name,
  remote_repository_config ->> 'AptRepository' as apt_repository,
  remote_repository_config ->> 'DockerRepository' as docker_repository,
  remote_repository_config ->> 'MavenRepository' as maven_repository,
  remote_repository_config ->> 'NpmRepository' as npm_repository,
  remote_repository_config ->> 'PythonRepository' as python_repository,
  remote_repository_config ->> 'YumRepository' as yum_repository
from
  gcp_artifact_registry_repository;
import os

from netfl.core.experiment import FLExperiment
from netfl.utils.resources import (
    WorkerHostResource,
    NetworkResource,
    DeviceResource,
    ClusterResource,
    ClusterResourceType,
)

from task import FLTask


task = FLTask()
num_clients = task.train_configs().num_clients

if num_clients % 2 != 0:
    raise ValueError("Expected an even number of clients.")

worker_host_resource = WorkerHostResource(cpu_clock=2.25)

server_resource = DeviceResource(
    name="server",
    cpu_cores=14,
    cpu_clock=2.0,
    memory=2048,
    network_resource=NetworkResource(bw=1000),
    worker_host_resource=worker_host_resource,
)

pi3_0_resource = DeviceResource(
    name="pi3_0",
    cpu_cores=4,
    cpu_clock=1.2,
    memory=1024,
    network_resource=NetworkResource(bw=100),
    worker_host_resource=worker_host_resource,
)

pi3_1_resource = DeviceResource(
    name="pi3_1",
    cpu_cores=4,
    cpu_clock=1.2,
    memory=1024,
    network_resource=NetworkResource(bw=100),
    worker_host_resource=worker_host_resource,
)

cloud_resource = ClusterResource(
    name="cloud",
    type=ClusterResourceType.CLOUD,
    device_resources=[server_resource],
)

edge_0_resource = ClusterResource(
    name="edge_0",
    type=ClusterResourceType.EDGE,
    device_resources=(num_clients // 2) * [pi3_0_resource],
)

edge_1_resource = ClusterResource(
    name="edge_1",
    type=ClusterResourceType.EDGE,
    device_resources=(num_clients // 2) * [pi3_1_resource],
)

exp = FLExperiment(
    name="exp-3.2.4",
    task=task,
    cluster_resources=[cloud_resource, edge_0_resource, edge_1_resource],
    hugging_face_token=os.getenv("HUGGINGFACE_TOKEN"),
)

server = exp.create_server(server_resource)
edge_0_clients = exp.create_clients(pi3_0_resource, edge_0_resource.num_devices)
edge_1_clients = exp.create_clients(pi3_1_resource, edge_1_resource.num_devices)

cloud = exp.create_cluster(cloud_resource)
edge_0 = exp.create_cluster(edge_0_resource)
edge_1 = exp.create_cluster(edge_1_resource)

exp.add_to_cluster(server, cloud)

for client in edge_0_clients:
    exp.add_to_cluster(client, edge_0)
for client in edge_1_clients:
    exp.add_to_cluster(client, edge_1)

worker = exp.register_remote_worker("127.0.0.1")
worker.add_cluster(cloud)
worker.add_cluster(edge_0)
worker.add_cluster(edge_1)
worker.create_cluster_link(cloud, edge_0)
worker.create_cluster_link(cloud, edge_1)

try:
    exp.start()
except Exception as ex:
    print(ex)
finally:
    exp.stop()

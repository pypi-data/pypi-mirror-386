from kubernetes import client
from adam.utils import log2

class ConfigMapMount:
    def __init__(self, config_map_name: str, sub_path: str, mount_path: str):
        self.config_map_name = config_map_name
        self.sub_path = sub_path
        self.mount_path = mount_path

    def name(self) -> str:
        return f"{self.config_map_name}-volume"

# utility collection on volumes; methods are all static
class Volumes:
    def create_pvc(name: str, storage: int, namespace: str):
        v1 = client.CoreV1Api()
        pvc = client.V1PersistentVolumeClaim(
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1PersistentVolumeClaimSpec(
                access_modes=["ReadWriteOnce"],
                resources=client.V1ResourceRequirements(
                    requests={"storage": str(storage)+"Gi"}
                ))
        )
        try:
            v1.create_namespaced_persistent_volume_claim(namespace=namespace, body=pvc)
        except Exception as e:
            if e.status == 409:
                log2("PVC already exists, continue...")
            else:
                raise
        return
import pulumi
import pulumi_yandex as yandex

cfg = pulumi.Config()

project_name = cfg.get("projectName") or "lab04"
zone = cfg.get("zone") or "ru-central1-d"
subnet_cidr = cfg.get("subnetCidr") or "10.10.0.0/24"
image_family = cfg.get("imageFamily") or "ubuntu-2404-lts"
ssh_user = cfg.get("sshUser") or "ubuntu"
my_ip_cidr = cfg.require("myIpCidr")
ssh_public_key_path = cfg.require("sshPublicKeyPath")

with open(ssh_public_key_path, "r", encoding="utf-8") as f:
    ssh_public_key = f.read().strip()

image = yandex.get_compute_image(family=image_family)

network = yandex.VpcNetwork(
    f"{project_name}-network",
    name=f"{project_name}-network",
)

subnet = yandex.VpcSubnet(
    f"{project_name}-subnet",
    name=f"{project_name}-subnet",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=[subnet_cidr],
)

security_group = yandex.VpcSecurityGroup(
    f"{project_name}-sg",
    name=f"{project_name}-sg",
    network_id=network.id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            description="SSH from my IP",
            protocol="TCP",
            port=22,
            v4_cidr_blocks=[my_ip_cidr],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="HTTP",
            protocol="TCP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="App port",
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            description="Allow all egress",
            protocol="ANY",
            from_port=0,
            to_port=65535,
            v4_cidr_blocks=["0.0.0.0/0"],
        )
    ],
)

vm = yandex.ComputeInstance(
    f"{project_name}-vm",
    name=f"{project_name}-vm",
    zone=zone,
    platform_id="standard-v2",
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image.image_id,
            size=10,
            type="network-hdd",
        ),
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[security_group.id],
        )
    ],
    metadata={
        "ssh-keys": f"{ssh_user}:{ssh_public_key}",
    },
)

pulumi.export("vmPublicIp", vm.network_interfaces[0].nat_ip_address)
pulumi.export("sshCommand", pulumi.Output.format("ssh -i ~/.ssh/devops45labs {0}@{1}", ssh_user, vm.network_interfaces[0].nat_ip_address))

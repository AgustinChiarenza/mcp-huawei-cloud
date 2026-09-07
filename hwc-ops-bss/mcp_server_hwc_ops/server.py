import json
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Huawei Cloud SDK - Core
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.region.region import Region

# Huawei Cloud SDK - ECS
from huaweicloudsdkecs.v2.region.ecs_region import EcsRegion
from huaweicloudsdkecs.v2.ecs_client import EcsClient
from huaweicloudsdkecs.v2.model.list_servers_details_request import ListServersDetailsRequest
from huaweicloudsdkecs.v2.model.show_server_request import ShowServerRequest
from huaweicloudsdkecs.v2.model.batch_start_servers_request import BatchStartServersRequest
from huaweicloudsdkecs.v2.model.batch_start_servers_request_body import BatchStartServersRequestBody
from huaweicloudsdkecs.v2.model.batch_start_servers_option import BatchStartServersOption
from huaweicloudsdkecs.v2.model.batch_stop_servers_request import BatchStopServersRequest
from huaweicloudsdkecs.v2.model.batch_stop_servers_request_body import BatchStopServersRequestBody
from huaweicloudsdkecs.v2.model.batch_stop_servers_option import BatchStopServersOption
from huaweicloudsdkecs.v2.model.batch_reboot_servers_request import BatchRebootServersRequest
from huaweicloudsdkecs.v2.model.batch_reboot_servers_request_body import BatchRebootServersRequestBody
from huaweicloudsdkecs.v2.model.batch_reboot_severs_option import BatchRebootSeversOption
from huaweicloudsdkecs.v2.model.create_servers_request import CreateServersRequest
from huaweicloudsdkecs.v2.model.create_servers_request_body import CreateServersRequestBody
from huaweicloudsdkecs.v2.model.delete_servers_request import DeleteServersRequest
from huaweicloudsdkecs.v2.model.delete_servers_request_body import DeleteServersRequestBody
from huaweicloudsdkecs.v2.model.list_flavors_request import ListFlavorsRequest
from huaweicloudsdkecs.v2.model.update_server_request import UpdateServerRequest
from huaweicloudsdkecs.v2.model.update_server_option import UpdateServerOption
from huaweicloudsdkecs.v2.model.attach_server_volume_request import AttachServerVolumeRequest
from huaweicloudsdkecs.v2.model.attach_server_volume_option import AttachServerVolumeOption

# Huawei Cloud SDK - VPC
from huaweicloudsdkvpc.v2.region.vpc_region import VpcRegion
from huaweicloudsdkvpc.v2.vpc_client import VpcClient
from huaweicloudsdkvpc.v2.model.list_vpcs_request import ListVpcsRequest
from huaweicloudsdkvpc.v2.model.list_subnets_request import ListSubnetsRequest
from huaweicloudsdkvpc.v2.model.create_vpc_request import CreateVpcRequest
from huaweicloudsdkvpc.v2.model.create_vpc_option import CreateVpcOption
from huaweicloudsdkvpc.v2.model.delete_vpc_request import DeleteVpcRequest
from huaweicloudsdkvpc.v2.model.create_subnet_request import CreateSubnetRequest
from huaweicloudsdkvpc.v2.model.create_subnet_option import CreateSubnetOption
from huaweicloudsdkvpc.v2.model.delete_subnet_request import DeleteSubnetRequest
from huaweicloudsdkvpc.v2.model.list_security_groups_request import ListSecurityGroupsRequest
from huaweicloudsdkvpc.v2.model.create_security_group_request import CreateSecurityGroupRequest
from huaweicloudsdkvpc.v2.model.create_security_group_option import CreateSecurityGroupOption

# Huawei Cloud SDK - CBR
from huaweicloudsdkcbr.v1.region.cbr_region import CbrRegion
from huaweicloudsdkcbr.v1.cbr_client import CbrClient
from huaweicloudsdkcbr.v1.model.list_vault_request import ListVaultRequest
from huaweicloudsdkcbr.v1.model.list_backups_request import ListBackupsRequest

# Huawei Cloud SDK - CES
from huaweicloudsdkces.v1.region.ces_region import CesRegion
from huaweicloudsdkces.v1.ces_client import CesClient
from huaweicloudsdkces.v1.model.list_alarms_request import ListAlarmsRequest

# Huawei Cloud SDK - CTS
from huaweicloudsdkcts.v3.region.cts_region import CtsRegion
from huaweicloudsdkcts.v3.cts_client import CtsClient
from huaweicloudsdkcts.v3.model.list_traces_request import ListTracesRequest

# Huawei Cloud SDK - IAM
from huaweicloudsdkiam.v3.region.iam_region import IamRegion
from huaweicloudsdkiam.v3.iam_client import IamClient
from huaweicloudsdkiam.v3.model.keystone_list_projects_request import KeystoneListProjectsRequest

# Huawei Cloud SDK - LTS
from huaweicloudsdklts.v2.region.lts_region import LtsRegion
from huaweicloudsdklts.v2.lts_client import LtsClient
from huaweicloudsdklts.v2.model.list_log_groups_request import ListLogGroupsRequest


# ---------------------------------------------------------------------------
# Credentials helpers
# ---------------------------------------------------------------------------

def _get_credentials():
    """Read AK/SK from environment variables."""
    ak = os.environ.get("HUAWEI_ACCESS_KEY") or os.environ.get("HUAWEICLOUD_SDK_AK", "")
    sk = os.environ.get("HUAWEI_SECRET_KEY") or os.environ.get("HUAWEICLOUD_SDK_SK", "")
    if not ak or not sk:
        raise ValueError(
            "Missing Huawei Cloud credentials. Set HUAWEI_ACCESS_KEY (or HUAWEICLOUD_SDK_AK) "
            "and HUAWEI_SECRET_KEY (or HUAWEICLOUD_SDK_SK) environment variables."
        )
    return ak, sk


def _get_project_id(region: str) -> str:
    return os.environ.get("HUAWEI_PROJECT_ID", "")


def _build_credentials(region: str) -> BasicCredentials:
    ak, sk = _get_credentials()
    credentials = BasicCredentials(ak, sk)
    project_id = _get_project_id(region)
    if project_id:
        credentials.with_project_id(project_id)
    return credentials


# ---------------------------------------------------------------------------
# Client builders
# ---------------------------------------------------------------------------

def _ecs_client(region: str) -> EcsClient:
    credentials = _build_credentials(region)
    return EcsClient.new_builder().with_credentials(credentials).with_region(EcsRegion.value_of(region)).build()


def _vpc_client(region: str) -> VpcClient:
    credentials = _build_credentials(region)
    return VpcClient.new_builder().with_credentials(credentials).with_region(VpcRegion.value_of(region)).build()


def _cbr_client(region: str) -> CbrClient:
    credentials = _build_credentials(region)
    return CbrClient.new_builder().with_credentials(credentials).with_region(CbrRegion.value_of(region)).build()


def _ces_client(region: str) -> CesClient:
    credentials = _build_credentials(region)
    return CesClient.new_builder().with_credentials(credentials).with_region(CesRegion.value_of(region)).build()


def _cts_client(region: str) -> CtsClient:
    credentials = _build_credentials(region)
    return CtsClient.new_builder().with_credentials(credentials).with_region(CtsRegion.value_of(region)).build()


def _iam_client(region: str) -> IamClient:
    credentials = _build_credentials(region)
    return IamClient.new_builder().with_credentials(credentials).with_region(IamRegion.value_of(region)).build()


def _lts_client(region: str) -> LtsClient:
    credentials = _build_credentials(region)
    return LtsClient.new_builder().with_credentials(credentials).with_region(LtsRegion.value_of(region)).build()


def _ims_client(region: str):
    from huaweicloudsdkims.v2.region.ims_region import ImsRegion
    from huaweicloudsdkims.v2.ims_client import ImsClient
    credentials = _build_credentials(region)
    return ImsClient.new_builder().with_credentials(credentials).with_region(ImsRegion.value_of(region)).build()


def _eip_client(region: str):
    from huaweicloudsdkeip.v2.region.eip_region import EipRegion
    from huaweicloudsdkeip.v2.eip_client import EipClient
    credentials = _build_credentials(region)
    return EipClient.new_builder().with_credentials(credentials).with_region(EipRegion.value_of(region)).build()


def _evs_client(region: str):
    from huaweicloudsdkevs.v2.region.evs_region import EvsRegion
    from huaweicloudsdkevs.v2.evs_client import EvsClient
    credentials = _build_credentials(region)
    return EvsClient.new_builder().with_credentials(credentials).with_region(EvsRegion.value_of(region)).build()


def _elb_client(region: str):
    from huaweicloudsdkelb.v3.region.elb_region import ElbRegion
    from huaweicloudsdkelb.v3.elb_client import ElbClient
    credentials = _build_credentials(region)
    return ElbClient.new_builder().with_credentials(credentials).with_region(ElbRegion.value_of(region)).build()


def _dns_client(region: str):
    from huaweicloudsdkdns.v2.region.dns_region import DnsRegion
    from huaweicloudsdkdns.v2.dns_client import DnsClient
    credentials = _build_credentials(region)
    return DnsClient.new_builder().with_credentials(credentials).with_region(DnsRegion.value_of(region)).build()


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def _serialize(obj) -> str:
    """Convert SDK response object to JSON string."""
    if obj is None:
        return json.dumps({})
    if hasattr(obj, "to_dict"):
        return json.dumps(obj.to_dict(), indent=2, ensure_ascii=False, default=str)
    if isinstance(obj, (list, dict)):
        return json.dumps(obj, indent=2, ensure_ascii=False, default=str)
    return json.dumps(str(obj), indent=2, ensure_ascii=False)


def _extract_server_fields(server) -> dict:
    """Extract only useful fields from an ECS server object."""
    d = server.to_dict() if hasattr(server, "to_dict") else {}
    return {
        "id": d.get("id"),
        "name": d.get("name"),
        "status": d.get("status"),
        "flavor": d.get("flavor", {}).get("id") if isinstance(d.get("flavor"), dict) else d.get("flavor"),
        "vpc_id": d.get("metadata", {}).get("vpc_id") if isinstance(d.get("metadata"), dict) else None,
        "addresses": d.get("addresses"),
        "created": d.get("created"),
        "availability_zone": d.get("availability_zone"),
    }


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP("hwc-mcp-server-ops")


# ====================
# ECS - Compute
# ====================

@mcp.tool()
def ecs_list_servers(region: str = "la-south-2", limit: Optional[int] = None) -> str:
    """List ECS instances in a given region. Returns id, name, status, flavor, vpc_id, addresses, created, availability_zone."""
    client = _ecs_client(region)
    request = ListServersDetailsRequest()
    if limit:
        request.limit = limit
    response = client.list_servers_details(request)
    servers = response.servers if response and response.servers else []
    result = [_extract_server_fields(s) for s in servers]
    return json.dumps(result, indent=2, ensure_ascii=False, default=str)


@mcp.tool()
def ecs_show_server(region: str, server_id: str) -> str:
    """Show details of one ECS instance."""
    client = _ecs_client(region)
    request = ShowServerRequest(server_id=server_id)
    response = client.show_server(request)
    if response and response.server:
        return _serialize(response.server)
    return json.dumps({})


@mcp.tool()
def ecs_batch_start_servers(region: str, server_ids: str) -> str:
    """Start (power on) one or more ECS instances. server_ids is a comma-separated list of server UUIDs."""
    client = _ecs_client(region)
    ids = [s.strip() for s in server_ids.split(",") if s.strip()]
    os_start = BatchStartServersOption(servers=[{"id": sid} for sid in ids])
    body = BatchStartServersRequestBody(os_start=os_start)
    request = BatchStartServersRequest(body=body)
    response = client.batch_start_servers(request)
    return _serialize(response)


@mcp.tool()
def ecs_batch_stop_servers(region: str, server_ids: str, force: Optional[bool] = False) -> str:
    """Stop (power off) one or more ECS instances. server_ids is comma-separated. Set force=True for forced (HARD) shutdown."""
    client = _ecs_client(region)
    ids = [s.strip() for s in server_ids.split(",") if s.strip()]
    os_stop = BatchStopServersOption(servers=[{"id": sid} for sid in ids])
    if force:
        os_stop.type = "HARD"
    body = BatchStopServersRequestBody(os_stop=os_stop)
    request = BatchStopServersRequest(body=body)
    response = client.batch_stop_servers(request)
    return _serialize(response)


@mcp.tool()
def ecs_batch_reboot_servers(region: str, server_ids: str, force: Optional[bool] = False) -> str:
    """Reboot one or more ECS instances. server_ids is comma-separated. Set force=True for forced (HARD) reboot."""
    client = _ecs_client(region)
    ids = [s.strip() for s in server_ids.split(",") if s.strip()]
    reboot = BatchRebootSeversOption(servers=[{"id": sid} for sid in ids])
    if force:
        reboot.type = "HARD"
    body = BatchRebootServersRequestBody(reboot=reboot)
    request = BatchRebootServersRequest(body=body)
    response = client.batch_reboot_servers(request)
    return _serialize(response)


@mcp.tool()
def ecs_create_server(
    region: str,
    name: str,
    image_id: str,
    flavor_id: str,
    vpc_id: str,
    subnet_id: str,
    security_group_id: Optional[str] = None,
    admin_pass: Optional[str] = None,
    key_name: Optional[str] = None,
    availability_zone: Optional[str] = None,
    count: Optional[int] = 1,
    eip_id: Optional[str] = None,
) -> str:
    """Create one or more ECS instances in a VPC. Requires name, image_id, flavor_id, vpc_id, subnet_id. Optionally specify security_group_id, admin_pass, key_name, availability_zone, count, eip_id."""
    from huaweicloudsdkecs.v2 import (
        PrePaidServer,
        PrePaidServerNic,
        PrePaidServerRootVolume,
        PrePaidServerSecurityGroup,
        PrePaidServerEip,
        PrePaidServerEipBandwidth,
    )
    client = _ecs_client(region)
    nics = [PrePaidServerNic(subnet_id=subnet_id)]
    root_volume = PrePaidServerRootVolume(volumetype="SAS", size=40)
    server = PrePaidServer(
        name=name,
        image_ref=image_id,
        flavor_ref=flavor_id,
        vpcid=vpc_id,
        nics=nics,
        root_volume=root_volume,
    )
    if admin_pass:
        server.admin_pass = admin_pass
    if key_name:
        server.key_name = key_name
    if availability_zone:
        server.availability_zone = availability_zone
    if count and count > 1:
        server.count = count
    if security_group_id:
        server.security_groups = [PrePaidServerSecurityGroup(id=security_group_id)]
    if eip_id:
        server.eip = PrePaidServerEip(iptype="5_bgp", bandwidth=PrePaidServerEipBandwidth(size=5, sharetype="PER"))
    body = CreateServersRequestBody(server=server)
    request = CreateServersRequest(body=body)
    response = client.create_servers(request)
    return _serialize(response)


@mcp.tool()
def ecs_delete_server(region: str, server_id: str, delete_public_ip: Optional[bool] = False, delete_volume: Optional[bool] = False) -> str:
    """Delete an ECS instance. Set delete_public_ip=True to also delete associated EIP. Set delete_volume=True to also delete attached volumes."""
    client = _ecs_client(region)
    body = DeleteServersRequestBody(
        servers=[{"id": server_id}],
        delete_publicip=delete_public_ip,
        delete_volume=delete_volume,
    )
    request = DeleteServersRequest(body=body)
    response = client.delete_servers(request)
    return _serialize(response)


@mcp.tool()
def ecs_list_flavors(region: str = "la-south-2", availability_zone: Optional[str] = None) -> str:
    """List available ECS flavors (instance types) in a region. Returns id, name, vcpus, ram, disk."""
    client = _ecs_client(region)
    request = ListFlavorsRequest()
    if availability_zone:
        request.availability_zone = availability_zone
    response = client.list_flavors(request)
    flavors = response.flavors if response and response.flavors else []
    return json.dumps(
        [{"id": f.to_dict().get("id"), "name": f.to_dict().get("name"), "vcpus": f.to_dict().get("vcpus"), "ram": f.to_dict().get("ram"), "disk": f.to_dict().get("disk")} for f in flavors],
        indent=2, ensure_ascii=False, default=str,
    )


@mcp.tool()
def ecs_update_server(region: str, server_id: str, name: Optional[str] = None, description: Optional[str] = None) -> str:
    """Update an ECS instance. Supports renaming and updating description."""
    client = _ecs_client(region)
    body = UpdateServerOption()
    if name:
        body.name = name
    if description:
        body.description = description
    request = UpdateServerRequest(server_id=server_id, body=body)
    response = client.update_server(request)
    return _serialize(response)


# ====================
# IMS - Image Management
# ====================

@mcp.tool()
def ims_list_images(region: str = "la-south-2", image_type: Optional[str] = None, status: Optional[str] = None, limit: Optional[int] = None) -> str:
    """List IMS images. image_type: 'private'|'shared'|'market'|'gold'. status: 'active'|'queued'|'killed'. Returns id, name, status, os_type, min_disk, min_ram."""
    client = _ims_client(region)
    from huaweicloudsdkims.v2.model.list_images_request import ListImagesRequest
    request = ListImagesRequest()
    if image_type:
        request.imagetype = image_type
    if status:
        request.status = status
    if limit:
        request.limit = limit
    response = client.list_images(request)
    images = response.images if response and response.images else []
    result = []
    for img in images:
        d = img.to_dict() if hasattr(img, "to_dict") else {}
        result.append({
            "id": d.get("id"),
            "name": d.get("name"),
            "status": d.get("status"),
            "os_type": d.get("__os_type"),
            "min_disk": d.get("min_disk"),
            "min_ram": d.get("min_ram"),
        })
    return json.dumps(result, indent=2, ensure_ascii=False, default=str)


@mcp.tool()
def ims_show_image(region: str, image_id: str) -> str:
    """Show details of a specific IMS image."""
    client = _ims_client(region)
    from huaweicloudsdkims.v2.model.show_image_by_tags_resource import ShowImageByTagsResource
    from huaweicloudsdkims.v2.model.glance_show_image_request import GlanceShowImageRequest
    request = GlanceShowImageRequest(image_id=image_id)
    response = client.glance_show_image(request)
    return _serialize(response)


@mcp.tool()
def ims_create_image(region: str, name: str, instance_id: str, description: Optional[str] = None) -> str:
    """Create an IMS image from an existing ECS instance."""
    client = _ims_client(region)
    from huaweicloudsdkims.v2.model.create_image_request import CreateImageRequest
    from huaweicloudsdkims.v2.model.create_image_request_body import CreateImageRequestBody
    body = CreateImageRequestBody(name=name, instance_id=instance_id)
    if description:
        body.description = description
    request = CreateImageRequest(body=body)
    response = client.create_image(request)
    return _serialize(response)


# ====================
# VPC - Networking
# ====================

@mcp.tool()
def vpc_list_vpcs(region: str = "la-south-2") -> str:
    """List VPCs in a region."""
    client = _vpc_client(region)
    request = ListVpcsRequest()
    response = client.list_vpcs(request)
    vpcs = response.vpcs if response and response.vpcs else []
    return json.dumps([v.to_dict() for v in vpcs], indent=2, ensure_ascii=False, default=str)


@mcp.tool()
def vpc_list_subnets(region: str, vpc_id: Optional[str] = None) -> str:
    """List subnets in a region. Optionally filter by vpc_id."""
    client = _vpc_client(region)
    request = ListSubnetsRequest()
    if vpc_id:
        request.vpc_id = vpc_id
    response = client.list_subnets(request)
    subnets = response.subnets if response and response.subnets else []
    return json.dumps([s.to_dict() for s in subnets], indent=2, ensure_ascii=False, default=str)


@mcp.tool()
def vpc_create_vpc(region: str, name: str, cidr: str = "192.168.0.0/16") -> str:
    """Create a VPC with the given name and CIDR."""
    client = _vpc_client(region)
    body = CreateVpcOption(name=name, cidr=cidr)
    request = CreateVpcRequest(body=body)
    response = client.create_vpc(request)
    if response and response.vpc:
        return _serialize(response.vpc)
    return _serialize(response)


@mcp.tool()
def vpc_delete_vpc(region: str, vpc_id: str) -> str:
    """Delete a VPC by ID."""
    client = _vpc_client(region)
    request = DeleteVpcRequest(vpc_id=vpc_id)
    response = client.delete_vpc(request)
    return _serialize(response)


@mcp.tool()
def vpc_create_subnet(region: str, vpc_id: str, name: str, cidr: str, gateway_ip: str) -> str:
    """Create a subnet in a VPC. Requires vpc_id, name, cidr (e.g. 192.168.0.0/24), gateway_ip."""
    client = _vpc_client(region)
    body = CreateSubnetOption(name=name, cidr=cidr, gateway_ip=gateway_ip, vpc_id=vpc_id)
    request = CreateSubnetRequest(body=body)
    response = client.create_subnet(request)
    if response and response.subnet:
        return _serialize(response.subnet)
    return _serialize(response)


@mcp.tool()
def vpc_delete_subnet(region: str, vpc_id: str, subnet_id: str) -> str:
    """Delete a subnet by ID (requires vpc_id too)."""
    client = _vpc_client(region)
    request = DeleteSubnetRequest(vpc_id=vpc_id, subnet_id=subnet_id)
    response = client.delete_subnet(request)
    return _serialize(response)


@mcp.tool()
def vpc_list_security_groups(region: str = "la-south-2", limit: Optional[int] = None) -> str:
    """List security groups in a region."""
    client = _vpc_client(region)
    request = ListSecurityGroupsRequest()
    if limit:
        request.limit = limit
    response = client.list_security_groups(request)
    sgs = response.security_groups if response and response.security_groups else []
    return json.dumps([sg.to_dict() for sg in sgs], indent=2, ensure_ascii=False, default=str)


@mcp.tool()
def vpc_create_security_group(region: str, name: str, vpc_id: Optional[str] = None) -> str:
    """Create a security group. Optionally bind to a VPC."""
    client = _vpc_client(region)
    body = CreateSecurityGroupOption(name=name)
    if vpc_id:
        body.vpc_id = vpc_id
    request = CreateSecurityGroupRequest(body=body)
    response = client.create_security_group(request)
    if response and response.security_group:
        return _serialize(response.security_group)
    return _serialize(response)


# ====================
# EIP - Elastic IP
# ====================

@mcp.tool()
def eip_list_public_ips(region: str = "la-south-2") -> str:
    """List Elastic IP addresses in a region."""
    client = _eip_client(region)
    from huaweicloudsdkeip.v2.model.list_publicips_request import ListPublicipsRequest
    request = ListPublicipsRequest()
    response = client.list_publicips(request)
    publicips = response.publicips if response and response.publicips else []
    return json.dumps([p.to_dict() for p in publicips], indent=2, ensure_ascii=False, default=str)


@mcp.tool()
def eip_create_public_ip(region: str = "la-south-2") -> str:
    """Create a new Elastic IP address."""
    client = _eip_client(region)
    from huaweicloudsdkeip.v2.model.create_publicip_request import CreatePublicipRequest
    from huaweicloudsdkeip.v2.model.create_publicip_request_body import CreatePublicipRequestBody
    from huaweicloudsdkeip.v2.model.create_publicip_option import CreatePublicipOption
    body = CreatePublicipRequestBody(publicip=CreatePublicipOption())
    request = CreatePublicipRequest(body=body)
    response = client.create_publicip(request)
    if response and response.publicip:
        return _serialize(response.publicip)
    return _serialize(response)


@mcp.tool()
def eip_bind_public_ip(region: str, publicip_id: str, port_id: str) -> str:
    """Bind an EIP to a port (network interface). Use the port_id of the ECS NIC."""
    client = _eip_client(region)
    from huaweicloudsdkeip.v2.model.update_publicip_request import UpdatePublicipRequest
    from huaweicloudsdkeip.v2.model.update_publicips_request_body import UpdatePublicipsRequestBody
    from huaweicloudsdkeip.v2.model.update_publicip_option import UpdatePublicipOption
    body = UpdatePublicipsRequestBody(publicip=UpdatePublicipOption(port_id=port_id))
    request = UpdatePublicipRequest(publicip_id=publicip_id, body=body)
    response = client.update_publicip(request)
    if response and response.publicip:
        return _serialize(response.publicip)
    return _serialize(response)


# ====================
# EVS - Elastic Volume Service
# ====================

@mcp.tool()
def evs_list_volumes(region: str = "la-south-2", availability_zone: Optional[str] = None) -> str:
    """List EVS volumes (disks) in a region."""
    client = _evs_client(region)
    from huaweicloudsdkevs.v2.model.list_volumes_request import ListVolumesRequest
    request = ListVolumesRequest()
    if availability_zone:
        request.availability_zone = availability_zone
    response = client.list_volumes(request)
    volumes = response.volumes if response and response.volumes else []
    return json.dumps([v.to_dict() for v in volumes], indent=2, ensure_ascii=False, default=str)


@mcp.tool()
def evs_create_volume(region: str, name: str, size: int, availability_zone: str, volume_type: str = "SSD") -> str:
    """Create an EVS volume. size in GB. volume_type: SSD|SAS|SATA|GPSSD|ESSD. availability_zone required."""
    client = _evs_client(region)
    from huaweicloudsdkevs.v2.model.create_volume_request import CreateVolumeRequest
    from huaweicloudsdkevs.v2.model.create_volume_request_body import CreateVolumeRequestBody
    from huaweicloudsdkevs.v2.model.create_volume_option import CreateVolumeOption
    body = CreateVolumeRequestBody(volume=CreateVolumeOption(name=name, size=size, availability_zone=availability_zone, volume_type=volume_type))
    request = CreateVolumeRequest(body=body)
    response = client.create_volume(request)
    return _serialize(response)


@mcp.tool()
def evs_delete_volume(region: str, volume_id: str) -> str:
    """Delete an EVS volume by ID."""
    client = _evs_client(region)
    from huaweicloudsdkevs.v2.model.delete_volume_request import DeleteVolumeRequest
    request = DeleteVolumeRequest(volume_id=volume_id)
    response = client.delete_volume(request)
    return _serialize(response)


@mcp.tool()
def evs_attach_volume(region: str, server_id: str, volume_id: str, device: Optional[str] = None) -> str:
    """Attach an EVS volume to an ECS instance. device is optional mount point (e.g. /dev/sdb)."""
    client = _ecs_client(region)
    body = AttachServerVolumeOption(volume_id=volume_id)
    if device:
        body.device = device
    request = AttachServerVolumeRequest(server_id=server_id, body=body)
    response = client.attach_server_volume(request)
    return _serialize(response)


# ====================
# ELB - Elastic Load Balance
# ====================

@mcp.tool()
def elb_list_loadbalancers(region: str = "la-south-2") -> str:
    """List Elastic Load Balancers in a region."""
    client = _elb_client(region)
    from huaweicloudsdkelb.v3.model.list_load_balancers_request import ListLoadBalancersRequest
    request = ListLoadBalancersRequest()
    response = client.list_load_balancers(request)
    lbs = response.loadbalancers if response and response.loadbalancers else []
    return json.dumps([lb.to_dict() for lb in lbs], indent=2, ensure_ascii=False, default=str)


@mcp.tool()
def elb_list_listeners(region: str, loadbalancer_id: str) -> str:
    """List listeners of a specific load balancer."""
    client = _elb_client(region)
    from huaweicloudsdkelb.v3.model.list_listeners_request import ListListenersRequest
    request = ListListenersRequest(loadbalancer_id=loadbalancer_id)
    response = client.list_listeners(request)
    listeners = response.listeners if response and response.listeners else []
    return json.dumps([l.to_dict() for l in listeners], indent=2, ensure_ascii=False, default=str)


# ====================
# DNS
# ====================

@mcp.tool()
def dns_list_zones(region: str = "la-south-2", zone_type: Optional[str] = None) -> str:
    """List DNS zones. zone_type: 'public'|'private'. If not specified, lists public zones."""
    client = _dns_client(region)
    if zone_type == "private":
        from huaweicloudsdkdns.v2.model.list_private_zones_request import ListPrivateZonesRequest
        request = ListPrivateZonesRequest()
        response = client.list_private_zones(request)
        zones = response.zones if response and response.zones else []
    else:
        from huaweicloudsdkdns.v2.model.list_public_zones_request import ListPublicZonesRequest
        request = ListPublicZonesRequest()
        response = client.list_public_zones(request)
        zones = response.zones if response and response.zones else []
    return json.dumps([z.to_dict() for z in zones], indent=2, ensure_ascii=False, default=str)


@mcp.tool()
def dns_list_recordsets(region: str, zone_id: str) -> str:
    """List record sets in a DNS zone."""
    client = _dns_client(region)
    from huaweicloudsdkdns.v2.model.list_record_sets_by_zone_request import ListRecordSetsByZoneRequest
    request = ListRecordSetsByZoneRequest(zone_id=zone_id)
    response = client.list_record_sets_by_zone(request)
    recordsets = response.recordsets if response and response.recordsets else []
    return json.dumps([r.to_dict() for r in recordsets], indent=2, ensure_ascii=False, default=str)


# ====================
# OBS - Object Storage
# ====================

@mcp.tool()
def obs_list_buckets(region: Optional[str] = None) -> str:
    """List OBS buckets. Uses the OBS REST API via esdk. Returns bucket name, location, creation_date."""
    ak, sk = _get_credentials()
    try:
        from obs import ObsClient
    except ImportError:
        try:
            from esdk_obs_python.obs import ObsClient
        except ImportError:
            return json.dumps({"error": "OBS SDK not installed. Install esdk-obs-python or obs-sdk."})

    obs_region = region or "la-south-2"
    server = f"obs.{obs_region}.myhuaweicloud.com"
    obs_client = ObsClient(access_key_id=ak, secret_access_key=sk, server=server)

    try:
        resp = obs_client.listBuckets()
        if resp.status >= 300:
            return json.dumps({"error": resp.reason, "status": resp.status})

        buckets = []
        for bucket in resp.body.buckets if resp.body and resp.body.buckets else []:
            buckets.append({
                "name": bucket.name,
                "location": bucket.location,
                "create_date": bucket.create_date,
            })
        return json.dumps(buckets, indent=2, ensure_ascii=False, default=str)
    finally:
        obs_client.close()


# ====================
# CBR - Cloud Backup and Recovery
# ====================

@mcp.tool()
def cbr_list_vaults(region: str = "la-south-2") -> str:
    """List CBR backup vaults in a region."""
    client = _cbr_client(region)
    request = ListVaultRequest()
    response = client.list_vault(request)
    vaults = response.vaults if response and response.vaults else []
    return json.dumps([v.to_dict() for v in vaults], indent=2, ensure_ascii=False, default=str)


@mcp.tool()
def cbr_list_backups(region: str, vault_id: Optional[str] = None) -> str:
    """List CBR backups in a region. Optionally filter by vault_id."""
    client = _cbr_client(region)
    request = ListBackupsRequest()
    if vault_id:
        request.vault_id = [vault_id]
    response = client.list_backups(request)
    backups = response.backups if response and response.backups else []
    return json.dumps([b.to_dict() for b in backups], indent=2, ensure_ascii=False, default=str)


# ====================
# CES - Cloud Eye (Monitoring)
# ====================

@mcp.tool()
def ces_list_alarms(region: str = "la-south-2") -> str:
    """List Cloud Eye / CES alarms in a region."""
    client = _ces_client(region)
    request = ListAlarmsRequest()
    response = client.list_alarms(request)
    alarms = response.alarms if response and response.alarms else []
    return json.dumps([a.to_dict() for a in alarms], indent=2, ensure_ascii=False, default=str)


# ====================
# CTS - Cloud Trace (Audit)
# ====================

@mcp.tool()
def cts_list_traces(
    region: str = "la-south-2",
    limit: Optional[int] = None,
    resource_type: Optional[str] = None,
    user: Optional[str] = None,
) -> str:
    """List recent CTS traces/events in a region."""
    client = _cts_client(region)
    request = ListTracesRequest()
    if limit:
        request.limit = limit
    if resource_type:
        request.resource_type = resource_type
    if user:
        request.user = user
    response = client.list_traces(request)
    traces = response.traces if response and response.traces else []
    return json.dumps([t.to_dict() for t in traces], indent=2, ensure_ascii=False, default=str)


# ====================
# LTS - Log Tank Service
# ====================

@mcp.tool()
def lts_list_log_groups(region: str = "la-south-2") -> str:
    """List LTS log groups in a region."""
    client = _lts_client(region)
    request = ListLogGroupsRequest()
    response = client.list_log_groups(request)
    groups = response.log_groups if response and response.log_groups else []
    return json.dumps([g.to_dict() for g in groups], indent=2, ensure_ascii=False, default=str)


# ====================
# IAM - Identity and Access Management
# ====================

@mcp.tool()
def iam_get_current_user_or_projects(region: str = "la-south-2") -> str:
    """Return basic IAM/project information available from the configured credentials. Does not expose secrets."""
    client = _iam_client(region)
    result = {}

    try:
        request = KeystoneListProjectsRequest()
        response = client.keystone_list_projects(request)
        projects = response.projects if response and response.projects else []
        result["projects"] = [
            {
                "id": p.to_dict().get("id"),
                "name": p.to_dict().get("name"),
                "enabled": p.to_dict().get("enabled"),
            }
            for p in projects
        ]
    except Exception as e:
        result["projects_error"] = str(e)

    return json.dumps(result, indent=2, ensure_ascii=False, default=str)

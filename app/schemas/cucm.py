# app/schemas/cucm.py

from typing import List, Optional
from pydantic import BaseModel, Field


# =========================
# Core CUCM Entities
# =========================

class CUCMDevice(BaseModel):
    """Phone / gateway / trunk device-level view."""
    name: str = Field(..., example="SEP001122334455")
    description: Optional[str] = Field(None, example="Lobby Phone")
    product: Optional[str] = Field(None, example="Cisco 8851")
    model: Optional[str] = Field(None, example="Cisco 8851")
    protocol: Optional[str] = Field(None, example="SIP")
    device_type: Optional[str] = Field(
        None,
        example="Phone",  # Phone | Gateway | Trunk | CTI Port | Route List, etc.
    )
    device_pool: Optional[str] = Field(None, example="DP_Building1")
    location: Optional[str] = Field(None, example="HQ")
    css: Optional[str] = Field(None, example="CSS_Internal_External")
    owner_user_id: Optional[str] = Field(None, example="jdoe")
    presence_group: Optional[str] = Field(None, example="Standard Presence group")
    status: Optional[str] = Field(
        None,
        example="Registered",  # Registered | Unregistered | Rejected | Unknown
    )
    ip_address: Optional[str] = Field(None, example="10.10.10.50")
    mac_address: Optional[str] = Field(None, example="001122334455")
    firmware_load: Optional[str] = Field(None, example="sip88xx.12-5-1SR1-4")
    last_registration_time: Optional[str] = Field(
        None, example="2025-11-25T13:22:11Z"
    )


class CUCMLine(BaseModel):
    """Directory number / line appearance."""
    pattern: str = Field(..., example="1001")
    route_partition: Optional[str] = Field(None, example="PT_Internal")
    description: Optional[str] = Field(None, example="John Doe Desk")
    alerting_name: Optional[str] = Field(None, example="John Doe")
    ascii_alerting_name: Optional[str] = Field(None, example="John Doe")
    external_phone_number_mask: Optional[str] = Field(None, example="+15555551001")
    share_line_css: Optional[str] = Field(None, example="CSS_Internal_Only")
    call_forward_all_destination: Optional[str] = Field(None, example="2000")
    call_forward_busy_destination: Optional[str] = Field(None, example="Voicemail")
    call_forward_no_answer_destination: Optional[str] = Field(
        None, example="Voicemail"
    )
    voice_mail_profile: Optional[str] = Field(None, example="Standard Voicemail")
    associated_devices: List[str] = Field(
        default_factory=list, example=["SEP001122334455", "CSFJDOE"]
    )


class CUCMUser(BaseModel):
    """End user / application user view."""
    userid: str = Field(..., example="jdoe")
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    display_name: Optional[str] = Field(None, example="John Doe")
    telephone_number: Optional[str] = Field(None, example="+1 555 555 1001")
    mail_id: Optional[str] = Field(None, example="jdoe@example.com")
    department: Optional[str] = Field(None, example="IT")
    manager: Optional[str] = Field(None, example="asmith")
    primary_extension: Optional[str] = Field(None, example="1001")
    associated_devices: List[str] = Field(
        default_factory=list, example=["SEP001122334455", "CSFJDOE"]
    )
    associated_lines: List[str] = Field(
        default_factory=list, example=["1001", "2001"]
    )
    home_cluster: Optional[bool] = Field(None, example=True)
    enable_im_and_presence: Optional[bool] = Field(None, example=True)
    enable_mobility: Optional[bool] = Field(None, example=False)
    enable_emcc: Optional[bool] = Field(None, example=False)


# =========================
# Trunks / Gateways
# =========================

class CUCMSipTrunk(BaseModel):
    """SIP trunk configuration."""
    name: str = Field(..., example="SIP_ITSP_PRIMARY")
    description: Optional[str] = Field(None, example="Primary ITSP SIP trunk")
    device_pool: Optional[str] = Field(None, example="DP_HQ")
    location: Optional[str] = Field(None, example="HQ")
    css: Optional[str] = Field(None, example="CSS_PSTN_Allowed")
    sip_profile: Optional[str] = Field(None, example="Standard SIP Profile")
    sip_security_profile: Optional[str] = Field(
        None, example="Non-Secure SIP Trunk Profile"
    )
    destination_ips: List[str] = Field(
        default_factory=list,
        example=["198.51.100.10", "198.51.100.11"],
    )
    destination_port: Optional[int] = Field(None, example=5060)
    sip_trunk_type: Optional[str] = Field(
        None,
        example="ITSP",  # ITSP | CUBE | SBC | Other CUCM cluster
    )
    presence_group: Optional[str] = Field(
        None, example="Standard Presence group"
    )
    status: Optional[str] = Field(
        None,
        example="Registered",  # or "Unknown", "Partial Service", etc.
    )


class CUCMGateway(BaseModel):
    """H.323 / MGCP / SCCP gateway, or generic voice gateway."""
    name: str = Field(..., example="VG_HQ_01")
    description: Optional[str] = Field(None, example="HQ Voice Gateway")
    device_pool: Optional[str] = Field(None, example="DP_HQ")
    location: Optional[str] = Field(None, example="HQ")
    protocol: Optional[str] = Field(None, example="MGCP")
    model: Optional[str] = Field(None, example="ISR 4331")
    product: Optional[str] = Field(None, example="Cisco ISR 4331")
    status: Optional[str] = Field(None, example="Registered")
    ip_address: Optional[str] = Field(None, example="10.10.20.5")


class CUCMTrunkSummary(BaseModel):
    """Generic trunk summary (covers SIP, H.323, MGCP, etc.)."""
    name: str = Field(..., example="SIP_ITSP_PRIMARY")
    description: Optional[str] = None
    trunk_type: Optional[str] = Field(
        None, example="SIP"  # SIP | H323 | MGCP | InterCluster
    )
    device_pool: Optional[str] = None
    location: Optional[str] = None
    css: Optional[str] = None
    status: Optional[str] = Field(
        None, example="Registered"
    )


# =========================
# Call Routing Objects
# =========================

class CUCMRoutePattern(BaseModel):
    """Route pattern (DN pattern) for call routing."""
    pattern: str = Field(..., example="9.@")
    route_partition: Optional[str] = Field(None, example="PT_PSTN")
    description: Optional[str] = Field(None, example="PSTN Route Pattern")
    route_list_name: Optional[str] = Field(None, example="RL_PSTN")
    route_group_name: Optional[str] = Field(None, example="RG_PSTN")
    block_enable: Optional[bool] = Field(None, example=False)
    discard_digits: Optional[str] = Field(None, example="PreDot")
    called_party_transformation_css: Optional[str] = Field(
        None, example="CSS_CalledParty_Transform"
    )
    calling_party_transformation_css: Optional[str] = Field(
        None, example="CSS_CallingParty_Transform"
    )


class CUCMRouteGroup(BaseModel):
    """Route group definition."""
    name: str = Field(..., example="RG_PSTN")
    description: Optional[str] = Field(None, example="Primary PSTN route group")
    distribution_algorithm: Optional[str] = Field(
        None,
        example="TopDown",  # TopDown | Circular | LongestIdleTime | etc.
    )
    members: List[str] = Field(
        default_factory=list,
        example=["SIP_ITSP_PRIMARY", "SIP_ITSP_SECONDARY"],
    )


class CUCMRouteList(BaseModel):
    """Route list, referencing one or more route groups."""
    name: str = Field(..., example="RL_PSTN")
    description: Optional[str] = Field(None, example="PSTN route list")
    route_groups: List[str] = Field(
        default_factory=list,
        example=["RG_PSTN"],
    )
    call_hunting_order: Optional[str] = Field(
        None, example="TopDown"
    )


# =========================
# Device Pools, Locations, Partitions, CSS
# =========================

class CUCMDevicePool(BaseModel):
    name: str = Field(..., example="DP_HQ")
    description: Optional[str] = Field(None, example="HQ Device Pool")
    region: Optional[str] = Field(None, example="Region_HQ")
    date_time_group: Optional[str] = Field(
        None, example="CMLocal"
    )
    cm_group: Optional[str] = Field(
        None, example="CMG_HQ"
    )
    srst_reference: Optional[str] = Field(None, example="SRST_HQ")
    location: Optional[str] = Field(None, example="HQ")


class CUCMLocation(BaseModel):
    name: str = Field(..., example="HQ")
    description: Optional[str] = Field(None, example="HQ Location")
    within_audio_bandwidth_kbps: Optional[int] = Field(
        None, example=1024
    )
    within_video_bandwidth_kbps: Optional[int] = Field(
        None, example=4096
    )
    between_audio_bandwidth_kbps: Optional[int] = Field(
        None, example=1024
    )
    between_video_bandwidth_kbps: Optional[int] = Field(
        None, example=4096
    )


class CUCMPartition(BaseModel):
    name: str = Field(..., example="PT_Internal")
    description: Optional[str] = Field(None, example="Internal DNs")


class CUCMCallingSearchSpace(BaseModel):
    name: str = Field(..., example="CSS_Internal_External")
    description: Optional[str] = Field(None, example="Internal + PSTN access")
    partitions: List[str] = Field(
        default_factory=list,
        example=["PT_Internal", "PT_PSTN"],
    )


# =========================
# Hunt / Contact Center (Optional Core Objects)
# =========================

class CUCMHuntPilot(BaseModel):
    """Basic Hunt Pilot definition."""
    pattern: str = Field(..., example="2000")
    route_partition: Optional[str] = Field(None, example="PT_Internal")
    description: Optional[str] = Field(None, example="Service Desk Hunt Pilot")
    line_css: Optional[str] = Field(None, example="CSS_Internal_Only")
    hunt_list_name: Optional[str] = Field(None, example="HL_ServiceDesk")


class CUCMHuntList(BaseModel):
    name: str = Field(..., example="HL_ServiceDesk")
    description: Optional[str] = Field(None, example="Service Desk Hunt List")
    members: List[str] = Field(
        default_factory=list,
        example=["LineGroup_ServiceDesk"],
    )


class CUCMLineGroup(BaseModel):
    name: str = Field(..., example="LineGroup_ServiceDesk")
    description: Optional[str] = Field(None, example="Service Desk Line Group")
    distribution_algorithm: Optional[str] = Field(
        None, example="Broadcast"  # TopDown | Broadcast | Circular | etc.
    )
    members: List[str] = Field(
        default_factory=list,
        example=["1001", "1002", "1003"],
    )


# =========================
# List / Collection Wrappers
# =========================

class CUCMDeviceList(BaseModel):
    items: List[CUCMDevice]
    total: int = Field(..., example=1234)


class CUCMUserList(BaseModel):
    items: List[CUCMUser]
    total: int = Field(..., example=580)


class CUCMTrunkList(BaseModel):
    items: List[CUCMTrunkSummary]
    total: int = Field(..., example=12)


class CUCMRoutePatternList(BaseModel):
    items: List[CUCMRoutePattern]
    total: int = Field(..., example=150)


class CUCMRouteListList(BaseModel):
    items: List[CUCMRouteList]
    total: int = Field(..., example=10)


class CUCMRouteGroupList(BaseModel):
    items: List[CUCMRouteGroup]
    total: int = Field(..., example=8)
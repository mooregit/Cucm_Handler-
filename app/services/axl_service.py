# app/axl/axl_service.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.axl.axl_client import AXLClient
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.device import PhoneCreate, LineCreate


# =============================================================================
# USER OPERATIONS
# =============================================================================


def get_user(axl: AXLClient, userid: str) -> Dict[str, Any]:
    """
    Wrapper for AXL getUser.
    """
    return axl.getUser(userid=userid)


def list_users(
    axl: AXLClient,
    userid_pattern: str = "%",
) -> List[Dict[str, Any]]:
    """
    Wrapper around listUser.

    Returns a list of users (basic fields) whose userid matches `userid_pattern`.
    """
    res = axl.listUser(
        searchCriteria={"userid": userid_pattern},
        returnedTags={
            "userid": "",
            "firstName": "",
            "lastName": "",
            "telephoneNumber": "",
            "mailid": "",
        },
    )

    users = []
    if res and "return" in res and res["return"]:
        users = res["return"].get("user", []) or []

    # Zeep objects are fine to return; FastAPI's jsonable_encoder can handle them.
    return users


def count_users(axl: AXLClient) -> int:
    """
    Returns total number of CUCM end users.

    Uses executeSQLQuery for efficiency instead of listing all users.
    """
    res = axl.executeSQLQuery(sql="SELECT COUNT(*) AS cnt FROM enduser")
    rows = (res.get("return") or {}).get("row", [])
    if not rows:
        return 0
    row = rows[0]
    # field name may come back as 'cnt' or 'CNT' depending on version
    for key in row:
        return int(row[key])
    return 0


def create_user(axl: AXLClient, data: UserCreate) -> Dict[str, Any]:
    """
    Wrapper for addUser.

    Builds the appropriate dictionary for the AXL SOAP request.
    """
    payload = {
        "userid": data.userid,
        "firstName": data.first_name,
        "lastName": data.last_name,
        "telephoneNumber": data.telephone_number,
        "pin": data.pin,
        "presenceGroupName": data.presence_group,
        "userLocale": data.user_locale,
        "enableMobility": data.enable_mobility,
        "homeCluster": True,
    }

    # Remove empty/None values so they don't break AXL schema
    payload = {k: v for k, v in payload.items() if v is not None}

    return axl.addUser(user=payload)


def update_user(axl: AXLClient, userid: str, data: UserUpdate) -> Dict[str, Any]:
    """
    Wrapper for updateUser.

    updateUser requires top-level identifiers + nested fields.
    """
    payload = {k: v for k, v in data.model_dump().items() if v is not None}

    if not payload:
        raise ValueError("No fields provided for update")

    return axl.updateUser(userid=userid, **payload)


def delete_user(axl: AXLClient, userid: str) -> Dict[str, Any]:
    """
    Wrapper for removeUser.
    """
    return axl.removeUser(userid=userid)


# =============================================================================
# PHONE / DEVICE OPERATIONS
# =============================================================================


def get_phone(axl: AXLClient, name: str) -> Dict[str, Any]:
    """
    Wrapper for getPhone.
    """
    return axl.getPhone(name=name)


def list_phones(
    axl: AXLClient,
    name_pattern: str = "%",
) -> List[Dict[str, Any]]:
    """
    Wrapper around listPhone.

    Returns a list of phones (basic fields) whose device name matches `name_pattern`.
    """
    res = axl.listPhone(
        searchCriteria={"name": name_pattern},
        returnedTags={
            "name": "",
            "description": "",
            "product": "",
            "model": "",
            "devicePoolName": "",
            "locationName": "",
        },
    )

    phones = []
    if res and "return" in res and res["return"]:
        phones = res["return"].get("phone", []) or []

    return phones


def count_devices(axl: AXLClient) -> int:
    """
    Returns total number of CUCM devices (all types) using SQL.

    This counts all rows in the 'device' table (phones, gateways, trunks, etc.).
    """
    res = axl.executeSQLQuery(sql="SELECT COUNT(*) AS cnt FROM device")
    rows = (res.get("return") or {}).get("row", [])
    if not rows:
        return 0
    row = rows[0]
    for key in row:
        return int(row[key])
    return 0


def create_phone(axl: AXLClient, data: PhoneCreate) -> Dict[str, Any]:
    """
    Wrapper for addPhone.

    Only the core commonly used fields are provided.
    """
    payload = {
        "name": data.name,
        "description": data.description,
        "product": data.product,
        "class": "Phone",
        "protocol": data.protocol,
        "protocolSide": "User",
        "devicePoolName": data.device_pool,
        "locationName": data.location,
        "callingSearchSpaceName": data.css,
        "ownerUserName": data.owner_user,
    }

    # Lines must be formatted per AXL specs:
    if data.lines:
        payload["lines"] = {
            "line": [
                {
                    "index": i + 1,
                    "dirn": {
                        "pattern": line.pattern,
                        "routePartitionName": line.partition,
                    },
                }
                for i, line in enumerate(data.lines)
            ]
        }

    payload = {k: v for k, v in payload.items() if v is not None}

    return axl.addPhone(phone=payload)


def update_phone(axl: AXLClient, name: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper for updatePhone.

    Use this when only a few fields need updating.
    """
    clean_fields = {k: v for k, v in fields.items() if v is not None}
    return axl.updatePhone(name=name, **clean_fields)


def delete_phone(axl: AXLClient, name: str) -> Dict[str, Any]:
    """
    Wrapper for removePhone.
    """
    return axl.removePhone(name=name)


# =============================================================================
# LINE OPERATIONS
# =============================================================================


def get_line(
    axl: AXLClient,
    pattern: str,
    partition: Optional[str],
) -> Dict[str, Any]:
    """
    Wrapper for getLine.
    """
    return axl.getLine(
        pattern=pattern,
        routePartitionName=partition or "",
    )


def create_line(axl: AXLClient, data: LineCreate) -> Dict[str, Any]:
    """
    Wrapper for addLine.
    """
    payload = {
        "pattern": data.pattern,
        "description": data.description,
        "routePartitionName": data.partition,
        "alertingName": data.alerting_name,
        "asciiAlertingName": data.ascii_alerting_name,
        "shareLineAppearanceCssName": data.share_css,
    }

    payload = {k: v for k, v in payload.items() if v is not None}

    return axl.addLine(line=payload)


def delete_line(
    axl: AXLClient,
    pattern: str,
    partition: Optional[str],
) -> Dict[str, Any]:
    """
    Wrapper for removeLine.
    """
    return axl.removeLine(pattern=pattern, routePartitionName=partition or "")


# =============================================================================
# TRUNK OPERATIONS (CONFIG-LEVEL)
# =============================================================================


def list_sip_trunks(
    axl: AXLClient,
    name_pattern: str = "%",
) -> List[Dict[str, Any]]:
    """
    Wrapper around listSipTrunk.

    Note: This is CONFIG-LEVEL ONLY, not real-time status. AXL does not expose
    live trunk up/down state; use RISPort/PerfMon for real-time status.
    """
    res = axl.listSipTrunk(
        searchCriteria={"name": name_pattern},
        returnedTags={
            "name": "",
            "description": "",
            "devicePoolName": "",
            "destinationAddress": "",
            "destinationPort": "",
            "sipProfileName": "",
            "securityProfileName": "",
        },
    )

    trunks = []
    if res and "return" in res and res["return"]:
        trunks = res["return"].get("sipTrunk", []) or []

    return trunks


def count_sip_trunks(axl: AXLClient) -> int:
    """
    Returns total number of configured SIP trunks.

    Uses SQL for efficiency (trunk table).
    """
    res = axl.executeSQLQuery(sql="SELECT COUNT(*) AS cnt FROM trunk")
    rows = (res.get("return") or {}).get("row", [])
    if not rows:
        return 0
    row = rows[0]
    for key in row:
        return int(row[key])
    return 0


def get_sip_trunk(
    axl: AXLClient,
    name: str,
) -> Dict[str, Any]:
    """
    Wrapper for getSipTrunk.
    """
    return axl.getSipTrunk(name=name)


def get_sip_trunk_config_summary(
    axl: AXLClient,
    name_pattern: str = "%",
) -> Dict[str, Any]:
    """
    High-level config summary for SIP trunks (not real-time health).

    Returns:
        {
          "count": int,
          "trunks": [... basic config dicts ...]
        }
    """
    trunks = list_sip_trunks(axl, name_pattern=name_pattern)
    return {
        "count": len(trunks),
        "trunks": trunks,
    }


# =============================================================================
# SYSTEM / CLUSTER STATUS (CONFIG-LEVEL)
# =============================================================================


def get_cluster_version(axl: AXLClient) -> Dict[str, Any]:
    """
    Wrapper for getCCMVersion.

    Provides a basic system-level sanity check and version info.
    """
    # Passing empty string for processNodeName returns cluster version.
    return axl.getCCMVersion(processNodeName="")


def get_process_nodes(axl: AXLClient) -> List[Dict[str, Any]]:
    """
    Returns CUCM process nodes (publisher/subscribers) via SQL.

    Useful to see which nodes exist and their IPs/roles.
    """
    sql = """
        SELECT
            name,
            description,
            ipv4address,
            tkprocessnoderole
        FROM processnode
        WHERE name NOT LIKE 'Standby%'
    """
    res = axl.executeSQLQuery(sql=sql)
    rows = (res.get("return") or {}).get("row", [])
    return rows or []


def get_system_summary(axl: AXLClient) -> Dict[str, Any]:
    """
    High-level configuration summary for the CUCM cluster.

    NOTE: This is all configuration-level data. For live registration,
    device/trunk up/down, or performance metrics, use RISPort/PerfMon APIs.
    """
    version = get_cluster_version(axl)
    user_count = count_users(axl)
    device_count = count_devices(axl)
    sip_trunk_count = count_sip_trunks(axl)
    nodes = get_process_nodes(axl)

    return {
        "clusterVersion": version,
        "counts": {
            "users": user_count,
            "devices": device_count,
            "sipTrunks": sip_trunk_count,
        },
        "processNodes": nodes,
    }


# =============================================================================
# RAW SQL HELPERS
# =============================================================================


def run_sql_query(axl: AXLClient, sql: str) -> Dict[str, Any]:
    """
    Wrapper for executeSQLQuery.

    Use sparingly and carefully; always validate SQL if coming from user input.
    """
    return axl.executeSQLQuery(sql=sql)


def run_sql_update(axl: AXLClient, sql: str) -> Dict[str, Any]:
    """
    Wrapper for executeSQLUpdate.
    """
    return axl.executeSQLUpdate(sql=sql)

# ---------------------------------------------------------------------------
# AXLService class wrapper (expected by FastAPI dependencies)
# ---------------------------------------------------------------------------

class AXLService:
    """
    High-level wrapper exposing all AXL operations as methods.
    FastAPI expects this when using `Depends(get_axl_service)`.
    """

    def __init__(self, client: AXLClient):
        self.client = client

    # -------------------------
    # USER OPERATIONS
    # -------------------------

    def get_user(self, userid: str):
        return get_user(self.client, userid)

    def list_users(self, userid_pattern: str = "%"):
        return list_users(self.client, userid_pattern)

    def count_users(self):
        return count_users(self.client)

    def create_user(self, data: UserCreate):
        return create_user(self.client, data)

    def update_user(self, userid: str, data: UserUpdate):
        return update_user(self.client, userid, data)

    def delete_user(self, userid: str):
        return delete_user(self.client, userid)

    # -------------------------
    # PHONE / DEVICE
    # -------------------------

    def get_phone(self, name: str):
        return get_phone(self.client, name)

    def list_phones(self, name_pattern: str = "%"):
        return list_phones(self.client, name_pattern)

    def count_devices(self):
        return count_devices(self.client)

    def create_phone(self, data: PhoneCreate):
        return create_phone(self.client, data)

    def update_phone(self, name: str, fields: Dict[str, Any]):
        return update_phone(self.client, name, fields)

    def delete_phone(self, name: str):
        return delete_phone(self.client, name)

    # -------------------------
    # LINES
    # -------------------------

    def get_line(self, pattern: str, partition: Optional[str]):
        return get_line(self.client, pattern, partition)

    def create_line(self, data: LineCreate):
        return create_line(self.client, data)

    def delete_line(self, pattern: str, partition: Optional[str]):
        return delete_line(self.client, pattern, partition)

    # -------------------------
    # SIP TRUNKS
    # -------------------------

    def list_sip_trunks(self, name_pattern: str = "%"):
        return list_sip_trunks(self.client, name_pattern)

    def count_sip_trunks(self):
        return count_sip_trunks(self.client)

    def get_sip_trunk(self, name: str):
        return get_sip_trunk(self.client, name)

    def get_sip_trunk_config_summary(self, name_pattern: str = "%"):
        return get_sip_trunk_config_summary(self.client, name_pattern)

    # -------------------------
    # SYSTEM / CLUSTER STATUS
    # -------------------------

    def get_cluster_version(self):
        return get_cluster_version(self.client)

    def get_process_nodes(self):
        return get_process_nodes(self.client)

    def get_system_summary(self):
        return get_system_summary(self.client)

    # -------------------------
    # RAW SQL
    # -------------------------

    def run_sql_query(self, sql: str):
        return run_sql_query(self.client, sql)

    def run_sql_update(self, sql: str):
        return run_sql_update(self.client, sql)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

from app.services.axl_loader import get_axl_client

def get_axl_service() -> AXLService:
    """
    FastAPI dependency that returns an initialized AXLService.
    """
    client = get_axl_client()
    return AXLService(client)

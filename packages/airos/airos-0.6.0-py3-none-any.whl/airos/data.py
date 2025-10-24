"""Provide mashumaro data object for AirOSData."""

from dataclasses import dataclass
from enum import Enum
import ipaddress
import logging
import re
from typing import Any

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig

logger = logging.getLogger(__name__)

# Regex for a standard MAC address format (e.g., 01:23:45:67:89:AB)
# This handles both colon and hyphen separators.
MAC_ADDRESS_REGEX = re.compile(r"^([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})$")

# Regex for a MAC address mask (e.g., the redacted format 00:00:00:00:89:AB)
MAC_ADDRESS_MASK_REGEX = re.compile(r"^(00:){4}[0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}$")


# Helper functions
def is_mac_address(value: str) -> bool:
    """Check if a string is a valid MAC address."""
    return bool(MAC_ADDRESS_REGEX.match(value))


def is_mac_address_mask(value: str) -> bool:
    """Check if a string is a valid MAC address mask (e.g., the redacted format)."""
    return bool(MAC_ADDRESS_MASK_REGEX.match(value))


def is_ip_address(value: str) -> bool:
    """Check if a string is a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True  # pragma: no cover


def redact_data_smart(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively redacts sensitive keys in a dictionary."""
    sensitive_keys = {
        "hostname",
        "essid",
        "mac",
        "apmac",
        "hwaddr",
        "lastip",
        "ipaddr",
        "ip6addr",
        "device_id",
        "sys_id",
        "station_id",
        "platform",
    }

    def _redact(d: dict[str, Any]) -> dict[str, Any]:
        redacted_d = {}
        for k, v in d.items():
            if k in sensitive_keys:
                if isinstance(v, str) and (is_mac_address(v) or is_mac_address_mask(v)):
                    # Redact only the last part of a MAC address to a dummy value
                    redacted_d[k] = "00:11:22:33:" + v.replace("-", ":").upper()[-5:]
                elif isinstance(v, str) and is_ip_address(v):  # pragma: no cover
                    # Redact to a dummy local IP address
                    redacted_d[k] = "127.0.0.3"
                elif isinstance(v, list) and all(
                    isinstance(i, str) and is_ip_address(i) for i in v
                ):  # pragma: no cover
                    # Redact list of IPs to a dummy list
                    redacted_d[k] = ["127.0.0.3"]  # type: ignore[assignment]
                elif isinstance(v, list) and all(
                    isinstance(i, dict) and "addr" in i and is_ip_address(i["addr"])
                    for i in v
                ):  # pragma: no cover
                    # Redact list of dictionaries with IP addresses to a dummy list
                    redacted_list = []
                    for item in v:
                        redacted_item = item.copy()
                        redacted_item["addr"] = (
                            "127.0.0.3"
                            if ipaddress.ip_address(redacted_item["addr"]).version == 4
                            else "::1"
                        )
                        redacted_list.append(redacted_item)
                    redacted_d[k] = redacted_list  # type: ignore[assignment]
                else:
                    redacted_d[k] = "REDACTED"
            elif isinstance(v, dict):
                redacted_d[k] = _redact(v)  # type: ignore[assignment]
            elif isinstance(v, list):
                redacted_d[k] = [
                    _redact(item) if isinstance(item, dict) else item for item in v
                ]  # type: ignore[assignment]
            else:
                redacted_d[k] = v
        return redacted_d

    return _redact(data)


class AirOSDataClass(DataClassDictMixin):
    """A base class for all mashumaro dataclasses."""


@dataclass
class AirOSDataBaseClass(AirOSDataClass):
    """Base class for all AirOS data models."""

    class Config(BaseConfig):
        """Create base class for multiple version support."""

        alias_generator = str.upper


def _check_and_log_unknown_enum_value(
    data_dict: dict[str, Any],
    key: str,
    enum_class: type[Enum],
    dataclass_name: str,
    field_name: str,
) -> None:
    """Clean unsupported parameters with logging."""
    value = data_dict.get(key)
    if value is not None and isinstance(value, str):
        if value not in [e.value for e in enum_class]:
            logger.warning(
                "Unknown value '%s' for %s.%s. Please report at "
                "https://github.com/CoMPaTech/python-airos/issues so we can add support.",
                value,
                dataclass_name,
                field_name,
            )
            del data_dict[key]


class IeeeMode(Enum):
    """Enum definition."""

    AUTO = "AUTO"
    _11ACVHT80 = "11ACVHT80"  # On a NanoStation
    _11ACVHT60 = "11ACVHT60"
    _11ACVHT50 = "11ACVHT50"
    _11ACVHT40 = "11ACVHT40"
    _11ACVHT20 = "11ACVHT20"  # On a LiteBeam
    _11NAHT40MINUS = "11NAHT40MINUS"  # On a v6 XM
    _11NAHT40PLUS = "11NAHT40PLUS"  # On a v6 XW
    # More to be added when known


class DerivedWirelessRole(Enum):
    """Enum definition."""

    STATION = "station"
    ACCESS_POINT = "access_point"


class DerivedWirelessMode(Enum):
    """Enum definition."""

    PTP = "point_to_point"
    PTMP = "point_to_multipoint"


class WirelessMode(Enum):
    """Enum definition."""

    PTMP_ACCESSPOINT = "ap-ptmp"
    PTMP_STATION = "sta-ptmp"
    PTP_ACCESSPOINT = "ap-ptp"
    PTP_STATION = "sta-ptp"
    UNKNOWN = "unknown"  # Reported on v8.7.18 NanoBeam 5AC for remote.mode
    # More to be added when known


class Wireless6Mode(Enum):
    """Enum definition."""

    STATION = "sta"
    ACCESSPOINT = "ap"
    # More to be added when known


class Security(Enum):
    """Enum definition."""

    WPA2 = "WPA2"
    # More to be added when known


class NetRole(Enum):
    """Enum definition."""

    BRIDGE = "bridge"
    ROUTER = "router"
    # More to be added when known


@dataclass
class ChainName(AirOSDataClass):
    """Leaf definition."""

    number: int
    name: str


@dataclass
class Host(AirOSDataClass):
    """Leaf definition."""

    hostname: str
    uptime: int
    power_time: int
    time: str
    timestamp: int
    fwversion: str
    devmodel: str
    netrole: NetRole
    loadavg: float | int | None
    totalram: int
    freeram: int
    temperature: int
    cpuload: float | int | None
    device_id: str
    height: int | None  # Reported none on LiteBeam 5AC

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Pre-deserialize hook for Host."""
        _check_and_log_unknown_enum_value(d, "netrole", NetRole, "Host", "netrole")
        return d


@dataclass
class Host6(AirOSDataClass):
    """Leaf definition."""

    hostname: str
    uptime: int
    fwversion: str
    fwprefix: str
    devmodel: str
    netrole: NetRole
    totalram: int
    freeram: int
    cpuload: float | int | None
    cputotal: float | int | None  # Reported on XM firmware
    cpubusy: float | int | None  # Reported on XM firmware

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Pre-deserialize hook for Host."""
        _check_and_log_unknown_enum_value(d, "netrole", NetRole, "Host", "netrole")

        # Calculate cpufloat from actuals instead on relying on near 100% value
        if (
            all(isinstance(d.get(k), (int, float)) for k in ("cpubusy", "cputotal"))
            and d["cputotal"] > 0
        ):
            d["cpuload"] = round((d["cpubusy"] / d["cputotal"]) * 100, 2)
        return d


@dataclass
class Services(AirOSDataClass):
    """Leaf definition."""

    dhcpc: bool
    dhcpd: bool
    dhcp6d_stateful: bool
    pppoe: bool
    airview: int


@dataclass
class Services6(AirOSDataClass):
    """Leaf definition."""

    dhcpc: bool
    dhcpd: bool
    pppoe: bool


@dataclass
class Airview6(AirOSDataClass):
    """Leaf definition."""

    enabled: int


@dataclass
class Firewall(AirOSDataClass):
    """Leaf definition."""

    iptables: bool
    ebtables: bool
    ip6tables: bool
    eb6tables: bool


@dataclass
class Throughput(AirOSDataClass):
    """Leaf definition."""

    tx: int
    rx: int


@dataclass
class ServiceTime(AirOSDataClass):
    """Leaf definition."""

    time: int
    link: int


@dataclass
class Polling(AirOSDataClass):
    """Leaf definition."""

    cb_capacity: int
    dl_capacity: int
    ul_capacity: int
    use: int
    tx_use: int
    rx_use: int
    atpc_status: int
    fixed_frame: bool
    gps_sync: bool
    ff_cap_rep: bool
    flex_mode: int | None = None  # Not present in all devices


@dataclass
class Polling6(AirOSDataClass):
    """Leaf definition."""

    dl_capacity: int | None = None  # New
    ul_capacity: int | None = None  # New


@dataclass
class Stats(AirOSDataClass):
    """Leaf definition."""

    rx_bytes: int
    rx_packets: int
    rx_pps: int
    tx_bytes: int
    tx_packets: int
    tx_pps: int


@dataclass
class EvmData(AirOSDataClass):
    """Leaf definition."""

    usage: int
    cinr: int
    evm: list[list[int]]


@dataclass
class Airmax(AirOSDataClass):
    """Leaf definition."""

    actual_priority: int
    beam: int
    desired_priority: int
    cb_capacity: int
    dl_capacity: int
    ul_capacity: int
    atpc_status: int
    rx: EvmData
    tx: EvmData


@dataclass
class EthList(AirOSDataClass):
    """Leaf definition."""

    ifname: str
    enabled: bool
    plugged: bool
    duplex: bool
    speed: int
    snr: list[int]
    cable_len: int


@dataclass
class GPSData(AirOSDataClass):
    """Leaf definition."""

    lat: float | int | None = None
    lon: float | int | None = None
    fix: int | None = None
    sats: int | None = None  # LiteAP GPS
    dim: int | None = None  # LiteAP GPS
    dop: float | int | None = None  # LiteAP GPS
    alt: float | int | None = None  # LiteAP GPS
    time_synced: int | None = None  # LiteAP GPS


@dataclass
class UnmsStatus(AirOSDataClass):
    """Leaf definition."""

    status: int
    timestamp: str | None = None


@dataclass
class Remote(AirOSDataClass):
    """Leaf definition."""

    device_id: str
    hostname: str
    platform: str
    version: str
    time: str
    cpuload: float | int | None
    temperature: int
    totalram: int
    freeram: int
    netrole: str
    sys_id: str
    tx_throughput: int
    rx_throughput: int
    uptime: int
    power_time: int
    compat_11n: int
    signal: int
    rssi: int
    noisefloor: int
    tx_power: int
    distance: int  # In meters
    rx_chainmask: int
    chainrssi: list[int]
    tx_ratedata: list[int]
    tx_bytes: int
    rx_bytes: int
    cable_loss: int
    ethlist: list[EthList]
    ipaddr: list[str]
    oob: bool
    unms: UnmsStatus
    airview: int
    service: ServiceTime
    mode: WirelessMode | None = None  # Investigate why remotes can have no mode set
    ip6addr: list[str] | None = None  # For v4 only devices
    height: int | None = None
    age: int | None = None  # At least not present on 8.7.11
    gps: GPSData | None = (
        None  # Reported NanoStation 5AC 8.7.18 without GPS Core 150491
    )
    antenna_gain: int | None = None  # Reported on Prism 6.3.5? and LiteBeam 8.7.8

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Pre-deserialize hook for Wireless."""
        _check_and_log_unknown_enum_value(d, "mode", WirelessMode, "Remote", "mode")
        return d


@dataclass
class Disconnected(AirOSDataClass):
    """Leaf definition for disconnected devices."""

    mac: str
    lastip: str
    hostname: str
    platform: str
    reason_code: int
    disconnect_duration: int
    airos_connected: bool = False  # Mock add to determine Disconnected vs Station
    signal: int | None = None  # Litebeam 5AC can have no signal


@dataclass
class Station(AirOSDataClass):
    """Leaf definition for connected/active devices."""

    mac: str
    lastip: str
    signal: int
    rssi: int
    noisefloor: int
    chainrssi: list[int]
    tx_idx: int
    rx_idx: int
    tx_nss: int
    rx_nss: int
    tx_latency: int
    distance: int  # In meters
    tx_packets: int
    tx_lretries: int
    tx_sretries: int
    uptime: int
    dl_signal_expect: int
    ul_signal_expect: int
    cb_capacity_expect: int
    dl_capacity_expect: int
    ul_capacity_expect: int
    dl_rate_expect: int
    ul_rate_expect: int
    dl_linkscore: int
    ul_linkscore: int
    dl_avg_linkscore: int
    ul_avg_linkscore: int
    tx_ratedata: list[int]
    stats: Stats
    airmax: Airmax
    last_disc: int
    remote: Remote
    airos_connected: bool = True  # Mock add to determine Disconnected vs Station


@dataclass
class Wireless(AirOSDataClass):
    """Leaf definition."""

    essid: str
    band: int
    compat_11n: int
    hide_essid: int
    apmac: str
    frequency: int
    center1_freq: int
    dfs: int
    distance: int  # In meters
    security: Security
    noisef: int
    txpower: int
    aprepeater: bool
    rstatus: int
    chanbw: int
    rx_chainmask: int
    tx_chainmask: int
    cac_state: int
    cac_timeout: int
    rx_idx: int
    rx_nss: int
    tx_idx: int
    tx_nss: int
    throughput: Throughput
    service: ServiceTime
    polling: Polling
    count: int
    sta: list[Station]
    sta_disconnected: list[Disconnected]
    ieeemode: IeeeMode
    mode: WirelessMode | None = None  # Investigate further (see WirelessMode in Remote)
    nol_state: int | None = None  # Reported on Prism 6.3.5? and LiteBeam 8.7.8
    nol_timeout: int | None = None  # Reported on Prism 6.3.5? and LiteBeam 8.7.8
    antenna_gain: int | None = None  # Reported on Prism 6.3.5? and LiteBeam 8.7.8

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Pre-deserialize hook for Wireless."""

        _check_and_log_unknown_enum_value(d, "mode", WirelessMode, "Wireless", "mode")

        _check_and_log_unknown_enum_value(
            d, "security", Security, "Wireless", "security"
        )

        # Ensure ieeemode/opmode are in uppercase and map opmode back into ieeemode
        d["ieeemode"] = d["ieeemode"].upper() or None
        _check_and_log_unknown_enum_value(
            d, "ieeemode", IeeeMode, "Wireless", "ieeemode"
        )

        return d


@dataclass
class Wireless6(AirOSDataClass):
    """Leaf definition."""

    essid: str
    hide_essid: int
    apmac: str
    countrycode: int
    channel: int
    frequency: int
    dfs: int
    opmode: str
    antenna: str
    chains: str
    signal: int
    rssi: int
    noisef: int
    txpower: int
    ack: int
    distance: int  # In meters
    ccq: int
    txrate: str
    rxrate: str
    security: Security
    qos: str
    rstatus: int
    cac_nol: int
    nol_chans: int
    wds: int
    aprepeater: int  # Not bool as v8
    chanbw: int
    polling: Polling6
    ieeemode: IeeeMode  # Virtual to match base/v8
    mode: Wireless6Mode | None = None
    antenna_gain: int | None = None  # Virtual to match base/v8

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        """Pre-deserialize hook for Wireless6."""
        _check_and_log_unknown_enum_value(d, "mode", Wireless6Mode, "Wireless6", "mode")
        _check_and_log_unknown_enum_value(
            d, "security", Security, "Wireless", "security"
        )

        freq = d.get("frequency")
        if isinstance(freq, str) and "MHz" in freq:
            d["frequency"] = int(freq.split()[0])

        rxrate = d.get("rxrate")
        txrate = d.get("txrate")
        d["polling"] = {  # Map to Polling6 as MBPS strings to int kbps
            "dl_capacity": int(float(rxrate) * 1000) if rxrate else 0,
            "ul_capacity": int(float(txrate) * 1000) if txrate else 0,
        }

        d["ieeemode"] = d["opmode"].upper() or None
        _check_and_log_unknown_enum_value(
            d, "ieeemode", IeeeMode, "Wireless", "ieeemode"
        )
        match = re.search(r"(\d+)\s*dBi", d["antenna"])
        d["antenna_gain"] = int(match.group(1)) if match else None

        return d


@dataclass
class InterfaceStatus(AirOSDataClass):
    """Leaf definition."""

    plugged: bool
    tx_bytes: int
    rx_bytes: int
    tx_packets: int
    rx_packets: int
    tx_errors: int
    rx_errors: int
    tx_dropped: int
    rx_dropped: int
    ipaddr: str
    speed: int
    duplex: bool
    snr: list[int] | None = None
    cable_len: int | None = None
    ip6addr: list[dict[str, Any]] | None = None


@dataclass
class Interface6Status(AirOSDataClass):
    """Leaf definition."""

    duplex: bool
    plugged: bool
    speed: int
    snr: list[int] | None = None
    cable_len: int | None = None
    ip6addr: list[dict[str, Any]] | None = None


@dataclass
class Interface(AirOSDataClass):
    """Leaf definition."""

    ifname: str
    hwaddr: str
    enabled: bool
    status: InterfaceStatus
    mtu: int


@dataclass
class Interface6(AirOSDataClass):
    """Leaf definition."""

    ifname: str
    hwaddr: str
    enabled: bool
    status: Interface6Status
    mtu: int | None = None  # Reported unpresent on v6


@dataclass
class ProvisioningMode(AirOSDataClass):
    """Leaf definition."""


@dataclass
class NtpClient(AirOSDataClass):
    """Leaf definition."""


@dataclass
class GPSMain(AirOSDataClass):
    """Leaf definition."""

    lat: float | int | None
    lon: float | int | None
    fix: int


@dataclass
class Derived(AirOSDataClass):
    """Contain custom data generated by this module."""

    mac: str  # Base device MAC address (i.e. eth0)
    mac_interface: str  # Interface derived from

    # Split for WirelessMode
    station: bool
    access_point: bool

    # Split for WirelessMode
    ptp: bool
    ptmp: bool

    role: DerivedWirelessRole
    mode: DerivedWirelessMode

    # Lookup of model_id (presumed via SKU)
    sku: str

    # Firmware major version
    fw_major: int | None = None


@dataclass
class AirOS8Data(AirOSDataBaseClass):
    """Dataclass for AirOS v8 devices."""

    chain_names: list[ChainName]
    host: Host
    genuine: str
    services: Services
    firewall: Firewall
    portfw: bool
    wireless: Wireless
    interfaces: list[Interface]
    provmode: Any
    ntpclient: Any
    unms: UnmsStatus
    derived: Derived
    gps: GPSData | None = (
        None  # Reported NanoStation 5AC 8.7.18 without GPS Core 150491
    )


@dataclass
class AirOS6Data(AirOSDataBaseClass):
    """Dataclass for AirOS v6 devices."""

    airview: Airview6
    host: Host6
    genuine: str
    services: Services6
    firewall: Firewall
    wireless: Wireless6
    interfaces: list[Interface6]
    unms: UnmsStatus
    derived: Derived

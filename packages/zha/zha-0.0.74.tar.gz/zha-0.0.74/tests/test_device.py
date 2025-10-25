"""Test ZHA device switch."""

import asyncio
from datetime import UTC, datetime
import logging
import time
from unittest import mock
from unittest.mock import call, patch

import pytest
from zigpy.exceptions import ZigbeeException
import zigpy.profiles.zha
from zigpy.quirks.registry import DeviceRegistry
from zigpy.quirks.v2 import DeviceAlertLevel, DeviceAlertMetadata, QuirkBuilder
from zigpy.quirks.v2.homeassistant import EntityType
from zigpy.quirks.v2.homeassistant.sensor import SensorDeviceClass, SensorStateClass
import zigpy.types
from zigpy.zcl import ClusterType
from zigpy.zcl.clusters import general
from zigpy.zcl.clusters.general import Ota, PowerConfiguration
from zigpy.zcl.foundation import Status, WriteAttributesResponse
import zigpy.zdo.types as zdo_t

from tests.common import (
    SIG_EP_INPUT,
    SIG_EP_OUTPUT,
    SIG_EP_PROFILE,
    SIG_EP_TYPE,
    create_mock_zigpy_device,
    get_entity,
    join_zigpy_device,
    zigpy_device_from_json,
)
from zha.application import Platform
from zha.application.const import (
    CLUSTER_COMMAND_SERVER,
    CLUSTER_COMMANDS_CLIENT,
    CLUSTER_COMMANDS_SERVER,
    CLUSTER_TYPE_IN,
    CLUSTER_TYPE_OUT,
    UNKNOWN,
)
from zha.application.gateway import Gateway
from zha.application.platforms import PlatformEntity
from zha.application.platforms.binary_sensor import IASZone
from zha.application.platforms.light import Light
from zha.application.platforms.sensor import LQISensor, RSSISensor
from zha.application.platforms.switch import Switch
from zha.exceptions import ZHAException
from zha.zigbee.device import (
    ClusterBinding,
    DeviceFirmwareInfoUpdatedEvent,
    ZHAEvent,
    get_device_automation_triggers,
)
from zha.zigbee.group import Group


def zigpy_device(
    zha_gateway: Gateway, with_basic_cluster_handler: bool = True, **kwargs
):
    """Return a ZigpyDevice with a switch cluster."""
    in_clusters = [general.OnOff.cluster_id]
    if with_basic_cluster_handler:
        in_clusters.append(general.Basic.cluster_id)

    endpoints = {
        3: {
            SIG_EP_INPUT: in_clusters,
            SIG_EP_OUTPUT: [],
            SIG_EP_TYPE: zigpy.profiles.zha.DeviceType.ON_OFF_SWITCH,
            SIG_EP_PROFILE: zigpy.profiles.zha.PROFILE_ID,
        }
    }
    return create_mock_zigpy_device(zha_gateway, endpoints, **kwargs)


def zigpy_device_mains(zha_gateway: Gateway, with_basic_cluster_handler: bool = True):
    """Return a ZigpyDevice with a switch cluster."""
    in_clusters = [general.OnOff.cluster_id]
    if with_basic_cluster_handler:
        in_clusters.append(general.Basic.cluster_id)

    endpoints = {
        3: {
            SIG_EP_INPUT: in_clusters,
            SIG_EP_OUTPUT: [],
            SIG_EP_TYPE: zigpy.profiles.zha.DeviceType.ON_OFF_SWITCH,
            SIG_EP_PROFILE: zigpy.profiles.zha.PROFILE_ID,
        }
    }
    return create_mock_zigpy_device(
        zha_gateway,
        endpoints,
        node_descriptor=zdo_t.NodeDescriptor(
            logical_type=zdo_t.LogicalType.EndDevice,
            complex_descriptor_available=0,
            user_descriptor_available=0,
            reserved=0,
            aps_flags=0,
            frequency_band=zdo_t.NodeDescriptor.FrequencyBand.Freq2400MHz,
            mac_capability_flags=(
                zdo_t.NodeDescriptor.MACCapabilityFlags.MainsPowered
                | zdo_t.NodeDescriptor.MACCapabilityFlags.AllocateAddress
            ),
            manufacturer_code=4447,
            maximum_buffer_size=127,
            maximum_incoming_transfer_size=100,
            server_mask=11264,
            maximum_outgoing_transfer_size=100,
            descriptor_capability_field=zdo_t.NodeDescriptor.DescriptorCapability.NONE,
        ),
    )


async def _send_time_changed(zha_gateway: Gateway, seconds: int):
    """Send a time changed event."""
    await asyncio.sleep(seconds)
    await zha_gateway.async_block_till_done(wait_background_tasks=True)


@patch(
    "zha.zigbee.cluster_handlers.general.BasicClusterHandler.async_initialize",
    new=mock.AsyncMock(),
)
async def test_check_available_success(
    zha_gateway: Gateway,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Check device availability success on 1st try."""
    device_with_basic_cluster_handler = zigpy_device_mains(
        zha_gateway, with_basic_cluster_handler=True
    )
    zha_device = await join_zigpy_device(zha_gateway, device_with_basic_cluster_handler)
    basic_ch = device_with_basic_cluster_handler.endpoints[3].basic

    assert not zha_device.is_coordinator
    assert not zha_device.is_active_coordinator

    basic_ch.read_attributes.reset_mock()
    device_with_basic_cluster_handler.last_seen = None
    assert zha_device.available is True
    await _send_time_changed(zha_gateway, zha_device.consider_unavailable_time + 2)
    assert zha_device.available is False
    assert basic_ch.read_attributes.await_count == 0

    device_with_basic_cluster_handler.last_seen = (
        time.time() - zha_device.consider_unavailable_time - 100
    )
    _seens = [time.time(), device_with_basic_cluster_handler.last_seen]

    def _update_last_seen(*args, **kwargs):  # pylint: disable=unused-argument
        new_last_seen = _seens.pop()
        device_with_basic_cluster_handler.last_seen = new_last_seen

    basic_ch.read_attributes.side_effect = _update_last_seen

    for entity in zha_device.platform_entities.values():
        entity.emit = mock.MagicMock(wraps=entity.emit)

    # we want to test the device availability handling alone
    zha_gateway.global_updater.stop()

    # successfully ping zigpy device, but zha_device is not yet available
    await _send_time_changed(
        zha_gateway, zha_gateway._device_availability_checker.__polling_interval + 1
    )
    assert basic_ch.read_attributes.await_count == 1
    assert basic_ch.read_attributes.await_args[0][0] == ["manufacturer"]
    assert zha_device.available is False

    for entity in zha_device.platform_entities.values():
        entity.emit.assert_not_called()
        assert not entity.available
        entity.emit.reset_mock()

    # There was traffic from the device: pings, but not yet available
    await _send_time_changed(
        zha_gateway, zha_gateway._device_availability_checker.__polling_interval + 1
    )
    assert basic_ch.read_attributes.await_count == 2
    assert basic_ch.read_attributes.await_args[0][0] == ["manufacturer"]
    assert zha_device.available is False

    for entity in zha_device.platform_entities.values():
        entity.emit.assert_not_called()
        assert not entity.available
        entity.emit.reset_mock()

    # There was traffic from the device: don't try to ping, marked as available
    await _send_time_changed(
        zha_gateway, zha_gateway._device_availability_checker.__polling_interval + 1
    )
    assert basic_ch.read_attributes.await_count == 2
    assert basic_ch.read_attributes.await_args[0][0] == ["manufacturer"]
    assert zha_device.available is True
    assert zha_device.on_network is True

    for entity in zha_device.platform_entities.values():
        entity.emit.assert_called()
        assert entity.available
        entity.emit.reset_mock()

    assert "Device is not on the network, marking unavailable" not in caplog.text
    zha_device.on_network = False

    assert zha_device.available is False
    assert zha_device.on_network is False

    assert "Device is not on the network, marking unavailable" in caplog.text

    for entity in zha_device.platform_entities.values():
        entity.emit.assert_called()
        assert not entity.available
        entity.emit.reset_mock()


@patch(
    "zha.zigbee.cluster_handlers.general.BasicClusterHandler.async_initialize",
    new=mock.AsyncMock(),
)
async def test_check_available_unsuccessful(
    zha_gateway: Gateway,
) -> None:
    """Check device availability all tries fail."""

    device_with_basic_cluster_handler = zigpy_device_mains(
        zha_gateway, with_basic_cluster_handler=True
    )
    zha_device = await join_zigpy_device(zha_gateway, device_with_basic_cluster_handler)
    basic_ch = device_with_basic_cluster_handler.endpoints[3].basic

    assert zha_device.available is True
    assert basic_ch.read_attributes.await_count == 0

    device_with_basic_cluster_handler.last_seen = (
        time.time() - zha_device.consider_unavailable_time - 2
    )

    for entity in zha_device.platform_entities.values():
        entity.emit = mock.MagicMock(wraps=entity.emit)

    # we want to test the device availability handling alone
    zha_gateway.global_updater.stop()

    # unsuccessfully ping zigpy device, but zha_device is still available
    await _send_time_changed(
        zha_gateway, zha_gateway._device_availability_checker.__polling_interval + 1
    )

    assert basic_ch.read_attributes.await_count == 1
    assert basic_ch.read_attributes.await_args[0][0] == ["manufacturer"]
    assert zha_device.available is True

    for entity in zha_device.platform_entities.values():
        entity.emit.assert_not_called()
        assert entity.available
        entity.emit.reset_mock()

    # still no traffic, but zha_device is still available
    await _send_time_changed(
        zha_gateway, zha_gateway._device_availability_checker.__polling_interval + 1
    )

    assert basic_ch.read_attributes.await_count == 2
    assert basic_ch.read_attributes.await_args[0][0] == ["manufacturer"]
    assert zha_device.available is True

    for entity in zha_device.platform_entities.values():
        entity.emit.assert_not_called()
        assert entity.available
        entity.emit.reset_mock()

    # not even trying to update, device is unavailable
    await _send_time_changed(
        zha_gateway, zha_gateway._device_availability_checker.__polling_interval + 1
    )

    assert basic_ch.read_attributes.await_count == 2
    assert basic_ch.read_attributes.await_args[0][0] == ["manufacturer"]
    assert zha_device.available is False

    for entity in zha_device.platform_entities.values():
        entity.emit.assert_called()
        assert not entity.available
        entity.emit.reset_mock()


@patch(
    "zha.zigbee.cluster_handlers.general.BasicClusterHandler.async_initialize",
    new=mock.AsyncMock(),
)
async def test_check_available_no_basic_cluster_handler(
    zha_gateway: Gateway,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Check device availability for a device without basic cluster."""
    device_without_basic_cluster_handler = zigpy_device(
        zha_gateway, with_basic_cluster_handler=False
    )
    caplog.set_level(logging.DEBUG, logger="homeassistant.components.zha")

    zha_device = await join_zigpy_device(
        zha_gateway, device_without_basic_cluster_handler
    )

    assert zha_device.available is True

    device_without_basic_cluster_handler.last_seen = (
        time.time() - zha_device.consider_unavailable_time - 2
    )

    assert "does not have a mandatory basic cluster" not in caplog.text
    await _send_time_changed(
        zha_gateway, zha_gateway._device_availability_checker.__polling_interval + 1
    )

    assert zha_device.available is False
    assert "does not have a mandatory basic cluster" in caplog.text


async def test_device_is_active_coordinator(
    zha_gateway: Gateway,
) -> None:
    """Test that the current coordinator is uniquely detected."""

    current_coord_dev = zigpy_device(
        zha_gateway, ieee="aa:bb:cc:dd:ee:ff:00:11", nwk=0x0000
    )
    current_coord_dev.node_desc = current_coord_dev.node_desc.replace(
        logical_type=zdo_t.LogicalType.Coordinator
    )

    old_coord_dev = zigpy_device(
        zha_gateway, ieee="aa:bb:cc:dd:ee:ff:00:12", nwk=0x0000
    )
    old_coord_dev.node_desc = old_coord_dev.node_desc.replace(
        logical_type=zdo_t.LogicalType.Coordinator
    )

    # The two coordinators have different IEEE addresses
    assert current_coord_dev.ieee != old_coord_dev.ieee

    current_coordinator = await join_zigpy_device(zha_gateway, current_coord_dev)
    stale_coordinator = await join_zigpy_device(zha_gateway, old_coord_dev)

    # Ensure the current ApplicationController's IEEE matches our coordinator's
    current_coordinator.gateway.application_controller.state.node_info.ieee = (
        current_coord_dev.ieee
    )

    assert current_coordinator.is_active_coordinator
    assert not stale_coordinator.is_active_coordinator


@pytest.mark.parametrize(
    # node_info is populated with manf and model strings
    ("manf", "model", "expected_manf", "expected_model", "expected_name"),
    [
        ("RealManf", "RealModel", "RealManf", "RealModel", "RealManf RealModel"),
        (
            "RealManf",
            None,
            "RealManf",
            "Generic Zigbee Coordinator (EZSP)",
            "RealManf Generic Zigbee Coordinator (EZSP)",
        ),
        (None, "RealModel", "", "RealModel", " RealModel"),
        (
            None,
            None,
            "",
            "Generic Zigbee Coordinator (EZSP)",
            " Generic Zigbee Coordinator (EZSP)",
        ),
        (
            "Nabu Casa",
            "Home Assistant Connect ZBT-2",
            "Nabu Casa",
            "Home Assistant Connect ZBT-2",
            "Home Assistant Connect ZBT-2",
        ),
    ],
)
async def test_coordinator_info_names(
    zha_gateway: Gateway,
    manf,
    model,
    expected_manf,
    expected_model,
    expected_name,
) -> None:
    """Test that the current coordinator device is named correctly."""

    current_coord_dev = zigpy_device(
        zha_gateway, ieee="aa:bb:cc:dd:ee:ff:00:11", nwk=0x0000
    )
    current_coord_dev.node_desc = current_coord_dev.node_desc.replace(
        logical_type=zdo_t.LogicalType.Coordinator
    )

    app = current_coord_dev.application
    app.state.node_info.ieee = current_coord_dev.ieee
    app.state.node_info.manufacturer = manf
    app.state.node_info.model = model

    current_coordinator = await join_zigpy_device(zha_gateway, current_coord_dev)
    assert current_coordinator.is_active_coordinator

    assert current_coordinator.manufacturer == expected_manf
    assert current_coordinator.model == expected_model
    assert current_coordinator.name == expected_name


async def test_async_get_clusters(
    zha_gateway: Gateway,
) -> None:
    """Test async_get_clusters method."""
    zigpy_dev = zigpy_device(zha_gateway, with_basic_cluster_handler=True)
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    assert zha_device.async_get_clusters() == {
        3: {
            CLUSTER_TYPE_IN: {
                general.Basic.cluster_id: zigpy_dev.endpoints[3].in_clusters[
                    general.Basic.cluster_id
                ],
                general.OnOff.cluster_id: zigpy_dev.endpoints[3].in_clusters[
                    general.OnOff.cluster_id
                ],
            },
            CLUSTER_TYPE_OUT: {},
        }
    }


async def test_async_get_groupable_endpoints(
    zha_gateway: Gateway,
) -> None:
    """Test async_get_groupable_endpoints method."""
    zigpy_dev = zigpy_device(zha_gateway, with_basic_cluster_handler=True)
    zigpy_dev.endpoints[3].add_input_cluster(general.Groups.cluster_id)
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    assert zha_device.async_get_groupable_endpoints() == [3]


async def test_async_get_std_clusters(
    zha_gateway: Gateway,
) -> None:
    """Test async_get_std_clusters method."""
    zigpy_dev = zigpy_device(zha_gateway, with_basic_cluster_handler=True)
    zigpy_dev.endpoints[3].profile_id = zigpy.profiles.zha.PROFILE_ID
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    assert zha_device.async_get_std_clusters() == {
        3: {
            CLUSTER_TYPE_IN: {
                general.Basic.cluster_id: zigpy_dev.endpoints[3].in_clusters[
                    general.Basic.cluster_id
                ],
                general.OnOff.cluster_id: zigpy_dev.endpoints[3].in_clusters[
                    general.OnOff.cluster_id
                ],
            },
            CLUSTER_TYPE_OUT: {},
        }
    }


async def test_async_get_cluster(
    zha_gateway: Gateway,
) -> None:
    """Test async_get_cluster method."""
    zigpy_dev = zigpy_device(zha_gateway, with_basic_cluster_handler=True)
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    assert zha_device.async_get_cluster(3, general.OnOff.cluster_id) == (
        zigpy_dev.endpoints[3].on_off
    )


async def test_async_get_cluster_attributes(
    zha_gateway: Gateway,
) -> None:
    """Test async_get_cluster_attributes method."""
    zigpy_dev = zigpy_device(zha_gateway, with_basic_cluster_handler=True)
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    assert (
        zha_device.async_get_cluster_attributes(3, general.OnOff.cluster_id)
        == zigpy_dev.endpoints[3].on_off.attributes
    )

    with pytest.raises(KeyError):
        assert (
            zha_device.async_get_cluster_attributes(3, general.BinaryValue.cluster_id)
            is None
        )


async def test_async_get_cluster_commands(
    zha_gateway: Gateway,
) -> None:
    """Test async_get_cluster_commands method."""
    zigpy_dev = zigpy_device(zha_gateway, with_basic_cluster_handler=True)
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    assert zha_device.async_get_cluster_commands(3, general.OnOff.cluster_id) == {
        CLUSTER_COMMANDS_CLIENT: zigpy_dev.endpoints[3].on_off.client_commands,
        CLUSTER_COMMANDS_SERVER: zigpy_dev.endpoints[3].on_off.server_commands,
    }


async def test_write_zigbee_attribute(
    zha_gateway: Gateway,
) -> None:
    """Test write_zigbee_attribute method."""
    zigpy_dev = zigpy_device(zha_gateway, with_basic_cluster_handler=True)
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    with pytest.raises(
        ValueError,
        match="Cluster 8 not found on endpoint 3 while writing attribute 0 with value 20",
    ):
        await zha_device.write_zigbee_attribute(
            3,
            general.LevelControl.cluster_id,
            general.LevelControl.AttributeDefs.current_level.id,
            20,
        )

    cluster = zigpy_dev.endpoints[3].on_off
    cluster.write_attributes.reset_mock()

    response: WriteAttributesResponse = await zha_device.write_zigbee_attribute(
        3,
        general.OnOff.cluster_id,
        general.OnOff.AttributeDefs.start_up_on_off.id,
        general.OnOff.StartUpOnOff.PreviousValue,
    )

    assert response is not None
    assert len(response) == 1
    status_record = response[0][0]
    assert status_record.status == Status.SUCCESS

    assert cluster.write_attributes.await_count == 1
    assert cluster.write_attributes.await_args == call(
        {
            general.OnOff.AttributeDefs.start_up_on_off.id: general.OnOff.StartUpOnOff.PreviousValue
        },
        manufacturer=None,
    )

    cluster.write_attributes.reset_mock()
    cluster.write_attributes.side_effect = ZigbeeException
    m1 = "Failed to set attribute: value: <StartUpOnOff.PreviousValue: 255> "
    m2 = "attribute: 16387 cluster_id: 6 endpoint_id: 3"
    with pytest.raises(
        ZHAException,
        match=f"{m1}{m2}",
    ):
        await zha_device.write_zigbee_attribute(
            3,
            general.OnOff.cluster_id,
            general.OnOff.AttributeDefs.start_up_on_off.id,
            general.OnOff.StartUpOnOff.PreviousValue,
        )

    cluster = zigpy_dev.endpoints[3].on_off
    cluster.write_attributes.reset_mock()


async def test_issue_cluster_command(
    zha_gateway: Gateway,
) -> None:
    """Test issue_cluster_command method."""
    zigpy_dev = zigpy_device(zha_gateway, with_basic_cluster_handler=True)
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    with pytest.raises(
        ValueError,
        match="Cluster 8 not found on endpoint 3 while issuing command 0 with args \\[20\\]",
    ):
        await zha_device.issue_cluster_command(
            3,
            general.LevelControl.cluster_id,
            general.LevelControl.ServerCommandDefs.move_to_level.id,
            CLUSTER_COMMAND_SERVER,
            [20],
            None,
        )

    cluster = zigpy_dev.endpoints[3].on_off

    with patch("zigpy.zcl.Cluster.request", return_value=[0x5, Status.SUCCESS]):
        await zha_device.issue_cluster_command(
            3,
            general.OnOff.cluster_id,
            general.OnOff.ServerCommandDefs.on.id,
            CLUSTER_COMMAND_SERVER,
            None,
            {},
        )

        assert cluster.request.await_count == 1


async def test_async_add_to_group_remove_from_group(
    zha_gateway: Gateway,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test async_add_to_group and async_remove_from_group methods."""
    zigpy_dev = zigpy_device(zha_gateway, with_basic_cluster_handler=True)
    zigpy_dev.endpoints[3].add_input_cluster(general.Groups.cluster_id)
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    group: Group = zha_device.gateway.groups[0x1001]

    assert (zha_device.ieee, 3) not in group.zigpy_group.members

    await zha_device.async_add_to_group(group.group_id)

    assert (zha_device.ieee, 3) in group.zigpy_group.members

    await zha_device.async_remove_from_group(group.group_id)

    assert (zha_device.ieee, 3) not in group.zigpy_group.members

    await zha_device.async_add_endpoint_to_group(3, group.group_id)

    assert (zha_device.ieee, 3) in group.zigpy_group.members

    await zha_device.async_remove_endpoint_from_group(3, group.group_id)

    assert (zha_device.ieee, 3) not in group.zigpy_group.members

    with patch("zigpy.device.Device.add_to_group", side_effect=ZigbeeException):
        await zha_device.async_add_to_group(group.group_id)
        assert (zha_device.ieee, 3) not in group.zigpy_group.members
        assert (
            "Failed to add device '00:0d:6f:00:0a:90:69:e7' to group: 0x1001"
            in caplog.text
        )

    with patch("zigpy.endpoint.Endpoint.add_to_group", side_effect=ZigbeeException):
        await zha_device.async_add_endpoint_to_group(3, group.group_id)
        assert (zha_device.ieee, 3) not in group.zigpy_group.members
        assert (
            "Failed to add endpoint: 3 for device: '00:0d:6f:00:0a:90:69:e7' to group: 0x1001"
            in caplog.text
        )

    # add it
    assert (zha_device.ieee, 3) not in group.zigpy_group.members
    await zha_device.async_add_to_group(group.group_id)
    assert (zha_device.ieee, 3) in group.zigpy_group.members

    with patch("zigpy.device.Device.remove_from_group", side_effect=ZigbeeException):
        await zha_device.async_remove_from_group(group.group_id)
        assert (zha_device.ieee, 3) in group.zigpy_group.members
        assert (
            "Failed to remove device '00:0d:6f:00:0a:90:69:e7' from group: 0x1001"
            in caplog.text
        )

    with patch(
        "zigpy.endpoint.Endpoint.remove_from_group", side_effect=ZigbeeException
    ):
        await zha_device.async_remove_endpoint_from_group(3, group.group_id)
        assert (zha_device.ieee, 3) in group.zigpy_group.members
        assert (
            "Failed to remove endpoint: 3 for device '00:0d:6f:00:0a:90:69:e7' from group: 0x1001"
            in caplog.text
        )


async def test_async_bind_to_group(
    zha_gateway: Gateway,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test async_bind_to_group method."""
    zigpy_dev = zigpy_device(zha_gateway, with_basic_cluster_handler=True)
    zigpy_dev.endpoints[3].add_input_cluster(general.Groups.cluster_id)
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    zigpy_dev_remote = zigpy_device(zha_gateway, with_basic_cluster_handler=True)
    zigpy_dev_remote._ieee = zigpy.types.EUI64.convert("00:0d:7f:00:0a:90:69:e8")
    zigpy_dev_remote.endpoints[3].add_output_cluster(general.OnOff.cluster_id)
    zha_device_remote = await join_zigpy_device(zha_gateway, zigpy_dev_remote)
    assert zha_device_remote is not None

    group: Group = zha_device.gateway.groups[0x1001]

    # add a device to the group for binding
    assert (zha_device.ieee, 3) not in group.zigpy_group.members
    await zha_device.async_add_to_group(group.group_id)
    assert (zha_device.ieee, 3) in group.zigpy_group.members

    await zha_device_remote.async_bind_to_group(
        group.group_id,
        [ClusterBinding(name="on_off", type=CLUSTER_TYPE_OUT, id=6, endpoint_id=3)],
    )
    assert (
        "0xb79c: Bind_req 00:0d:7f:00:0a:90:69:e8, ep: 3, cluster: 6 to group: 0x1001 completed: [<Status.SUCCESS: 0>]"
        in caplog.text
    )

    await zha_device_remote.async_unbind_from_group(
        group.group_id,
        [ClusterBinding(name="on_off", type=CLUSTER_TYPE_OUT, id=6, endpoint_id=3)],
    )

    m1 = "0xb79c: Unbind_req 00:0d:7f:00:0a:90:69:e8, ep: 3, cluster: 6"
    assert f"{m1} to group: 0x1001 completed: [<Status.SUCCESS: 0>]" in caplog.text


async def test_device_automation_triggers(
    zha_gateway: Gateway,
) -> None:
    """Test device automation triggers."""
    zigpy_dev = zigpy_device(zha_gateway, with_basic_cluster_handler=True)
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    assert get_device_automation_triggers(zha_device) == {
        ("device_offline", "device_offline"): {"device_event_type": "device_offline"}
    }

    assert zha_device.device_automation_commands == {}
    assert zha_device.device_automation_triggers == {
        ("device_offline", "device_offline"): {"device_event_type": "device_offline"}
    }


async def test_device_properties(
    zha_gateway: Gateway,
) -> None:
    """Test device properties."""
    zigpy_dev = zigpy_device(zha_gateway, with_basic_cluster_handler=True)
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    assert zha_device.is_mains_powered is False
    assert zha_device.is_end_device is True
    assert zha_device.is_router is False
    assert zha_device.is_coordinator is False
    assert zha_device.is_active_coordinator is False
    assert zha_device.device_type == "EndDevice"
    assert zha_device.power_source == "Battery or Unknown"
    assert zha_device.available is True
    assert zha_device.on_network is True
    assert zha_device.last_seen is not None
    assert zha_device.last_seen < time.time()

    assert zha_device.ieee == zigpy_dev.ieee
    assert zha_device.nwk == zigpy_dev.nwk
    assert zha_device.manufacturer_code == 0x1037
    assert zha_device.name == "FakeManufacturer FakeModel"
    assert zha_device.manufacturer == "FakeManufacturer"
    assert zha_device.model == "FakeModel"
    assert zha_device.is_groupable is False

    assert zha_device.power_configuration_ch is None
    assert zha_device.basic_ch is not None
    assert zha_device.firmware_version is None

    assert len(zha_device.platform_entities) == 3

    lqi_entity = zha_device.platform_entities[
        Platform.SENSOR, "00:0d:6f:00:0a:90:69:e7-3-0-lqi"
    ]
    assert type(lqi_entity) is LQISensor

    rssi_entity = zha_device.platform_entities[
        Platform.SENSOR, "00:0d:6f:00:0a:90:69:e7-3-0-rssi"
    ]
    assert type(rssi_entity) is RSSISensor

    switch_entity = zha_device.platform_entities[
        Platform.SWITCH, "00:0d:6f:00:0a:90:69:e7-3-6"
    ]
    assert isinstance(switch_entity, Switch)

    with pytest.raises(KeyError, match="Entity foo not found"):
        zha_device.get_platform_entity("bar", "foo")

    # test things are none when they aren't returned by Zigpy
    zigpy_dev.node_desc = None
    delattr(zha_device, "manufacturer_code")
    delattr(zha_device, "is_mains_powered")
    delattr(zha_device, "device_type")
    delattr(zha_device, "is_router")
    delattr(zha_device, "is_end_device")
    delattr(zha_device, "is_coordinator")

    assert zha_device.manufacturer_code is None
    assert zha_device.is_mains_powered is None
    assert zha_device.device_type is UNKNOWN
    assert zha_device.is_router is None
    assert zha_device.is_end_device is None
    assert zha_device.is_coordinator is None


async def test_device_firmware_version_syncing(zha_gateway: Gateway) -> None:
    """Test device firmware version syncing."""
    zigpy_dev = await zigpy_device_from_json(
        zha_gateway.application_controller,
        "tests/data/devices/philips-sml001.json",
    )

    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    # Register a callback to listen for device updates
    update_callback = mock.Mock()
    zha_device.on_event(DeviceFirmwareInfoUpdatedEvent.event_type, update_callback)

    # The firmware version is restored on device initialization
    assert zha_device.firmware_version == "0x42006bb7"

    # If we update the entity, the device updates as well
    update_entity = get_entity(zha_device, platform=Platform.UPDATE)
    update_entity._ota_cluster_handler.attribute_updated(
        attrid=Ota.AttributeDefs.current_file_version.id,
        value=zigpy.types.uint32_t(0xABCD1234),
        timestamp=datetime.now(UTC),
    )

    assert zha_device.firmware_version == "0xabcd1234"

    # Duplicate updates are ignored
    update_entity._ota_cluster_handler.attribute_updated(
        attrid=Ota.AttributeDefs.current_file_version.id,
        value=zigpy.types.uint32_t(0xABCD1234),
        timestamp=datetime.now(UTC),
    )

    assert zha_device.firmware_version == "0xabcd1234"
    assert update_callback.mock_calls == [
        call(
            DeviceFirmwareInfoUpdatedEvent(
                old_firmware_version="0x42006bb7",
                new_firmware_version="0xabcd1234",
            )
        )
    ]


async def test_quirks_v2_device_renaming(zha_gateway: Gateway) -> None:
    """Test quirks v2 device renaming."""
    registry = DeviceRegistry()

    (
        QuirkBuilder("CentraLite", "3405-L", registry=registry)
        .friendly_name(manufacturer="Lowe's", model="IRIS Keypad V2")
        .add_to_registry()
    )

    zigpy_dev = registry.get_device(
        await zigpy_device_from_json(
            zha_gateway.application_controller,
            "tests/data/devices/centralite-3405-l.json",
        )
    )

    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)
    assert zha_device.model == "IRIS Keypad V2"
    assert zha_device.manufacturer == "Lowe's"


async def test_quirks_v2_device_alerts(zha_gateway: Gateway) -> None:
    """Test quirks v2 device alerts."""

    # Normal device, no alerts
    zigpy_dev = await zigpy_device_from_json(
        zha_gateway.application_controller,
        "tests/data/devices/ikea-of-sweden-tradfri-bulb-e26-opal-1000lm.json",
    )
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)
    assert not zha_device.device_alerts

    # Explicit alerts
    registry = DeviceRegistry()

    (
        QuirkBuilder("CentraLite", "3405-L", registry=registry)
        .device_alert(level=DeviceAlertLevel.WARNING, message="Test warning")
        .add_to_registry()
    )

    zigpy_dev = registry.get_device(
        await zigpy_device_from_json(
            zha_gateway.application_controller,
            "tests/data/devices/centralite-3405-l.json",
        )
    )

    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)
    assert zha_device.device_alerts == (
        DeviceAlertMetadata(level=DeviceAlertLevel.WARNING, message="Test warning"),
    )


@pytest.mark.parametrize(
    ("json_path", "primary_platform", "primary_entity_type"),
    [
        # Light bulb
        (
            "tests/data/devices/ikea-of-sweden-tradfri-bulb-gu10-ws-400lm.json",
            Platform.LIGHT,
            Light,
        ),
        # Night light with a bulb and a motion sensor
        (
            "tests/data/devices/third-reality-inc-3rsnl02043z.json",
            Platform.LIGHT,
            Light,
        ),
        # Door sensor
        (
            "tests/data/devices/centralite-3320-l.json",
            Platform.BINARY_SENSOR,
            IASZone,
        ),
        # Smart plug with energy monitoring
        (
            "tests/data/devices/innr-sp-234.json",
            Platform.SWITCH,
            Switch,
        ),
        # Atmosphere sensor with humidity, temperature, and pressure
        (
            "tests/data/devices/lumi-lumi-weather.json",
            None,
            None,
        ),
    ],
)
async def test_primary_entity_computation(
    json_path: str,
    primary_platform: Platform | None,
    primary_entity_type: PlatformEntity | None,
    zha_gateway: Gateway,
) -> None:
    """Test primary entity computation."""

    zigpy_dev = await zigpy_device_from_json(
        zha_gateway.application_controller,
        json_path,
    )
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    # There is a single light entity
    primary = [e for e in zha_device.platform_entities.values() if e.primary]

    if primary_platform is None:
        assert not primary
    else:
        assert primary == [
            get_entity(zha_device, primary_platform, entity_type=primary_entity_type)
        ]


async def test_quirks_v2_primary_entity(zha_gateway: Gateway) -> None:
    """Test quirks v2 primary entity."""
    registry = DeviceRegistry()

    (
        QuirkBuilder("CentraLite", "3405-L", registry=registry)
        .sensor(
            attribute_name=PowerConfiguration.AttributeDefs.battery_quantity.id,
            cluster_id=PowerConfiguration.cluster_id,
            translation_key="battery_quantity",
            fallback_name="Battery quantity",
            primary=True,
        )
        .add_to_registry()
    )

    zigpy_dev = registry.get_device(
        await zigpy_device_from_json(
            zha_gateway.application_controller,
            "tests/data/devices/centralite-3405-l.json",
        )
    )

    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    (primary,) = [e for e in zha_device.platform_entities.values() if e.primary]
    assert primary.translation_key == "battery_quantity"


async def test_quirks_v2_prevent_default_entities(zha_gateway: Gateway) -> None:
    """Test quirks v2 can prevent creating default entities."""
    registry = DeviceRegistry()

    (
        QuirkBuilder("CentraLite", "3405-L", registry=registry)
        .prevent_default_entity_creation(endpoint_id=123)
        .prevent_default_entity_creation(cluster_id=0x4567)
        .prevent_default_entity_creation(unique_id_suffix="_something")
        .prevent_default_entity_creation(function=lambda entity: None)
        .prevent_default_entity_creation(
            function=lambda entity: entity.__class__.__name__ == "IdentifyButton"
        )
        .add_to_registry()
    )

    zigpy_dev = registry.get_device(
        await zigpy_device_from_json(
            zha_gateway.application_controller,
            "tests/data/devices/centralite-3405-l.json",
        )
    )

    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    with pytest.raises(KeyError):
        zha_device.get_platform_entity(
            Platform.BUTTON, unique_id="00:0d:6f:00:05:65:83:f2-1-3"
        )

    assert len(zha_device.platform_entities) == 8


async def test_quirks_v2_change_entity_metadata(zha_gateway: Gateway) -> None:
    """Test quirks v2 can change entity metadata."""
    registry = DeviceRegistry()

    def filter_func(entity) -> bool:
        return entity.__class__.__name__ == "LQISensor"

    (
        QuirkBuilder("CentraLite", "3405-L", registry=registry)
        .change_entity_metadata(
            endpoint_id=1,
            unique_id_suffix="-lqi",
            new_device_class=SensorDeviceClass.POWER,
            new_state_class=SensorStateClass.MEASUREMENT,
            new_entity_category=EntityType.CONFIG,
            new_entity_registry_enabled_default=False,
            new_translation_key="custom_lqi_key",
            new_fallback_name="Custom LQI Name",
        )
        .change_entity_metadata(
            function=filter_func,
            new_unique_id="custom_lqi_unique_id",
        )
        .change_entity_metadata(
            endpoint_id=1,
            cluster_id=general.Identify.cluster_id,
            cluster_type=ClusterType.Server,
            new_primary=True,
        )
        .add_to_registry()
    )

    zigpy_dev = registry.get_device(
        await zigpy_device_from_json(
            zha_gateway.application_controller,
            "tests/data/devices/centralite-3405-l.json",
        )
    )

    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    # Find the LQI sensor entity to verify metadata changes were applied
    lqi_entity = get_entity(
        zha_device, platform=Platform.SENSOR, qualifier="custom_lqi_unique_id"
    )

    assert lqi_entity is not None, "LQI sensor entity should exist"

    # Verify metadata changes were applied - first filter matches by endpoint_id=1 and unique_id_suffix="-lqi"
    assert lqi_entity._attr_device_class == SensorDeviceClass.POWER
    assert lqi_entity._attr_state_class == SensorStateClass.MEASUREMENT
    assert lqi_entity._attr_entity_category == EntityType.CONFIG
    assert lqi_entity._attr_entity_registry_enabled_default is False
    assert lqi_entity._attr_translation_key == "custom_lqi_key"
    assert lqi_entity._attr_fallback_name == "Custom LQI Name"

    # Verify metadata changes from second filter - function-based match
    assert lqi_entity.unique_id == "custom_lqi_unique_id"

    button_entity = get_entity(zha_device, platform=Platform.BUTTON)
    assert button_entity._attr_primary is True


async def test_join_binding_reporting(zha_gateway: Gateway) -> None:
    """Test that new joins go through binding and attribute reporting."""

    zigpy_dev = await zigpy_device_from_json(
        zha_gateway.application_controller,
        "tests/data/devices/espressif-zigbeecarbondioxidesensor.json",
    )

    co2 = zigpy_dev.endpoints[10].carbon_dioxide_concentration

    with (
        patch.object(co2, "bind", wraps=co2.bind) as mock_bind,
        patch.object(
            co2, "configure_reporting_multiple", wraps=co2.configure_reporting_multiple
        ) as mock_reporting_config,
    ):
        await join_zigpy_device(zha_gateway, zigpy_dev)

    assert mock_bind.mock_calls == [call()]
    assert mock_reporting_config.mock_calls == [
        call({"measured_value": (30, 900, 1e-6)})
    ]


async def test_endpoint_none_profile(
    zha_gateway: Gateway,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test endpoint with None profile id being skipped."""
    zigpy_dev = zigpy_device(zha_gateway, with_basic_cluster_handler=True)
    zigpy_dev.endpoints[3].profile_id = None
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    assert zha_device.async_get_std_clusters() == {}
    assert "Skipping endpoint, profile is None" in caplog.text


async def test_somrig_events(zha_gateway: Gateway) -> None:
    """Test that Somrig events are handled correctly."""

    zigpy_dev = await zigpy_device_from_json(
        zha_gateway.application_controller,
        "tests/data/devices/ikea-of-sweden-somrig-shortcut-button.json",
    )

    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    listener = mock.Mock()
    zha_device.on_all_events(listener)

    # ShortcutV2Cluster:initial_press(new_position=0)
    zigpy_dev.packet_received(
        zigpy.types.ZigbeePacket(
            src_ep=1,
            dst_ep=1,
            tsn=0,
            profile_id=260,
            cluster_id=64640,
            data=zigpy.types.SerializableBytes(b"\x15|\x11\x0f\x01\x00"),
        )
    )

    assert listener.mock_calls == [
        call(
            ZHAEvent(
                device_ieee=zigpy.types.EUI64.convert("ab:cd:ef:12:6d:e6:02:47"),
                unique_id="ab:cd:ef:12:6d:e6:02:47",
                data={
                    "unique_id": "ab:cd:ef:12:6d:e6:02:47:1:0xfc80_CLIENT",
                    "endpoint_id": 1,
                    "cluster_id": 64640,
                    "command": "initial_press",
                    "args": [0],
                    "params": {"new_position": 0},
                },
                event_type="zha_event",
                event="zha_event",
            )
        )
    ]


async def test_symfonisk_events(
    zha_gateway: Gateway,
) -> None:
    """Test that Symfonisk events are handled correctly."""

    zigpy_dev = await zigpy_device_from_json(
        zha_gateway.application_controller,
        "tests/data/devices/ikea-of-sweden-symfonisk-sound-remote-gen2.json",
    )

    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    listener = mock.Mock()
    zha_device.on_all_events(listener)

    # ShortcutV1Cluster:shortcut_v1_events(shortcut_button=1, shortcut_event=1)
    zigpy_dev.packet_received(
        zigpy.types.ZigbeePacket(
            src_ep=1,
            dst_ep=1,
            tsn=0,
            profile_id=260,
            cluster_id=64639,
            data=zigpy.types.SerializableBytes(b"\x15|\x11\x1f\x01\x01\x01"),
        )
    )

    assert listener.mock_calls == [
        call(
            ZHAEvent(
                device_ieee=zigpy.types.EUI64.convert("ab:cd:ef:12:52:61:2b:43"),
                unique_id="ab:cd:ef:12:52:61:2b:43",
                data={
                    "unique_id": "ab:cd:ef:12:52:61:2b:43:1:0xfc7f_CLIENT",
                    "endpoint_id": 1,
                    "cluster_id": 64639,
                    "command": "shortcut_v1_events",
                    "args": [1, 1],
                    "params": {"shortcut_button": 1, "shortcut_event": 1},
                },
                event_type="zha_event",
                event="zha_event",
            )
        )
    ]


async def test_device_on_remove_callback_failure(
    zha_gateway: Gateway,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that device.on_remove continues when callback fails."""
    zigpy_dev = await zigpy_device_from_json(
        zha_gateway.application_controller,
        "tests/data/devices/philips-sml001.json",
    )
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    failing_callback = mock.Mock(side_effect=Exception("Callback failed"))
    zha_device._on_remove_callbacks.append(failing_callback)

    await zha_device.on_remove()

    assert failing_callback.call_count == 1
    assert "Failed to execute on_remove callback" in caplog.text
    assert "Callback failed" in caplog.text


async def test_device_on_remove_platform_entity_failure(
    zha_gateway: Gateway,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that device.on_remove continues when platform entity removal fails."""
    zigpy_dev = await zigpy_device_from_json(
        zha_gateway.application_controller,
        "tests/data/devices/philips-sml001.json",
    )
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    switch_entity = get_entity(zha_device, platform=Platform.SWITCH)
    with patch.object(
        switch_entity, "on_remove", side_effect=Exception("Entity removal failed")
    ):
        await zha_device.on_remove()

    assert "Failed to remove platform entity" in caplog.text
    assert "Entity removal failed" in caplog.text


async def test_device_on_remove_pending_entity_failure(
    zha_gateway: Gateway,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that device.on_remove continues when pending entity removal fails."""
    zigpy_dev = await zigpy_device_from_json(
        zha_gateway.application_controller,
        "tests/data/devices/philips-sml001.json",
    )
    zha_device = await join_zigpy_device(zha_gateway, zigpy_dev)

    update_entity = get_entity(zha_device, platform=Platform.UPDATE)
    zha_device._pending_entities.append(update_entity)

    with patch.object(
        update_entity,
        "on_remove",
        side_effect=Exception("Pending entity removal failed"),
    ):
        await zha_device.on_remove()

    assert "Failed to remove pending entity" in caplog.text
    assert "Pending entity removal failed" in caplog.text

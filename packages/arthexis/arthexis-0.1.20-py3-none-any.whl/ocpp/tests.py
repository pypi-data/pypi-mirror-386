import os
import sys
import time
from importlib import util as importlib_util
from pathlib import Path
from types import ModuleType

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:  # pragma: no cover - exercised via test command imports
    import tests.conftest as tests_conftest  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback for pytest importlib mode
    tests_dir = Path(__file__).resolve().parents[1] / "tests"
    spec = importlib_util.spec_from_file_location(
        "tests.conftest", tests_dir / "conftest.py"
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise
    tests_conftest = importlib_util.module_from_spec(spec)
    package = sys.modules.setdefault("tests", ModuleType("tests"))
    package.__path__ = [str(tests_dir)]
    sys.modules.setdefault("tests.conftest", tests_conftest)
    spec.loader.exec_module(tests_conftest)
else:
    sys.modules.setdefault("tests.conftest", tests_conftest)

import django

django.setup = tests_conftest._original_setup
django.setup()

from asgiref.testing import ApplicationCommunicator
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from django.test import (
    Client,
    RequestFactory,
    TransactionTestCase,
    TestCase,
    override_settings,
)
from django.conf import settings
from unittest import skip
from contextlib import suppress
from types import SimpleNamespace
from unittest.mock import patch, Mock, AsyncMock
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.encoding import force_str
from django.utils.translation import override, gettext as _
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from pages.models import Application, Module
from nodes.models import Node, NodeRole

from config.asgi import application

from .models import (
    Transaction,
    Charger,
    ChargerConfiguration,
    Simulator,
    MeterReading,
    Location,
    DataTransferMessage,
)
from .consumers import CSMSConsumer
from .views import dispatch_action, _transaction_rfid_details
from .status_display import STATUS_BADGE_MAP
from core.models import EnergyAccount, EnergyCredit, Reference, RFID, SecurityGroup
from . import store
from django.db.models.deletion import ProtectedError
from decimal import Decimal
import json
import websockets
import asyncio
from .simulator import SimulatorConfig, ChargePointSimulator
from .evcs import simulate, SimulatorState, _simulators
import re
from datetime import datetime, timedelta, timezone as dt_timezone
from .tasks import purge_meter_readings, send_daily_session_report
from django.db import close_old_connections
from django.db.utils import OperationalError
from urllib.parse import unquote, urlparse


class ClientWebsocketCommunicator(WebsocketCommunicator):
    """WebsocketCommunicator that injects a client address into the scope."""

    def __init__(
        self,
        application,
        path,
        *,
        client=None,
        headers=None,
        subprotocols=None,
        spec_version=None,
    ):
        if not isinstance(path, str):
            raise TypeError(f"Expected str, got {type(path)}")
        parsed = urlparse(path)
        scope = {
            "type": "websocket",
            "path": unquote(parsed.path),
            "query_string": parsed.query.encode("utf-8"),
            "headers": headers or [],
            "subprotocols": subprotocols or [],
        }
        if client is not None:
            scope["client"] = client
        if spec_version:
            scope["spec_version"] = spec_version
        self.scope = scope
        ApplicationCommunicator.__init__(self, application, self.scope)
        self.response_headers = None


class DummyWebSocket:
    """Simple websocket stub that records payloads sent by the view."""

    def __init__(self):
        self.sent: list[str] = []

    async def send(self, message):
        self.sent.append(message)


class DispatchActionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def tearDown(self):  # pragma: no cover - cleanup guard
        store.pending_calls.clear()
        store.triggered_followups.clear()

    def test_trigger_message_registers_pending_call(self):
        charger = Charger.objects.create(charger_id="TRIGGER1")
        dummy = DummyWebSocket()
        key = store.set_connection("TRIGGER1", None, dummy)
        self.addCleanup(lambda: store.connections.pop(key, None))
        log_key = store.identity_key("TRIGGER1", None)
        store.clear_log(log_key, log_type="charger")
        self.addCleanup(lambda: store.clear_log(log_key, log_type="charger"))

        request = self.factory.post(
            "/chargers/TRIGGER1/action/",
            data=json.dumps({"action": "trigger_message", "target": "BootNotification"}),
            content_type="application/json",
        )
        request.user = SimpleNamespace(
            is_authenticated=True,
            is_superuser=True,
            is_staff=True,
        )

        response = dispatch_action(request, "TRIGGER1")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(dummy.sent)
        frame = json.loads(dummy.sent[-1])
        self.assertEqual(frame[0], 2)
        self.assertEqual(frame[2], "TriggerMessage")
        message_id = frame[1]
        self.assertIn(message_id, store.pending_calls)
        metadata = store.pending_calls[message_id]
        self.assertEqual(metadata.get("action"), "TriggerMessage")
        self.assertEqual(metadata.get("trigger_target"), "BootNotification")
        self.assertEqual(metadata.get("log_key"), log_key)

class ChargerFixtureTests(TestCase):
    fixtures = [
        p.name
        for p in (Path(__file__).resolve().parent / "fixtures").glob(
            "initial_data__*.json"
        )
    ]

    @classmethod
    def setUpTestData(cls):
        location = Location.objects.create(name="Simulator")
        Charger.objects.create(
            charger_id="CP1",
            connector_id=1,
            location=location,
            require_rfid=False,
        )
        Charger.objects.create(
            charger_id="CP2",
            connector_id=2,
            location=location,
            require_rfid=True,
        )

    def test_cp2_requires_rfid(self):
        cp2 = Charger.objects.get(charger_id="CP2")
        self.assertTrue(cp2.require_rfid)

    def test_cp1_does_not_require_rfid(self):
        cp1 = Charger.objects.get(charger_id="CP1")
        self.assertFalse(cp1.require_rfid)

    def test_charger_connector_ids(self):
        cp1 = Charger.objects.get(charger_id="CP1")
        cp2 = Charger.objects.get(charger_id="CP2")
        self.assertEqual(cp1.connector_id, 1)
        self.assertEqual(cp2.connector_id, 2)
        self.assertEqual(cp1.name, "Simulator #1")
        self.assertEqual(cp2.name, "Simulator #2")


class ChargerUrlFallbackTests(TestCase):
    @override_settings(ALLOWED_HOSTS=["fallback.example", "10.0.0.0/8"])
    def test_reference_created_when_site_missing(self):
        Site.objects.all().delete()
        Site.objects.clear_cache()

        charger = Charger.objects.create(charger_id="NO_SITE")
        charger.refresh_from_db()

        self.assertIsNotNone(charger.reference)
        self.assertTrue(charger.reference.value.startswith("http://fallback.example"))
        self.assertTrue(charger.reference.value.endswith("/c/NO_SITE/"))

    def test_reference_not_created_for_loopback_domain(self):
        site = Site.objects.get_current()
        site.domain = "127.0.0.1"
        site.save()
        Site.objects.clear_cache()

        charger = Charger.objects.create(charger_id="LOCAL_LOOP")
        charger.refresh_from_db()

        self.assertIsNone(charger.reference)


class SinkConsumerTests(TransactionTestCase):
    async def test_sink_replies(self):
        communicator = WebsocketCommunicator(application, "/ws/sink/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to([2, "1", "Foo", {}])
        response = await communicator.receive_json_from()
        self.assertEqual(response, [3, "1", {}])

        await communicator.disconnect()


class CSMSConsumerTests(TransactionTestCase):
    async def _retry_db(self, func, attempts: int = 5, delay: float = 0.1):
        """Run a database function, retrying if the database is locked."""
        for _ in range(attempts):
            try:
                return await database_sync_to_async(func)()
            except OperationalError:
                await database_sync_to_async(close_old_connections)()
                await asyncio.sleep(delay)
        raise

    async def _send_status_notification(self, serial: str, payload: dict):
        communicator = WebsocketCommunicator(application, f"/{serial}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to([2, "1", "StatusNotification", payload])
        response = await communicator.receive_json_from()
        self.assertEqual(response, [3, "1", {}])

        await communicator.disconnect()

    async def test_rejected_connection_logs_query_string(self):
        raw_serial = "<charger_id>"
        query_string = "chargeboxid=%3Ccharger_id%3E"
        pending_key = store.pending_key(Charger.normalize_serial(raw_serial))
        store.ip_connections.clear()
        store.clear_log(pending_key, log_type="charger")

        communicator = ClientWebsocketCommunicator(
            application, f"/?{query_string}"
        )

        try:
            connected = await communicator.connect()
            self.assertEqual(connected, (False, 4003))

            log_entries = store.get_logs(pending_key, log_type="charger")
            self.assertTrue(
                any(
                    "Rejected connection:" in entry and query_string in entry
                    for entry in log_entries
                ),
                log_entries,
            )
        finally:
            store.ip_connections.clear()
            store.clear_log(pending_key, log_type="charger")
            lower_key = pending_key.lower()
            for key in list(store.logs["charger"].keys()):
                if key.lower() == lower_key:
                    store.logs["charger"].pop(key, None)
            with suppress(Exception):
                await communicator.disconnect()

    async def test_transaction_saved(self):
        communicator = WebsocketCommunicator(application, "/TEST/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [
                2,
                "1",
                "StartTransaction",
                {"meterStart": 10, "connectorId": 3},
            ]
        )
        response = await communicator.receive_json_from()
        tx_id = response[2]["transactionId"]

        tx = await database_sync_to_async(Transaction.objects.get)(
            pk=tx_id, charger__charger_id="TEST"
        )
        self.assertEqual(tx.meter_start, 10)
        self.assertEqual(tx.connector_id, 3)
        self.assertIsNone(tx.stop_time)

        await communicator.send_json_to(
            [
                2,
                "2",
                "StopTransaction",
                {"transactionId": tx_id, "meterStop": 20},
            ]
        )
        await communicator.receive_json_from()

        await database_sync_to_async(tx.refresh_from_db)()
        self.assertEqual(tx.meter_stop, 20)
        self.assertIsNotNone(tx.stop_time)

        await communicator.disconnect()

    def test_status_notification_available_clears_active_session(self):
        aggregate = Charger.objects.create(charger_id="STATUSCLR")
        connector = Charger.objects.create(
            charger_id="STATUSCLR",
            connector_id=2,
        )
        tx = Transaction.objects.create(
            charger=connector,
            meter_start=10,
            start_time=timezone.now(),
        )
        store_key = store.identity_key("STATUSCLR", 2)
        store.transactions[store_key] = tx
        consumer = CSMSConsumer()
        consumer.scope = {"headers": [], "client": ("127.0.0.1", 1234)}
        consumer.charger_id = "STATUSCLR"
        consumer.store_key = store_key
        consumer.connector_value = 2
        consumer.charger = connector
        consumer.aggregate_charger = aggregate
        consumer._consumption_task = None
        consumer._consumption_message_uuid = None
        consumer.send = AsyncMock()
        payload = {
            "connectorId": 2,
            "status": "Available",
            "errorCode": "NoError",
            "transactionId": tx.pk,
        }
        try:
            with patch.object(consumer, "_assign_connector", new=AsyncMock()):
                async_to_sync(consumer.receive)(
                    text_data=json.dumps([2, "1", "StatusNotification", payload])
                )
        finally:
            store.transactions.pop(store_key, None)
        self.assertNotIn(store_key, store.transactions)

    async def test_connection_logs_subprotocol(self):
        pending_key = store.pending_key("PROT1")
        original_connections = dict(store.connections)
        original_ip_connections = {
            ip: set(consumers) for ip, consumers in store.ip_connections.items()
        }
        original_logs = {
            key: list(entries)
            for key, entries in store.logs.get("charger", {}).items()
        }
        original_log_names = dict(store.log_names.get("charger", {}))
        store.connections.clear()
        store.ip_connections.clear()
        store.clear_log(pending_key, log_type="charger")

        communicator_with_protocol = ClientWebsocketCommunicator(
            application, "/PROT1/", subprotocols=["ocpp1.6"]
        )
        communicator_with_protocol.scope["path"] = (
            communicator_with_protocol.scope.get("path", "").rstrip("/")
        )
        communicator_without_protocol = ClientWebsocketCommunicator(
            application, "/PROT1/"
        )
        communicator_without_protocol.scope["path"] = (
            communicator_without_protocol.scope.get("path", "").rstrip("/")
        )

        try:
            accepted, negotiated = await communicator_with_protocol.connect()
            logs = store.get_logs(pending_key, log_type="charger")
            self.assertTrue(accepted, negotiated)
            self.assertEqual(negotiated, "ocpp1.6")
            self.assertTrue(
                any("Connected (subprotocol=ocpp1.6)" in entry for entry in logs),
                logs,
            )

            accepted_without, negotiated_without = await communicator_without_protocol.connect()
            logs = store.get_logs(pending_key, log_type="charger")
            self.assertTrue(accepted_without, logs)
            self.assertIsNone(negotiated_without)
            self.assertTrue(
                any("Connected (subprotocol=none)" in entry for entry in logs),
                logs,
            )
        finally:
            with suppress(Exception):
                await communicator_without_protocol.disconnect()
            with suppress(Exception):
                await communicator_with_protocol.disconnect()
            store.connections.clear()
            store.connections.update(original_connections)
            store.ip_connections.clear()
            for ip, consumers in original_ip_connections.items():
                store.ip_connections[ip] = set(consumers)
            store.logs.setdefault("charger", {})
            store.logs["charger"].clear()
            for key, entries in original_logs.items():
                store.logs["charger"][key] = list(entries)
            store.log_names.setdefault("charger", {})
            store.log_names["charger"].clear()
            store.log_names["charger"].update(original_log_names)

    async def test_rfid_recorded(self):
        await database_sync_to_async(Charger.objects.create)(charger_id="RFIDREC")
        communicator = WebsocketCommunicator(application, "/RFIDREC/?cid=RFIDREC")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [2, "1", "StartTransaction", {"meterStart": 1, "idTag": "TAG123"}]
        )
        response = await communicator.receive_json_from()
        tx_id = response[2]["transactionId"]

        tx = await database_sync_to_async(Transaction.objects.get)(
            pk=tx_id, charger__charger_id="RFIDREC"
        )
        self.assertEqual(tx.rfid, "TAG123")

        tag = await database_sync_to_async(RFID.objects.get)(rfid="TAG123")
        self.assertTrue(tag.allowed)
        self.assertIsNotNone(tag.last_seen_on)

        await communicator.disconnect()

    async def test_start_transaction_uses_payload_timestamp(self):
        communicator = WebsocketCommunicator(application, "/STAMPED/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        start_ts = datetime(2025, 9, 26, 18, 1, tzinfo=dt_timezone.utc)
        before = timezone.now()
        await communicator.send_json_to(
            [
                2,
                "1",
                "StartTransaction",
                {"meterStart": 5, "timestamp": start_ts.isoformat()},
            ]
        )
        response = await communicator.receive_json_from()
        after = timezone.now()
        tx_id = response[2]["transactionId"]

        tx = await database_sync_to_async(Transaction.objects.get)(
            pk=tx_id, charger__charger_id="STAMPED"
        )
        self.assertEqual(tx.start_time, start_ts)
        self.assertIsNotNone(tx.received_start_time)
        self.assertGreaterEqual(tx.received_start_time, before)
        self.assertLessEqual(tx.received_start_time, after)

        await communicator.disconnect()

    async def test_stop_transaction_uses_payload_timestamp(self):
        communicator = WebsocketCommunicator(application, "/STOPSTAMP/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [
                2,
                "1",
                "StartTransaction",
                {"meterStart": 10},
            ]
        )
        response = await communicator.receive_json_from()
        tx_id = response[2]["transactionId"]

        stop_ts = datetime(2025, 9, 26, 18, 5, tzinfo=dt_timezone.utc)
        before = timezone.now()
        await communicator.send_json_to(
            [
                2,
                "2",
                "StopTransaction",
                {
                    "transactionId": tx_id,
                    "meterStop": 20,
                    "timestamp": stop_ts.isoformat(),
                },
            ]
        )
        await communicator.receive_json_from()
        after = timezone.now()

        tx = await database_sync_to_async(Transaction.objects.get)(
            pk=tx_id, charger__charger_id="STOPSTAMP"
        )
        self.assertEqual(tx.stop_time, stop_ts)
        self.assertIsNotNone(tx.received_stop_time)
        self.assertGreaterEqual(tx.received_stop_time, before)
        self.assertLessEqual(tx.received_stop_time, after)

        await communicator.disconnect()

    async def test_start_transaction_sends_net_message(self):
        location = await database_sync_to_async(Location.objects.create)(
            name="Test Location"
        )
        await database_sync_to_async(Charger.objects.create)(
            charger_id="NETMSG", location=location
        )
        communicator = WebsocketCommunicator(application, "/NETMSG/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        with patch("nodes.models.NetMessage.broadcast") as mock_broadcast:
            await communicator.send_json_to(
                [
                    2,
                    "1",
                    "StartTransaction",
                    {"meterStart": 1, "connectorId": 1},
                ]
            )
            await communicator.receive_json_from()

        await communicator.disconnect()

        mock_broadcast.assert_called_once()
        _, kwargs = mock_broadcast.call_args
        self.assertEqual(kwargs["subject"], "NETMSG")
        body = kwargs["body"]
        self.assertRegex(body, r"^\d+\.\d kWh \d{2}:\d{2}$")

    async def test_consumption_message_updates_existing_entry(self):
        original_interval = CSMSConsumer.consumption_update_interval
        CSMSConsumer.consumption_update_interval = 0.01
        await database_sync_to_async(Charger.objects.create)(charger_id="UPDATEMSG")
        communicator = WebsocketCommunicator(application, "/UPDATEMSG/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        message_mock = Mock()
        message_mock.uuid = "mock-uuid"
        message_mock.save = Mock()
        message_mock.propagate = Mock()

        filter_mock = Mock()
        filter_mock.first.return_value = message_mock

        broadcast_result = SimpleNamespace(uuid="mock-uuid")

        try:
            with patch(
                "nodes.models.NetMessage.broadcast", return_value=broadcast_result
            ) as mock_broadcast, patch(
                "nodes.models.NetMessage.objects.filter", return_value=filter_mock
            ):
                await communicator.send_json_to(
                    [2, "1", "StartTransaction", {"meterStart": 1}]
                )
                await communicator.receive_json_from()
                mock_broadcast.assert_called_once()
                await asyncio.sleep(0.05)
                await communicator.disconnect()
        finally:
            CSMSConsumer.consumption_update_interval = original_interval
            with suppress(Exception):
                await communicator.disconnect()

        self.assertTrue(message_mock.save.called)
        self.assertTrue(message_mock.propagate.called)

    async def test_assign_connector_promotes_pending_connection(self):
        serial = "ASSIGNPROMOTE"
        path = f"/{serial}/"
        pending_key = store.pending_key(serial)
        new_key = store.identity_key(serial, 1)
        aggregate_key = store.identity_key(serial, None)

        store.connections.pop(pending_key, None)
        store.connections.pop(new_key, None)
        store.logs["charger"].pop(new_key, None)
        store.log_names["charger"].pop(new_key, None)
        store.log_names["charger"].pop(aggregate_key, None)

        aggregate = await database_sync_to_async(Charger.objects.create)(
            charger_id=serial,
            connector_id=None,
        )

        consumer = CSMSConsumer()
        consumer.scope = {"path": path, "headers": [], "client": ("127.0.0.1", 1234)}
        consumer.charger_id = serial
        consumer.store_key = pending_key
        consumer.connector_value = None
        consumer.client_ip = "127.0.0.1"
        consumer.charger = aggregate
        consumer.aggregate_charger = aggregate

        store.connections[pending_key] = consumer

        try:
            with patch.object(Charger, "refresh_manager_node", autospec=True) as mock_refresh:
                mock_refresh.return_value = None
                await consumer._assign_connector(1)

            self.assertEqual(consumer.store_key, new_key)
            self.assertNotIn(pending_key, store.connections)

            connector = await database_sync_to_async(Charger.objects.get)(
                charger_id=serial,
                connector_id=1,
            )
            self.assertEqual(consumer.charger.pk, connector.pk)
            self.assertEqual(consumer.charger.connector_id, 1)
            self.assertIsNone(consumer.aggregate_charger.connector_id)

            self.assertIn(new_key, store.log_names["charger"])
            self.assertIn(aggregate_key, store.log_names["charger"])

            self.assertNotIn(pending_key, store.connections)
        finally:
            store.connections.pop(new_key, None)
            store.connections.pop(pending_key, None)
            store.logs["charger"].pop(new_key, None)
            store.log_names["charger"].pop(new_key, None)
            store.log_names["charger"].pop(aggregate_key, None)
            await database_sync_to_async(Charger.objects.filter(charger_id=serial).delete)()

    async def test_change_availability_result_updates_model(self):
        store.pending_calls.clear()
        communicator = WebsocketCommunicator(application, "/AVAILRES/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [
                2,
                "boot",
                "BootNotification",
                {"chargePointVendor": "Test", "chargePointModel": "Model"},
            ]
        )
        await communicator.receive_json_from()

        message_id = "ca-result"
        requested_at = timezone.now()
        store.register_pending_call(
            message_id,
            {
                "action": "ChangeAvailability",
                "charger_id": "AVAILRES",
                "connector_id": None,
                "availability_type": "Inoperative",
                "requested_at": requested_at,
            },
        )
        await communicator.send_json_to([3, message_id, {"status": "Accepted"}])
        await asyncio.sleep(0.05)

        charger = await database_sync_to_async(Charger.objects.get)(
            charger_id="AVAILRES", connector_id=None
        )
        self.assertEqual(charger.availability_state, "Inoperative")
        self.assertEqual(charger.availability_request_status, "Accepted")
        self.assertEqual(charger.availability_requested_state, "Inoperative")
        await communicator.disconnect()

    async def test_get_configuration_result_logged(self):
        store.pending_calls.clear()
        pending_key = store.pending_key("CFGRES")
        store.clear_log(pending_key, log_type="charger")
        log_key = store.identity_key("CFGRES", None)
        store.clear_log(log_key, log_type="charger")
        communicator = WebsocketCommunicator(application, "/CFGRES/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await database_sync_to_async(Charger.objects.get_or_create)(
            charger_id="CFGRES", connector_id=1
        )
        await database_sync_to_async(Charger.objects.get_or_create)(
            charger_id="CFGRES", connector_id=2
        )

        message_id = "cfg-result"
        payload = {
            "configurationKey": [
                {
                    "key": "AllowOfflineTxForUnknownId",
                    "readonly": True,
                    "value": "false",
                }
            ]
        }
        store.register_pending_call(
            message_id,
            {
                "action": "GetConfiguration",
                "charger_id": "CFGRES",
                "connector_id": None,
                "log_key": log_key,
                "requested_at": timezone.now(),
            },
        )

        await communicator.send_json_to([3, message_id, payload])
        await asyncio.sleep(0.05)

        log_entries = store.get_logs(log_key, log_type="charger")
        self.assertTrue(
            any("GetConfiguration result" in entry for entry in log_entries)
        )
        self.assertNotIn(message_id, store.pending_calls)

        configuration = await database_sync_to_async(
            lambda: ChargerConfiguration.objects.order_by("-created_at").first()
        )()
        self.assertIsNotNone(configuration)
        self.assertEqual(configuration.charger_identifier, "CFGRES")
        self.assertEqual(
            configuration.configuration_keys,
            [
                {
                    "key": "AllowOfflineTxForUnknownId",
                    "value": "false",
                    "readonly": True,
                }
            ],
        )
        self.assertEqual(configuration.unknown_keys, [])
        config_ids = await database_sync_to_async(
            lambda: set(
                Charger.objects.filter(charger_id="CFGRES").values_list(
                    "configuration_id", flat=True
                )
            )
        )()
        self.assertEqual(config_ids, {configuration.pk})

        await communicator.disconnect()
        store.clear_log(log_key, log_type="charger")
        store.clear_log(pending_key, log_type="charger")

    async def test_get_configuration_error_logged(self):
        store.pending_calls.clear()
        pending_key = store.pending_key("CFGERR")
        store.clear_log(pending_key, log_type="charger")
        log_key = store.identity_key("CFGERR", None)
        store.clear_log(log_key, log_type="charger")
        communicator = WebsocketCommunicator(application, "/CFGERR/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        message_id = "cfg-error"
        store.register_pending_call(
            message_id,
            {
                "action": "GetConfiguration",
                "charger_id": "CFGERR",
                "connector_id": None,
                "log_key": log_key,
                "requested_at": timezone.now(),
            },
        )

        await communicator.send_json_to(
            [4, message_id, "InternalError", "Boom", {"detail": "nope"}]
        )
        await asyncio.sleep(0.05)

        log_entries = store.get_logs(log_key, log_type="charger")
        self.assertTrue(
            any("GetConfiguration error" in entry for entry in log_entries)
        )
        self.assertNotIn(message_id, store.pending_calls)

        await communicator.disconnect()
        store.clear_log(log_key, log_type="charger")
        store.clear_log(pending_key, log_type="charger")

    async def test_trigger_message_follow_up_logged(self):
        store.pending_calls.clear()
        cid = "TRIGLOG"
        pending_key = store.pending_key(cid)
        log_key = store.identity_key(cid, None)
        store.clear_log(pending_key, log_type="charger")
        store.clear_log(log_key, log_type="charger")

        communicator = WebsocketCommunicator(application, f"/{cid}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [
                2,
                "boot",
                "BootNotification",
                {"chargePointVendor": "Test", "chargePointModel": "Model"},
            ]
        )
        await communicator.receive_json_from()

        message_id = "trigger-result"
        store.register_pending_call(
            message_id,
            {
                "action": "TriggerMessage",
                "charger_id": cid,
                "connector_id": None,
                "log_key": log_key,
                "trigger_target": "BootNotification",
                "trigger_connector": None,
            },
        )

        await communicator.send_json_to([3, message_id, {"status": "Accepted"}])
        await asyncio.sleep(0.05)
        self.assertNotIn(message_id, store.pending_calls)

        log_entries = store.get_logs(log_key, log_type="charger")
        self.assertTrue(
            any(
                "TriggerMessage BootNotification result" in entry
                or "TriggerMessage result" in entry
                for entry in log_entries
            )
        )

        await communicator.send_json_to(
            [
                2,
                "trigger-follow",
                "BootNotification",
                {"chargePointVendor": "Test", "chargePointModel": "Model"},
            ]
        )
        await communicator.receive_json_from()
        await asyncio.sleep(0.05)

        log_entries = store.get_logs(log_key, log_type="charger")
        self.assertTrue(
            any(
                "TriggerMessage follow-up received: BootNotification" in entry
                for entry in log_entries
            )
        )

        await communicator.disconnect()
        store.clear_log(log_key, log_type="charger")
        store.clear_log(pending_key, log_type="charger")

    async def test_status_notification_updates_availability_state(self):
        store.pending_calls.clear()
        communicator = WebsocketCommunicator(application, "/STATAVAIL/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [
                2,
                "boot",
                "BootNotification",
                {"chargePointVendor": "Test", "chargePointModel": "Model"},
            ]
        )
        await communicator.receive_json_from()

        await communicator.send_json_to(
            [
                2,
                "stat1",
                "StatusNotification",
                {"connectorId": 1, "errorCode": "NoError", "status": "Unavailable"},
            ]
        )
        await communicator.receive_json_from()

        charger = await database_sync_to_async(Charger.objects.get)(
            charger_id="STATAVAIL", connector_id=1
        )
        self.assertEqual(charger.availability_state, "Inoperative")

        await communicator.send_json_to(
            [
                2,
                "stat2",
                "StatusNotification",
                {"connectorId": 1, "errorCode": "NoError", "status": "Available"},
            ]
        )
        await communicator.receive_json_from()

        charger = await database_sync_to_async(Charger.objects.get)(
            charger_id="STATAVAIL", connector_id=1
        )
        self.assertEqual(charger.availability_state, "Operative")
        await communicator.disconnect()

    async def test_consumption_message_final_update_on_disconnect(self):
        await database_sync_to_async(Charger.objects.create)(charger_id="FINALMSG")
        communicator = WebsocketCommunicator(application, "/FINALMSG/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        message_mock = Mock()
        message_mock.uuid = "mock-uuid"
        message_mock.save = Mock()
        message_mock.propagate = Mock()

        filter_mock = Mock()
        filter_mock.first.return_value = message_mock

        broadcast_result = SimpleNamespace(uuid="mock-uuid")

        try:
            with patch(
                "nodes.models.NetMessage.broadcast", return_value=broadcast_result
            ) as mock_broadcast, patch(
                "nodes.models.NetMessage.objects.filter", return_value=filter_mock
            ):
                await communicator.send_json_to(
                    [2, "1", "StartTransaction", {"meterStart": 1}]
                )
                await communicator.receive_json_from()
                mock_broadcast.assert_called_once()
                await communicator.disconnect()
        finally:
            with suppress(Exception):
                await communicator.disconnect()

        self.assertTrue(message_mock.save.called)
        self.assertTrue(message_mock.propagate.called)

    async def test_rfid_unbound_instance_created(self):
        await database_sync_to_async(Charger.objects.create)(charger_id="NEWRFID")
        communicator = WebsocketCommunicator(application, "/NEWRFID/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [2, "1", "StartTransaction", {"meterStart": 1, "idTag": "TAG456"}]
        )
        await communicator.receive_json_from()

        tag = await database_sync_to_async(RFID.objects.get)(rfid="TAG456")
        count = await database_sync_to_async(tag.energy_accounts.count)()
        self.assertEqual(count, 0)

        await communicator.disconnect()

    async def test_firmware_status_notification_updates_database_and_views(self):
        communicator = WebsocketCommunicator(application, "/FWSTAT/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        ts = timezone.now().replace(microsecond=0)
        payload = {
            "status": "Installing",
            "statusInfo": "Applying patch",
            "timestamp": ts.isoformat(),
        }

        await communicator.send_json_to(
            [2, "1", "FirmwareStatusNotification", payload]
        )
        response = await communicator.receive_json_from()
        self.assertEqual(response, [3, "1", {}])

        def _fetch_status():
            charger = Charger.objects.get(charger_id="FWSTAT", connector_id=None)
            return (
                charger.firmware_status,
                charger.firmware_status_info,
                charger.firmware_timestamp,
            )

        status, info, recorded_ts = await database_sync_to_async(_fetch_status)()
        self.assertEqual(status, "Installing")
        self.assertEqual(info, "Applying patch")
        self.assertIsNotNone(recorded_ts)
        self.assertEqual(recorded_ts.replace(microsecond=0), ts)

        log_entries = store.get_logs(store.identity_key("FWSTAT", None), log_type="charger")
        self.assertTrue(
            any("FirmwareStatusNotification" in entry for entry in log_entries)
        )

        def _fetch_views():
            User = get_user_model()
            user = User.objects.create_user(username="fwstatus", password="pw")
            client = Client()
            client.force_login(user)
            detail = client.get(reverse("charger-detail", args=["FWSTAT"]))
            status_page = client.get(reverse("charger-status", args=["FWSTAT"]))
            list_response = client.get(reverse("charger-list"))
            return (
                detail.status_code,
                json.loads(detail.content.decode()),
                status_page.status_code,
                status_page.content.decode(),
                list_response.status_code,
                json.loads(list_response.content.decode()),
            )

        (
            detail_code,
            detail_payload,
            status_code,
            html,
            list_code,
            list_payload,
        ) = await database_sync_to_async(_fetch_views)()
        self.assertEqual(detail_code, 200)
        self.assertEqual(status_code, 200)
        self.assertEqual(list_code, 200)
        self.assertEqual(detail_payload["firmwareStatus"], "Installing")
        self.assertEqual(detail_payload["firmwareStatusInfo"], "Applying patch")
        self.assertEqual(detail_payload["firmwareTimestamp"], ts.isoformat())
        self.assertNotIn('id="firmware-status"', html)
        self.assertNotIn('id="firmware-status-info"', html)
        self.assertNotIn('id="firmware-timestamp"', html)

        matching = [
            item
            for item in list_payload.get("chargers", [])
            if item["charger_id"] == "FWSTAT" and item["connector_id"] is None
        ]
        self.assertTrue(matching)
        self.assertEqual(matching[0]["firmwareStatus"], "Installing")
        self.assertEqual(matching[0]["firmwareStatusInfo"], "Applying patch")
        list_ts = datetime.fromisoformat(matching[0]["firmwareTimestamp"])
        self.assertAlmostEqual(list_ts.timestamp(), ts.timestamp(), places=3)

        store.clear_log(store.identity_key("FWSTAT", None), log_type="charger")

        await communicator.disconnect()

    async def test_firmware_status_notification_updates_connector_and_aggregate(
        self,
    ):
        communicator = WebsocketCommunicator(application, "/FWCONN/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [
                2,
                "1",
                "FirmwareStatusNotification",
                {"connectorId": 2, "status": "Downloaded"},
            ]
        )
        response = await communicator.receive_json_from()
        self.assertEqual(response, [3, "1", {}])

        def _fetch_chargers():
            aggregate = Charger.objects.get(charger_id="FWCONN", connector_id=None)
            connector = Charger.objects.get(charger_id="FWCONN", connector_id=2)
            return (
                aggregate.firmware_status,
                aggregate.firmware_status_info,
                aggregate.firmware_timestamp,
                connector.firmware_status,
                connector.firmware_status_info,
                connector.firmware_timestamp,
            )

        (
            aggregate_status,
            aggregate_info,
            aggregate_ts,
            connector_status,
            connector_info,
            connector_ts,
        ) = await database_sync_to_async(_fetch_chargers)()

        self.assertEqual(aggregate_status, "Downloaded")
        self.assertEqual(connector_status, "Downloaded")
        self.assertEqual(aggregate_info, "")
        self.assertEqual(connector_info, "")
        self.assertIsNotNone(aggregate_ts)
        self.assertIsNotNone(connector_ts)
        self.assertAlmostEqual(
            (connector_ts - aggregate_ts).total_seconds(), 0, delta=1.0
        )

        log_entries = store.get_logs(
            store.identity_key("FWCONN", 2), log_type="charger"
        )
        self.assertTrue(
            any("FirmwareStatusNotification" in entry for entry in log_entries)
        )
        log_entries_agg = store.get_logs(
            store.identity_key("FWCONN", None), log_type="charger"
        )
        self.assertTrue(
            any("FirmwareStatusNotification" in entry for entry in log_entries_agg)
        )

        store.clear_log(store.identity_key("FWCONN", 2), log_type="charger")
        store.clear_log(store.identity_key("FWCONN", None), log_type="charger")

        await communicator.disconnect()

    async def test_vid_populated_from_vin(self):
        await database_sync_to_async(Charger.objects.create)(charger_id="VINREC")
        communicator = WebsocketCommunicator(application, "/VINREC/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [2, "1", "StartTransaction", {"meterStart": 1, "vin": "WP0ZZZ11111111111"}]
        )
        response = await communicator.receive_json_from()
        tx_id = response[2]["transactionId"]

        tx = await database_sync_to_async(Transaction.objects.get)(
            pk=tx_id, charger__charger_id="VINREC"
        )
        self.assertEqual(tx.vid, "WP0ZZZ11111111111")
        self.assertEqual(tx.vehicle_identifier, "WP0ZZZ11111111111")
        self.assertEqual(tx.vehicle_identifier_source, "vid")

        await communicator.disconnect()

    async def test_vid_recorded(self):
        await database_sync_to_async(Charger.objects.create)(charger_id="VIDREC")
        communicator = WebsocketCommunicator(application, "/VIDREC/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [2, "1", "StartTransaction", {"meterStart": 1, "vid": "VID123456"}]
        )
        response = await communicator.receive_json_from()
        tx_id = response[2]["transactionId"]

        tx = await database_sync_to_async(Transaction.objects.get)(
            pk=tx_id, charger__charger_id="VIDREC"
        )
        self.assertEqual(tx.vid, "VID123456")
        self.assertEqual(tx.rfid, "")

        await communicator.disconnect()

    async def test_connector_id_set_from_meter_values(self):
        communicator = WebsocketCommunicator(application, "/NEWCID/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        payload = {
            "connectorId": 7,
            "meterValue": [
                {
                    "timestamp": timezone.now().isoformat(),
                    "sampledValue": [{"value": "1"}],
                }
            ],
        }
        await communicator.send_json_to([2, "1", "MeterValues", payload])
        await communicator.receive_json_from()

        charger = await database_sync_to_async(Charger.objects.get)(
            charger_id="NEWCID", connector_id=7
        )
        self.assertEqual(charger.connector_id, 7)

        await communicator.disconnect()

    async def test_new_charger_created_for_different_connector(self):
        communicator = WebsocketCommunicator(application, "/DUPC/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        payload1 = {
            "connectorId": 1,
            "meterValue": [
                {
                    "timestamp": timezone.now().isoformat(),
                    "sampledValue": [{"value": "1"}],
                }
            ],
        }
        await communicator.send_json_to([2, "1", "MeterValues", payload1])
        await communicator.receive_json_from()
        await communicator.disconnect()
        await communicator.wait()
        await database_sync_to_async(close_old_connections)()

        communicator = WebsocketCommunicator(application, "/DUPC/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        payload2 = {
            "connectorId": 2,
            "meterValue": [
                {
                    "timestamp": timezone.now().isoformat(),
                    "sampledValue": [{"value": "1"}],
                }
            ],
        }
        await communicator.send_json_to([2, "1", "MeterValues", payload2])
        await communicator.receive_json_from()
        await communicator.disconnect()
        await communicator.wait()
        await database_sync_to_async(close_old_connections)()

        count = await self._retry_db(
            lambda: Charger.objects.filter(charger_id="DUPC").count()
        )
        self.assertEqual(count, 3)
        connectors = await self._retry_db(
            lambda: list(
                Charger.objects.filter(charger_id="DUPC").values_list(
                    "connector_id", flat=True
                )
            )
        )
        self.assertIn(1, connectors)
        self.assertIn(2, connectors)
        self.assertIn(None, connectors)

    async def test_console_reference_created_for_aggregate_connector(self):
        communicator = ClientWebsocketCommunicator(
            application,
            "/CONREF/",
            client=("203.0.113.5", 12345),
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to([2, "1", "BootNotification", {}])
        await communicator.receive_json_from()

        reference = await database_sync_to_async(
            lambda: Reference.objects.get(alt_text="CONREF Console")
        )()
        self.assertEqual(reference.value, "http://203.0.113.5:8900")
        self.assertTrue(reference.show_in_header)

        await communicator.send_json_to(
            [
                2,
                "2",
                "StatusNotification",
                {"connectorId": 1, "status": "Available"},
            ]
        )
        await communicator.receive_json_from()

        count = await database_sync_to_async(
            lambda: Reference.objects.filter(alt_text="CONREF Console").count()
        )()
        self.assertEqual(count, 1)

        await communicator.disconnect()

    async def test_console_reference_uses_forwarded_for_header(self):
        communicator = ClientWebsocketCommunicator(
            application,
            "/FORWARDED/",
            client=("127.0.0.1", 23456),
            headers=[(b"x-forwarded-for", b"198.51.100.75, 127.0.0.1")],
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        self.assertIn("198.51.100.75", store.ip_connections)

        await communicator.send_json_to([2, "1", "BootNotification", {}])
        await communicator.receive_json_from()

        reference = await database_sync_to_async(
            lambda: Reference.objects.get(alt_text="FORWARDED Console")
        )()
        self.assertEqual(reference.value, "http://198.51.100.75:8900")

        await communicator.disconnect()

    async def test_console_reference_skips_loopback_ip(self):
        communicator = ClientWebsocketCommunicator(
            application,
            "/LOCAL/",
            client=("127.0.0.1", 34567),
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to([2, "1", "BootNotification", {}])
        await communicator.receive_json_from()

        exists = await database_sync_to_async(
            lambda: Reference.objects.filter(alt_text="LOCAL Console").exists()
        )()
        self.assertFalse(exists)

        await communicator.disconnect()

    async def test_transaction_created_from_meter_values(self):
        communicator = WebsocketCommunicator(application, "/NOSTART/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [
                2,
                "1",
                "MeterValues",
                {
                    "transactionId": 99,
                    "meterValue": [
                        {
                            "timestamp": "2025-01-01T00:00:00Z",
                            "sampledValue": [
                                {
                                    "value": "1000",
                                    "measurand": "Energy.Active.Import.Register",
                                    "unit": "W",
                                }
                            ],
                        }
                    ],
                },
            ]
        )
        await communicator.receive_json_from()

        tx = await database_sync_to_async(Transaction.objects.get)(
            pk=99, charger__charger_id="NOSTART"
        )
        self.assertEqual(tx.meter_start, 1000)
        self.assertIsNone(tx.meter_stop)

        await communicator.send_json_to(
            [
                2,
                "2",
                "StopTransaction",
                {"transactionId": 99, "meterStop": 1500},
            ]
        )
        await communicator.receive_json_from()
        await database_sync_to_async(tx.refresh_from_db)()
        self.assertEqual(tx.meter_stop, 1500)
        self.assertIsNotNone(tx.stop_time)

        await communicator.disconnect()

    async def test_diagnostics_status_notification_updates_records(self):
        communicator = WebsocketCommunicator(application, "/DIAGCP/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        reported_at = timezone.now().replace(microsecond=0)
        payload = {
            "status": "Uploaded",
            "connectorId": 5,
            "uploadLocation": "https://example.com/diag.tar",
            "timestamp": reported_at.isoformat(),
        }

        await communicator.send_json_to(
            [2, "1", "DiagnosticsStatusNotification", payload]
        )
        response = await communicator.receive_json_from()
        self.assertEqual(response[0], 3)
        self.assertEqual(response[2], {})

        def _fetch():
            aggregate = Charger.objects.get(charger_id="DIAGCP", connector_id=None)
            connector = Charger.objects.get(charger_id="DIAGCP", connector_id=5)
            return aggregate, connector

        aggregate, connector = await database_sync_to_async(_fetch)()
        self.assertEqual(aggregate.diagnostics_status, "Uploaded")
        self.assertEqual(connector.diagnostics_status, "Uploaded")
        self.assertEqual(
            aggregate.diagnostics_location, "https://example.com/diag.tar"
        )
        self.assertEqual(
            connector.diagnostics_location, "https://example.com/diag.tar"
        )
        self.assertEqual(aggregate.diagnostics_timestamp, reported_at)
        self.assertEqual(connector.diagnostics_timestamp, reported_at)

        connector_logs = store.get_logs(
            store.identity_key("DIAGCP", 5), log_type="charger"
        )
        aggregate_logs = store.get_logs(
            store.identity_key("DIAGCP", None), log_type="charger"
        )
        self.assertTrue(
            any("DiagnosticsStatusNotification" in entry for entry in connector_logs)
        )
        self.assertTrue(
            any("DiagnosticsStatusNotification" in entry for entry in aggregate_logs)
        )

        await communicator.disconnect()

    async def test_temperature_recorded(self):
        charger = await database_sync_to_async(Charger.objects.create)(
            charger_id="TEMP1"
        )
        communicator = WebsocketCommunicator(application, "/TEMP1/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [
                2,
                "1",
                "MeterValues",
                {
                    "meterValue": [
                        {
                            "timestamp": "2025-01-01T00:00:00Z",
                            "sampledValue": [
                                {
                                    "value": "42",
                                    "measurand": "Temperature",
                                    "unit": "Celsius",
                                }
                            ],
                        }
                    ]
                },
            ]
        )
        await communicator.receive_json_from()

        await database_sync_to_async(charger.refresh_from_db)()
        self.assertEqual(charger.temperature, Decimal("42"))
        self.assertEqual(charger.temperature_unit, "Celsius")

        await communicator.disconnect()

    def test_status_notification_updates_models_and_views(self):
        serial = "STATUS-CP"
        payload = {
            "connectorId": 1,
            "status": "Faulted",
            "errorCode": "GroundFailure",
            "info": "Relay malfunction",
            "vendorId": "ACME",
            "timestamp": "2024-01-01T12:34:56Z",
        }

        async_to_sync(self._send_status_notification)(serial, payload)

        expected_ts = parse_datetime(payload["timestamp"])
        aggregate = Charger.objects.get(charger_id=serial, connector_id=None)
        connector = Charger.objects.get(charger_id=serial, connector_id=1)

        vendor_data = {"info": payload["info"], "vendorId": payload["vendorId"]}
        self.assertEqual(aggregate.last_status, payload["status"])
        self.assertEqual(aggregate.last_error_code, payload["errorCode"])
        self.assertEqual(aggregate.last_status_vendor_info, vendor_data)
        self.assertEqual(aggregate.last_status_timestamp, expected_ts)
        self.assertEqual(connector.last_status, payload["status"])
        self.assertEqual(connector.last_error_code, payload["errorCode"])
        self.assertEqual(connector.last_status_vendor_info, vendor_data)
        self.assertEqual(connector.last_status_timestamp, expected_ts)

        connector_log = store.get_logs(
            store.identity_key(serial, 1), log_type="charger"
        )
        self.assertTrue(
            any("StatusNotification processed" in entry for entry in connector_log)
        )

        user = get_user_model().objects.create_user(
            username="status", email="status@example.com", password="pwd"
        )
        self.client.force_login(user)

        list_response = self.client.get(reverse("charger-list"))
        self.assertEqual(list_response.status_code, 200)
        chargers = list_response.json()["chargers"]
        aggregate_entry = next(
            item
            for item in chargers
            if item["charger_id"] == serial and item["connector_id"] is None
        )
        connector_entry = next(
            item
            for item in chargers
            if item["charger_id"] == serial and item["connector_id"] == 1
        )
        expected_iso = expected_ts.isoformat()
        self.assertEqual(aggregate_entry["lastStatus"], payload["status"])
        self.assertEqual(aggregate_entry["lastErrorCode"], payload["errorCode"])
        self.assertEqual(aggregate_entry["lastStatusVendorInfo"], vendor_data)
        self.assertEqual(aggregate_entry["lastStatusTimestamp"], expected_iso)
        self.assertEqual(aggregate_entry["status"], "Faulted (GroundFailure)")
        self.assertEqual(aggregate_entry["statusColor"], "#dc3545")
        self.assertEqual(connector_entry["lastStatus"], payload["status"])
        self.assertEqual(connector_entry["lastErrorCode"], payload["errorCode"])
        self.assertEqual(connector_entry["lastStatusVendorInfo"], vendor_data)
        self.assertEqual(connector_entry["lastStatusTimestamp"], expected_iso)
        self.assertEqual(connector_entry["status"], "Faulted (GroundFailure)")
        self.assertEqual(connector_entry["statusColor"], "#dc3545")

        detail_response = self.client.get(
            reverse("charger-detail-connector", args=[serial, 1])
        )
        self.assertEqual(detail_response.status_code, 200)
        detail_payload = detail_response.json()
        self.assertEqual(detail_payload["lastStatus"], payload["status"])
        self.assertEqual(detail_payload["lastErrorCode"], payload["errorCode"])
        self.assertEqual(detail_payload["lastStatusVendorInfo"], vendor_data)
        self.assertEqual(detail_payload["lastStatusTimestamp"], expected_iso)
        self.assertEqual(detail_payload["status"], "Faulted (GroundFailure)")
        self.assertEqual(detail_payload["statusColor"], "#dc3545")

        status_resp = self.client.get(
            reverse("charger-status-connector", args=[serial, "1"])
        )
        self.assertContains(status_resp, "Faulted (GroundFailure)")
        self.assertContains(status_resp, "Error code: GroundFailure")
        self.assertContains(status_resp, "Vendor: ACME")
        self.assertContains(status_resp, "Info: Relay malfunction")
        self.assertContains(status_resp, "background-color: #dc3545")

        aggregate_status = self.client.get(reverse("charger-status", args=[serial]))
        self.assertContains(
            aggregate_status,
            f"Serial Number: {serial}",
        )
        self.assertNotContains(aggregate_status, 'id="last-status-raw"')
        self.assertContains(aggregate_status, "Info: Relay malfunction")

        page_resp = self.client.get(reverse("charger-page", args=[serial]))
        self.assertContains(page_resp, "Faulted (GroundFailure)")
        self.assertContains(page_resp, "Vendor")
        self.assertContains(page_resp, "Relay malfunction")
        self.assertContains(page_resp, "background-color: #dc3545")

        store.clear_log(store.identity_key(serial, 1), log_type="charger")
        store.clear_log(store.identity_key(serial, None), log_type="charger")

    async def test_message_logged_and_session_file_created(self):
        cid = "LOGTEST1"
        log_path = Path("logs") / f"charger.{cid}.log"
        if log_path.exists():
            log_path.unlink()
        session_dir = Path("logs") / "sessions" / cid
        if session_dir.exists():
            for f in session_dir.glob("*.json"):
                f.unlink()
        communicator = WebsocketCommunicator(application, f"/{cid}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [
                2,
                "1",
                "StartTransaction",
                {"meterStart": 1},
            ]
        )
        response = await communicator.receive_json_from()
        tx_id = response[2]["transactionId"]

        await communicator.send_json_to(
            [
                2,
                "2",
                "StopTransaction",
                {"transactionId": tx_id, "meterStop": 2},
            ]
        )
        await communicator.receive_json_from()
        await communicator.disconnect()

        content = log_path.read_text()
        self.assertIn("StartTransaction", content)
        self.assertNotIn(">", content)

        files = list(session_dir.glob(f"*_{tx_id}.json"))
        self.assertEqual(len(files), 1)
        data = json.loads(files[0].read_text())
        self.assertTrue(any("StartTransaction" in m["message"] for m in data))

    async def test_binary_message_logged(self):
        cid = "BINARY1"
        log_path = Path("logs") / f"charger.{cid}.log"
        if log_path.exists():
            log_path.unlink()
        communicator = WebsocketCommunicator(application, f"/{cid}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_to(bytes_data=b"\x01\x02\x03")
        await communicator.disconnect()

        content = log_path.read_text()
        self.assertIn("AQID", content)

    async def test_session_file_written_on_disconnect(self):
        cid = "LOGTEST2"
        log_path = Path("logs") / f"charger.{cid}.log"
        if log_path.exists():
            log_path.unlink()
        session_dir = Path("logs") / "sessions" / cid
        if session_dir.exists():
            for f in session_dir.glob("*.json"):
                f.unlink()
        communicator = WebsocketCommunicator(application, f"/{cid}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [
                2,
                "1",
                "StartTransaction",
                {"meterStart": 5},
            ]
        )
        await communicator.receive_json_from()

        await communicator.disconnect()

        session_dir = Path("logs") / "sessions" / cid
        files = list(session_dir.glob("*.json"))
        self.assertEqual(len(files), 1)
        data = json.loads(files[0].read_text())
        self.assertTrue(any("StartTransaction" in m["message"] for m in data))

    async def test_second_connection_closes_first(self):
        communicator1 = WebsocketCommunicator(application, "/DUPLICATE/")
        connected, _ = await communicator1.connect()
        self.assertTrue(connected)
        pending_key = store.pending_key("DUPLICATE")
        first_consumer = store.connections.get(pending_key)

        communicator2 = WebsocketCommunicator(application, "/DUPLICATE/")
        connected2, _ = await communicator2.connect()
        self.assertTrue(connected2)

        # The first communicator should be closed when the second connects.
        await communicator1.wait()
        self.assertIsNot(store.connections.get(pending_key), first_consumer)

        await communicator2.disconnect()

    async def test_connectors_share_serial_without_disconnecting(self):
        communicator1 = WebsocketCommunicator(application, "/MULTI/")
        connected1, _ = await communicator1.connect()
        self.assertTrue(connected1)
        await communicator1.send_json_to(
            [
                2,
                "1",
                "StartTransaction",
                {"connectorId": 1, "meterStart": 10},
            ]
        )
        await communicator1.receive_json_from()

        communicator2 = WebsocketCommunicator(application, "/MULTI/")
        connected2, _ = await communicator2.connect()
        self.assertTrue(connected2)
        await communicator2.send_json_to(
            [
                2,
                "2",
                "StartTransaction",
                {"connectorId": 2, "meterStart": 10},
            ]
        )
        await communicator2.receive_json_from()

        key1 = store.identity_key("MULTI", 1)
        key2 = store.identity_key("MULTI", 2)
        self.assertIn(key1, store.connections)
        self.assertIn(key2, store.connections)
        self.assertIsNot(store.connections[key1], store.connections[key2])

        await communicator1.disconnect()
        await communicator2.disconnect()
        store.transactions.pop(key1, None)
        store.transactions.pop(key2, None)


    async def test_rate_limit_blocks_third_connection(self):
        store.ip_connections.clear()
        ip = "203.0.113.10"
        communicator1 = ClientWebsocketCommunicator(
            application, "/IPLIMIT1/", client=(ip, 1001)
        )
        communicator2 = ClientWebsocketCommunicator(
            application, "/IPLIMIT2/", client=(ip, 1002)
        )
        communicator3 = ClientWebsocketCommunicator(
            application, "/IPLIMIT3/", client=(ip, 1003)
        )
        other = ClientWebsocketCommunicator(
            application, "/OTHERIP/", client=("198.51.100.5", 2001)
        )
        connected1 = connected2 = connected_other = False
        try:
            connected1, _ = await communicator1.connect()
            self.assertTrue(connected1)
            connected2, _ = await communicator2.connect()
            self.assertTrue(connected2)
            connected3, code = await communicator3.connect()
            self.assertFalse(connected3)
            self.assertEqual(code, 4003)
            connected_other, _ = await other.connect()
            self.assertTrue(connected_other)
        finally:
            if connected1:
                await communicator1.disconnect()
            if connected2:
                await communicator2.disconnect()
            if connected_other:
                await other.disconnect()

    async def test_rate_limit_allows_reconnect_after_disconnect(self):
        store.ip_connections.clear()
        ip = "203.0.113.20"
        communicator1 = ClientWebsocketCommunicator(
            application, "/LIMITRESET1/", client=(ip, 3001)
        )
        communicator2 = ClientWebsocketCommunicator(
            application, "/LIMITRESET2/", client=(ip, 3002)
        )
        communicator3 = ClientWebsocketCommunicator(
            application, "/LIMITRESET3/", client=(ip, 3003)
        )
        communicator3_retry = None
        connected1 = connected2 = connected3_retry = False
        try:
            connected1, _ = await communicator1.connect()
            self.assertTrue(connected1)
            connected2, _ = await communicator2.connect()
            self.assertTrue(connected2)
            connected3, code = await communicator3.connect()
            self.assertFalse(connected3)
            self.assertEqual(code, 4003)
            await communicator1.disconnect()
            connected1 = False
            communicator3_retry = ClientWebsocketCommunicator(
                application, "/LIMITRESET4/", client=(ip, 3004)
            )
            connected3_retry, _ = await communicator3_retry.connect()
            self.assertTrue(connected3_retry)
        finally:
            if connected1:
                await communicator1.disconnect()
            if connected2:
                await communicator2.disconnect()
            if connected3_retry and communicator3_retry is not None:
                await communicator3_retry.disconnect()

    async def test_data_transfer_inbound_persists_message(self):
        store.pending_calls.clear()
        communicator = WebsocketCommunicator(application, "/DTIN/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        payload = {"vendorId": "Acme", "messageId": "diag", "data": {"foo": "bar"}}
        await communicator.send_json_to([2, "dt-msg", "DataTransfer", payload])
        response = await communicator.receive_json_from()
        self.assertEqual(response, [3, "dt-msg", {"status": "UnknownVendorId"}])

        await communicator.disconnect()

        message = await database_sync_to_async(DataTransferMessage.objects.get)(
            ocpp_message_id="dt-msg"
        )
        self.assertEqual(
            message.direction, DataTransferMessage.DIRECTION_CP_TO_CSMS
        )
        self.assertEqual(message.vendor_id, "Acme")
        self.assertEqual(message.message_id, "diag")
        self.assertEqual(message.payload, payload)
        self.assertEqual(message.status, "UnknownVendorId")
        self.assertIsNotNone(message.responded_at)

    async def test_data_transfer_action_round_trip(self):
        store.pending_calls.clear()
        communicator = WebsocketCommunicator(application, "/DTOUT/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        User = get_user_model()
        user = await database_sync_to_async(User.objects.create_user)(
            username="dtuser", password="pw"
        )
        await database_sync_to_async(self.client.force_login)(user)

        url = reverse("charger-action", args=["DTOUT"])
        request_payload = {
            "action": "data_transfer",
            "vendorId": "AcmeCorp",
            "messageId": "ping",
            "data": {"echo": "value"},
        }
        response = await database_sync_to_async(self.client.post)(
            url,
            data=json.dumps(request_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response_body = json.loads(response.content.decode())
        sent_frame = json.loads(response_body["sent"])
        self.assertEqual(sent_frame[2], "DataTransfer")
        sent_payload = sent_frame[3]
        self.assertEqual(sent_payload["vendorId"], "AcmeCorp")
        self.assertEqual(sent_payload.get("messageId"), "ping")

        outbound = await communicator.receive_json_from()
        self.assertEqual(outbound, sent_frame)

        message_id = sent_frame[1]
        record = await database_sync_to_async(DataTransferMessage.objects.get)(
            ocpp_message_id=message_id
        )
        self.assertEqual(
            record.direction, DataTransferMessage.DIRECTION_CSMS_TO_CP
        )
        self.assertEqual(record.status, "Pending")
        self.assertIsNone(record.response_data)
        self.assertIn(message_id, store.pending_calls)
        self.assertEqual(store.pending_calls[message_id]["message_pk"], record.pk)

        reply_payload = {"status": "Accepted", "data": {"result": "ok"}}
        await communicator.send_json_to([3, message_id, reply_payload])
        await asyncio.sleep(0.05)

        updated = await database_sync_to_async(DataTransferMessage.objects.get)(
            pk=record.pk
        )
        self.assertEqual(updated.status, "Accepted")
        self.assertEqual(updated.response_data, {"result": "ok"})
        self.assertIsNotNone(updated.responded_at)
        self.assertNotIn(message_id, store.pending_calls)

        await communicator.disconnect()


class ChargerLandingTests(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(username="u", password="pwd")
        self.client.force_login(self.user)

    def test_reference_created_and_page_renders(self):
        charger = Charger.objects.create(charger_id="PAGE1")
        self.assertIsNotNone(charger.reference)

        response = self.client.get(reverse("charger-page", args=["PAGE1"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["LANGUAGE_CODE"], "es")
        with override("es"):
            self.assertContains(
                response,
                _(
                    "Plug in your vehicle and slide your RFID card over the reader to begin charging."
                ),
            )
            self.assertContains(response, _("Advanced View"))
        status_url = reverse("charger-status-connector", args=["PAGE1", "all"])
        self.assertContains(response, status_url)

    def test_charger_page_respects_language_configuration(self):
        charger = Charger.objects.create(charger_id="PAGE-DE", language="de")

        response = self.client.get(reverse("charger-page", args=["PAGE-DE"]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["LANGUAGE_CODE"], "de")
        self.assertContains(response, 'lang="de"')
        self.assertContains(response, 'data-preferred-language="de"')

    def test_status_page_renders(self):
        charger = Charger.objects.create(charger_id="PAGE2")
        resp = self.client.get(reverse("charger-status", args=["PAGE2"]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "PAGE2")

    def test_placeholder_serial_rejected(self):
        with self.assertRaises(ValidationError):
            Charger.objects.create(charger_id="<charger_id>")

    def test_placeholder_serial_not_created_from_status_view(self):
        existing = Charger.objects.count()
        response = self.client.get(reverse("charger-status", args=["<charger_id>"]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Charger.objects.count(), existing)
        self.assertFalse(
            Location.objects.filter(
                name__startswith="<", name__endswith=">", chargers__isnull=True
            ).exists()
        )

    def test_charger_page_shows_progress(self):
        charger = Charger.objects.create(charger_id="STATS")
        tx = Transaction.objects.create(
            charger=charger,
            meter_start=1000,
            start_time=timezone.now(),
        )
        key = store.identity_key(charger.charger_id, charger.connector_id)
        store.transactions[key] = tx
        resp = self.client.get(reverse("charger-page", args=["STATS"]))
        self.assertContains(resp, "progress-bar")
        store.transactions.pop(key, None)

    def test_public_page_overrides_available_status_when_charging(self):
        charger = Charger.objects.create(
            charger_id="STATEPUB",
            last_status="Available",
        )
        tx = Transaction.objects.create(
            charger=charger,
            meter_start=1000,
            start_time=timezone.now(),
        )
        key = store.identity_key(charger.charger_id, charger.connector_id)
        store.transactions[key] = tx
        try:
            response = self.client.get(reverse("charger-page", args=["STATEPUB"]))
            self.assertEqual(response.status_code, 200)
            self.assertContains(
                response,
                'class="badge" style="background-color: #198754;">Charging</span>',
            )
        finally:
            store.transactions.pop(key, None)

    def test_admin_status_overrides_available_status_when_charging(self):
        charger = Charger.objects.create(
            charger_id="STATEADM",
            last_status="Available",
        )
        tx = Transaction.objects.create(
            charger=charger,
            meter_start=1000,
            start_time=timezone.now(),
        )
        key = store.identity_key(charger.charger_id, charger.connector_id)
        store.transactions[key] = tx
        try:
            response = self.client.get(reverse("charger-status", args=["STATEADM"]))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'id="charger-state">Charging</strong>')
            self.assertContains(
                response,
                'style="width:20px;height:20px;background-color: #198754;"',
            )
        finally:
            store.transactions.pop(key, None)

    def test_public_page_shows_available_when_status_stale(self):
        charger = Charger.objects.create(
            charger_id="STALEPUB",
            last_status="Charging",
        )
        response = self.client.get(reverse("charger-page", args=["STALEPUB"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'style="background-color: #0d6efd; color: #fff;">Available</span>',
        )

    def test_admin_status_shows_available_when_status_stale(self):
        charger = Charger.objects.create(
            charger_id="STALEADM",
            last_status="Charging",
        )
        response = self.client.get(reverse("charger-status", args=["STALEADM"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="charger-state">Available</strong>')

    def test_public_status_shows_rfid_link_for_known_tag(self):
        aggregate = Charger.objects.create(charger_id="PUBRFID")
        connector = Charger.objects.create(
            charger_id="PUBRFID",
            connector_id=1,
        )
        tx = Transaction.objects.create(
            charger=connector,
            meter_start=1000,
            start_time=timezone.now(),
            rfid="TAGLINK",
        )
        key = store.identity_key(connector.charger_id, connector.connector_id)
        store.transactions[key] = tx
        tag = RFID.objects.create(rfid="TAGLINK")
        admin_url = reverse("admin:core_rfid_change", args=[tag.pk])
        try:
            response = self.client.get(
                reverse(
                    "charger-page-connector",
                    args=[connector.charger_id, connector.connector_slug],
                )
            )
            self.assertContains(response, admin_url)
            self.assertContains(response, "TAGLINK")

            overview = self.client.get(reverse("charger-page", args=[aggregate.charger_id]))
            self.assertContains(overview, admin_url)
        finally:
            store.transactions.pop(key, None)

    def test_public_status_shows_rfid_text_when_unknown(self):
        Charger.objects.create(charger_id="PUBTEXT")
        connector = Charger.objects.create(
            charger_id="PUBTEXT",
            connector_id=1,
        )
        tx = Transaction.objects.create(
            charger=connector,
            meter_start=1000,
            start_time=timezone.now(),
            rfid="TAGNONE",
        )
        key = store.identity_key(connector.charger_id, connector.connector_id)
        store.transactions[key] = tx
        try:
            response = self.client.get(
                reverse(
                    "charger-page-connector",
                    args=[connector.charger_id, connector.connector_slug],
                )
            )
            self.assertContains(response, "TAGNONE")
            self.assertNotContains(response, "TAGNONE</a>")

            overview = self.client.get(reverse("charger-page", args=[connector.charger_id]))
            self.assertContains(overview, "TAGNONE")
        finally:
            store.transactions.pop(key, None)

    def test_display_name_used_on_public_pages(self):
        charger = Charger.objects.create(
            charger_id="NAMED",
            display_name="Entrada",
        )
        landing = self.client.get(reverse("charger-page", args=["NAMED"]))
        self.assertContains(landing, "Entrada")
        status = self.client.get(
            reverse("charger-status-connector", args=["NAMED", "all"])
        )
        self.assertContains(status, "Entrada")

    def test_total_includes_ongoing_transaction(self):
        charger = Charger.objects.create(charger_id="ONGOING")
        tx = Transaction.objects.create(
            charger=charger,
            meter_start=1000,
            start_time=timezone.now(),
        )
        key = store.identity_key(charger.charger_id, charger.connector_id)
        store.transactions[key] = tx
        MeterReading.objects.create(
            charger=charger,
            transaction=tx,
            timestamp=timezone.now(),
            measurand="Energy.Active.Import.Register",
            value=Decimal("2500"),
            unit="W",
        )
        resp = self.client.get(reverse("charger-status", args=["ONGOING"]))
        self.assertContains(resp, 'Total Energy: <span id="total-kw">1.50</span> kW')
        store.transactions.pop(key, None)

    def test_connector_specific_routes_render(self):
        Charger.objects.create(charger_id="ROUTED")
        connector = Charger.objects.create(charger_id="ROUTED", connector_id=1)
        page = self.client.get(reverse("charger-page-connector", args=["ROUTED", "1"]))
        self.assertEqual(page.status_code, 200)
        status = self.client.get(
            reverse("charger-status-connector", args=["ROUTED", "1"])
        )
        self.assertEqual(status.status_code, 200)
        search = self.client.get(
            reverse("charger-session-search-connector", args=["ROUTED", "1"])
        )
        self.assertEqual(search.status_code, 200)
        log_id = store.identity_key("ROUTED", connector.connector_id)
        store.add_log(log_id, "entry", log_type="charger")
        log = self.client.get(
            reverse("charger-log-connector", args=["ROUTED", "1"]) + "?type=charger"
        )
        self.assertContains(log, "entry")
        store.clear_log(log_id, log_type="charger")

    def test_temperature_displayed(self):
        charger = Charger.objects.create(
            charger_id="TEMP2", temperature=Decimal("21.5"), temperature_unit="Celsius"
        )
        resp = self.client.get(reverse("charger-status", args=["TEMP2"]))
        self.assertContains(resp, "Temperature")
        self.assertContains(resp, "21.5")

    def test_log_page_renders_without_charger(self):
        log_id = store.identity_key("LOG1", None)
        store.add_log(log_id, "hello", log_type="charger")
        entry = store.get_logs(log_id, log_type="charger")[0]
        self.assertRegex(
            entry,
            r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} hello$",
        )
        resp = self.client.get(reverse("charger-log", args=["LOG1"]) + "?type=charger")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "hello")
        store.clear_log(log_id, log_type="charger")

    def test_log_page_is_case_insensitive(self):
        log_id = store.identity_key("cp2", None)
        store.add_log(log_id, "entry", log_type="charger")
        resp = self.client.get(reverse("charger-log", args=["CP2"]) + "?type=charger")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "entry")
        store.clear_log(log_id, log_type="charger")


class SimulatorLandingTests(TestCase):
    def setUp(self):
        role, _ = NodeRole.objects.get_or_create(name="Terminal")
        Node.objects.update_or_create(
            mac_address=Node.get_current_mac(),
            defaults={"hostname": "localhost", "address": "127.0.0.1", "role": role},
        )
        Site.objects.update_or_create(
            id=1, defaults={"domain": "testserver", "name": ""}
        )
        app = Application.objects.create(name="Ocpp")
        module = Module.objects.create(node_role=role, application=app, path="/ocpp/")
        module.create_landings()
        User = get_user_model()
        self.user = User.objects.create_user(username="nav", password="pwd")
        self.client = Client()

    @skip("Navigation links unavailable in test environment")
    def test_simulator_app_link_in_nav(self):
        resp = self.client.get(reverse("pages:index"))
        self.assertContains(resp, "/ocpp/cpms/dashboard/")
        self.assertNotContains(resp, "/ocpp/evcs/simulator/")
        self.client.force_login(self.user)
        resp = self.client.get(reverse("pages:index"))
        self.assertContains(resp, "/ocpp/cpms/dashboard/")
        self.assertContains(resp, "/ocpp/evcs/simulator/")

    def test_cp_simulator_redirects_to_login(self):
        response = self.client.get(reverse("cp-simulator"))
        login_url = reverse("pages:login")
        self.assertEqual(response.status_code, 302)
        self.assertIn(login_url, response.url)


class ChargerAdminTests(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username="ocpp-admin", password="secret", email="admin@example.com"
        )
        self.client.force_login(self.admin)

    def test_admin_lists_landing_link(self):
        charger = Charger.objects.create(charger_id="ADMIN1")
        url = reverse("admin:ocpp_charger_changelist")
        resp = self.client.get(url)
        self.assertContains(resp, charger.get_absolute_url())
        status_url = reverse("charger-status-connector", args=["ADMIN1", "all"])
        self.assertContains(resp, status_url)

    def test_admin_does_not_list_qr_link(self):
        charger = Charger.objects.create(charger_id="QR1")
        url = reverse("admin:ocpp_charger_changelist")
        resp = self.client.get(url)
        self.assertNotContains(resp, charger.reference.image.url)

    def test_toggle_rfid_authentication_action_toggles_value(self):
        charger_requires = Charger.objects.create(
            charger_id="RFIDON", require_rfid=True
        )
        charger_optional = Charger.objects.create(
            charger_id="RFIDOFF", require_rfid=False
        )
        url = reverse("admin:ocpp_charger_changelist")
        response = self.client.post(
            url,
            {
                "action": "toggle_rfid_authentication",
                "_selected_action": [
                    charger_requires.pk,
                    charger_optional.pk,
                ],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        charger_requires.refresh_from_db()
        charger_optional.refresh_from_db()
        self.assertFalse(charger_requires.require_rfid)
        self.assertTrue(charger_optional.require_rfid)
        self.assertContains(response, "Updated RFID authentication")

    def test_admin_lists_log_link(self):
        charger = Charger.objects.create(charger_id="LOG1")
        url = reverse("admin:ocpp_charger_changelist")
        resp = self.client.get(url)
        log_url = reverse("admin:ocpp_charger_log", args=[charger.pk])
        self.assertContains(resp, log_url)

    def test_admin_status_overrides_available_when_active_session(self):
        charger = Charger.objects.create(
            charger_id="ADMINCHARGE",
            last_status="Available",
        )
        tx = Transaction.objects.create(
            charger=charger,
            start_time=timezone.now(),
        )
        key = store.identity_key(charger.charger_id, charger.connector_id)
        store.transactions[key] = tx
        try:
            url = reverse("admin:ocpp_charger_changelist")
            resp = self.client.get(url)
            charging_label = force_str(STATUS_BADGE_MAP["charging"][0])
            self.assertContains(resp, f">{charging_label}<")
        finally:
            store.transactions.pop(key, None)

    def test_admin_status_shows_available_when_status_stale(self):
        charger = Charger.objects.create(
            charger_id="ADMINSTALE",
            last_status="Charging",
        )
        url = reverse("admin:ocpp_charger_changelist")
        resp = self.client.get(url)
        available_label = force_str(STATUS_BADGE_MAP["available"][0])
        self.assertContains(resp, f">{available_label}<")

    def test_recheck_charger_status_action_sends_trigger(self):
        charger = Charger.objects.create(charger_id="RECHECK1")

        class DummyConnection:
            def __init__(self):
                self.sent: list[str] = []

            async def send(self, message):
                self.sent.append(message)

        ws = DummyConnection()
        store.set_connection(charger.charger_id, charger.connector_id, ws)
        try:
            url = reverse("admin:ocpp_charger_changelist")
            response = self.client.post(
                url,
                {
                    "action": "recheck_charger_status",
                    "index": 0,
                    "select_across": 0,
                    "_selected_action": [charger.pk],
                },
                follow=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(ws.sent)
            self.assertIn("TriggerMessage", ws.sent[0])
            self.assertContains(response, "Requested status update")
        finally:
            store.pop_connection(charger.charger_id, charger.connector_id)
            store.clear_pending_calls(charger.charger_id)

    def test_admin_log_view_displays_entries(self):
        charger = Charger.objects.create(charger_id="LOG2")
        log_id = store.identity_key(charger.charger_id, charger.connector_id)
        store.add_log(log_id, "entry", log_type="charger")
        url = reverse("admin:ocpp_charger_log", args=[charger.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "entry")
        store.clear_log(log_id, log_type="charger")

    def test_admin_change_links_landing_page(self):
        charger = Charger.objects.create(charger_id="CHANGE1")
        url = reverse("admin:ocpp_charger_change", args=[charger.pk])
        resp = self.client.get(url)
        self.assertContains(resp, charger.get_absolute_url())

    def test_admin_shows_location_name(self):
        loc = Location.objects.create(name="AdminLoc")
        Charger.objects.create(charger_id="ADMINLOC", location=loc)
        url = reverse("admin:ocpp_charger_changelist")
        resp = self.client.get(url)
        self.assertContains(resp, "AdminLoc")

    def test_last_fields_are_read_only(self):
        now = timezone.now()
        charger = Charger.objects.create(
            charger_id="ADMINRO",
            last_heartbeat=now,
            last_meter_values={"a": 1},
        )
        url = reverse("admin:ocpp_charger_change", args=[charger.pk])
        resp = self.client.get(url)
        self.assertContains(resp, "Last heartbeat")
        self.assertContains(resp, "Last meter values")
        self.assertNotContains(resp, 'name="last_heartbeat"')
        self.assertNotContains(resp, 'name="last_meter_values"')

    def test_admin_action_sets_availability_state(self):
        charger = Charger.objects.create(charger_id="AVAIL1")
        url = reverse("admin:ocpp_charger_changelist")
        response = self.client.post(
            url,
            {
                "action": "set_availability_state_inoperative",
                "_selected_action": [charger.pk],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        charger.refresh_from_db()
        self.assertEqual(charger.availability_state, "Inoperative")
        self.assertIsNotNone(charger.availability_state_updated_at)

        response = self.client.post(
            url,
            {
                "action": "set_availability_state_operative",
                "_selected_action": [charger.pk],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        charger.refresh_from_db()
        self.assertEqual(charger.availability_state, "Operative")
        self.assertIsNotNone(charger.availability_state_updated_at)

    def test_purge_action_removes_data(self):
        charger = Charger.objects.create(charger_id="PURGE1")
        Transaction.objects.create(
            charger=charger,
            start_time=timezone.now(),
        )
        MeterReading.objects.create(
            charger=charger,
            timestamp=timezone.now(),
            value=1,
        )
        store.add_log(store.identity_key("PURGE1", None), "entry", log_type="charger")
        url = reverse("admin:ocpp_charger_changelist")
        self.client.post(
            url, {"action": "purge_data", "_selected_action": [charger.pk]}
        )
        self.assertFalse(Transaction.objects.filter(charger=charger).exists())
        self.assertFalse(MeterReading.objects.filter(charger=charger).exists())
        self.assertNotIn(store.identity_key("PURGE1", None), store.logs["charger"])

    def test_delete_requires_purge(self):
        charger = Charger.objects.create(charger_id="DEL1")
        Transaction.objects.create(
            charger=charger,
            start_time=timezone.now(),
        )
        delete_url = reverse("admin:ocpp_charger_delete", args=[charger.pk])
        with self.assertRaises(ProtectedError):
            self.client.post(delete_url, {"post": "yes"})
        self.assertTrue(Charger.objects.filter(pk=charger.pk).exists())
        url = reverse("admin:ocpp_charger_changelist")
        self.client.post(
            url, {"action": "purge_data", "_selected_action": [charger.pk]}
        )
        self.client.post(delete_url, {"post": "yes"})
        self.assertFalse(Charger.objects.filter(pk=charger.pk).exists())

    def test_fetch_configuration_dispatches_request(self):
        charger = Charger.objects.create(charger_id="CFGADMIN", connector_id=1)
        ws = DummyWebSocket()
        log_key = store.identity_key(charger.charger_id, charger.connector_id)
        store.clear_log(log_key, log_type="charger")
        pending_key = store.pending_key(charger.charger_id)
        store.clear_log(pending_key, log_type="charger")
        store.set_connection(charger.charger_id, charger.connector_id, ws)
        store.pending_calls.clear()
        try:
            url = reverse("admin:ocpp_charger_changelist")
            response = self.client.post(
                url,
                {
                    "action": "fetch_cp_configuration",
                    "_selected_action": [charger.pk],
                },
                follow=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(ws.sent), 1)
            frame = json.loads(ws.sent[0])
            self.assertEqual(frame[0], 2)
            self.assertEqual(frame[2], "GetConfiguration")
            self.assertIn(frame[1], store.pending_calls)
            metadata = store.pending_calls[frame[1]]
            self.assertEqual(metadata.get("action"), "GetConfiguration")
            self.assertEqual(metadata.get("charger_id"), charger.charger_id)
            self.assertEqual(metadata.get("connector_id"), charger.connector_id)
            self.assertEqual(metadata.get("log_key"), log_key)
            log_entries = store.get_logs(log_key, log_type="charger")
            self.assertTrue(
                any("GetConfiguration" in entry for entry in log_entries)
            )
        finally:
            store.pop_connection(charger.charger_id, charger.connector_id)
            store.pending_calls.clear()
            store.clear_log(log_key, log_type="charger")
            store.clear_log(pending_key, log_type="charger")

    def test_fetch_configuration_timeout_logged(self):
        charger = Charger.objects.create(charger_id="CFGWAIT", connector_id=1)
        ws = DummyWebSocket()
        log_key = store.identity_key(charger.charger_id, charger.connector_id)
        pending_key = store.pending_key(charger.charger_id)
        store.clear_log(log_key, log_type="charger")
        store.clear_log(pending_key, log_type="charger")
        store.set_connection(charger.charger_id, charger.connector_id, ws)
        store.pending_calls.clear()
        original_schedule = store.schedule_call_timeout
        try:
            with patch("ocpp.admin.store.schedule_call_timeout") as mock_schedule:
                def _side_effect(message_id, *, timeout=5.0, **kwargs):
                    kwargs["timeout"] = 0.05
                    return original_schedule(message_id, **kwargs)

                mock_schedule.side_effect = _side_effect
                url = reverse("admin:ocpp_charger_changelist")
                response = self.client.post(
                    url,
                    {
                        "action": "fetch_cp_configuration",
                        "_selected_action": [charger.pk],
                    },
                    follow=True,
                )
                self.assertEqual(response.status_code, 200)
                mock_schedule.assert_called_once()
            time.sleep(0.1)
            log_entries = store.get_logs(log_key, log_type="charger")
            self.assertTrue(
                any("GetConfiguration timed out" in entry for entry in log_entries)
            )
        finally:
            store.pop_connection(charger.charger_id, charger.connector_id)
            store.pending_calls.clear()
            store.clear_log(log_key, log_type="charger")
            store.clear_log(pending_key, log_type="charger")

    def test_remote_stop_action_dispatches_request(self):
        charger = Charger.objects.create(charger_id="STOPME", connector_id=1)
        ws = DummyWebSocket()
        log_key = store.identity_key(charger.charger_id, charger.connector_id)
        pending_key = store.pending_key(charger.charger_id)
        store.clear_log(log_key, log_type="charger")
        store.clear_log(pending_key, log_type="charger")
        store.set_connection(charger.charger_id, charger.connector_id, ws)
        tx = Transaction.objects.create(
            charger=charger,
            start_time=timezone.now(),
        )
        tx_key = store.identity_key(charger.charger_id, charger.connector_id)
        store.transactions[tx_key] = tx
        store.pending_calls.clear()
        try:
            url = reverse("admin:ocpp_charger_changelist")
            response = self.client.post(
                url,
                {
                    "action": "remote_stop_transaction",
                    "_selected_action": [charger.pk],
                },
                follow=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(ws.sent), 1)
            frame = json.loads(ws.sent[0])
            self.assertEqual(frame[0], 2)
            self.assertEqual(frame[2], "RemoteStopTransaction")
            self.assertIn("transactionId", frame[3])
            self.assertEqual(frame[3]["transactionId"], tx.pk)
            self.assertIn(frame[1], store.pending_calls)
            metadata = store.pending_calls[frame[1]]
            self.assertEqual(metadata.get("action"), "RemoteStopTransaction")
            self.assertEqual(metadata.get("charger_id"), charger.charger_id)
            self.assertEqual(metadata.get("connector_id"), charger.connector_id)
            self.assertEqual(metadata.get("transaction_id"), tx.pk)
            self.assertEqual(metadata.get("log_key"), log_key)
            log_entries = store.get_logs(log_key, log_type="charger")
            self.assertTrue(
                any("RemoteStopTransaction" in entry for entry in log_entries)
            )
        finally:
            store.pop_connection(charger.charger_id, charger.connector_id)
            store.pending_calls.clear()
            store.transactions.pop(tx_key, None)
            store.clear_log(log_key, log_type="charger")
            store.clear_log(pending_key, log_type="charger")

    def test_reset_action_dispatches_request(self):
        charger = Charger.objects.create(charger_id="RESETME", connector_id=1)
        ws = DummyWebSocket()
        log_key = store.identity_key(charger.charger_id, charger.connector_id)
        pending_key = store.pending_key(charger.charger_id)
        store.clear_log(log_key, log_type="charger")
        store.clear_log(pending_key, log_type="charger")
        store.set_connection(charger.charger_id, charger.connector_id, ws)
        store.pending_calls.clear()
        try:
            url = reverse("admin:ocpp_charger_changelist")
            response = self.client.post(
                url,
                {
                    "action": "reset_chargers",
                    "_selected_action": [charger.pk],
                },
                follow=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(ws.sent), 1)
            frame = json.loads(ws.sent[0])
            self.assertEqual(frame[0], 2)
            self.assertEqual(frame[2], "Reset")
            self.assertEqual(frame[3], {"type": "Soft"})
            self.assertIn(frame[1], store.pending_calls)
            metadata = store.pending_calls[frame[1]]
            self.assertEqual(metadata.get("action"), "Reset")
            self.assertEqual(metadata.get("charger_id"), charger.charger_id)
            self.assertEqual(metadata.get("connector_id"), charger.connector_id)
            self.assertEqual(metadata.get("log_key"), log_key)
            log_entries = store.get_logs(log_key, log_type="charger")
            self.assertTrue(any("Reset" in entry for entry in log_entries))
        finally:
            store.pop_connection(charger.charger_id, charger.connector_id)
            store.pending_calls.clear()
            store.clear_log(log_key, log_type="charger")
            store.clear_log(pending_key, log_type="charger")


class LocationAdminTests(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username="loc-admin", password="secret", email="loc@example.com"
        )
        self.client.force_login(self.admin)

    def test_change_form_lists_related_chargers(self):
        location = Location.objects.create(name="LocAdmin")
        base = Charger.objects.create(charger_id="LOCBASE", location=location)
        connector = Charger.objects.create(
            charger_id="LOCALTWO",
            connector_id=1,
            location=location,
        )

        url = reverse("admin:ocpp_location_change", args=[location.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        base_change_url = reverse("admin:ocpp_charger_change", args=[base.pk])
        connector_change_url = reverse("admin:ocpp_charger_change", args=[connector.pk])

        self.assertContains(resp, base_change_url)
        self.assertContains(resp, connector_change_url)
        self.assertContains(resp, f"Charge Point: {base.charger_id}")
        self.assertContains(resp, f"Charge Point: {connector.charger_id} #1")


class TransactionAdminTests(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username="tx-admin", password="secret", email="tx@example.com"
        )
        self.client.force_login(self.admin)

    def test_meter_readings_inline_displayed(self):
        charger = Charger.objects.create(charger_id="T1")
        tx = Transaction.objects.create(charger=charger, start_time=timezone.now())
        reading = MeterReading.objects.create(
            charger=charger,
            transaction=tx,
            timestamp=timezone.now(),
            value=Decimal("2.123"),
            unit="kW",
        )
        url = reverse("admin:ocpp_transaction_change", args=[tx.pk])
        resp = self.client.get(url)
        self.assertContains(resp, str(reading.value))


class SimulatorAdminTests(TransactionTestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username="admin2", password="secret", email="admin2@example.com"
        )
        self.client.force_login(self.admin)
        store.simulators.clear()
        store.logs["simulator"].clear()
        store.log_names["simulator"].clear()

    def test_admin_lists_log_link(self):
        sim = Simulator.objects.create(name="SIM", cp_path="SIMX")
        url = reverse("admin:ocpp_simulator_changelist")
        resp = self.client.get(url)
        log_url = reverse("admin:ocpp_simulator_log", args=[sim.pk])
        self.assertContains(resp, log_url)

    def test_admin_log_view_displays_entries(self):
        sim = Simulator.objects.create(name="SIMLOG", cp_path="SIMLOG")
        store.add_log("SIMLOG", "entry", log_type="simulator")
        url = reverse("admin:ocpp_simulator_log", args=[sim.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "entry")
        store.clear_log("SIMLOG", log_type="simulator")

    @patch("ocpp.admin.ChargePointSimulator.start")
    def test_start_simulator_message_includes_log_link(self, mock_start):
        sim = Simulator.objects.create(name="SIMMSG", cp_path="SIMMSG")
        mock_start.return_value = (True, "Connection accepted", "/tmp/sim.log")
        url = reverse("admin:ocpp_simulator_changelist")
        resp = self.client.post(
            url,
            {"action": "start_simulator", "_selected_action": [sim.pk]},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        log_url = reverse("admin:ocpp_simulator_log", args=[sim.pk])
        self.assertContains(resp, "View Log")
        self.assertContains(resp, log_url)
        self.assertContains(resp, "/tmp/sim.log")
        mock_start.assert_called_once()
        store.simulators.clear()

    @patch("ocpp.admin.ChargePointSimulator.start")
    def test_start_simulator_change_action(self, mock_start):
        sim = Simulator.objects.create(name="SIMCHG", cp_path="SIMCHG")
        mock_start.return_value = (True, "Started", "/tmp/log")
        resp = self._post_simulator_change(
            sim,
            _action="start_simulator_action",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "View Log")
        self.assertContains(resp, "/tmp/log")
        mock_start.assert_called_once()
        store.simulators.clear()

    def test_admin_shows_ws_url(self):
        sim = Simulator.objects.create(
            name="SIM2", cp_path="SIMY", host="h", ws_port=1111
        )
        url = reverse("admin:ocpp_simulator_changelist")
        resp = self.client.get(url)
        self.assertContains(resp, "ws://h:1111/SIMY/")

    def test_admin_ws_url_without_port(self):
        sim = Simulator.objects.create(
            name="SIMNP", cp_path="SIMNP", host="h", ws_port=None
        )
        url = reverse("admin:ocpp_simulator_changelist")
        resp = self.client.get(url)
        self.assertContains(resp, "ws://h/SIMNP/")

    def test_send_open_door_action_requires_running_simulator(self):
        sim = Simulator.objects.create(name="SIMDO", cp_path="SIMDO")
        url = reverse("admin:ocpp_simulator_changelist")
        resp = self.client.post(
            url,
            {"action": "send_open_door", "_selected_action": [sim.pk]},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "simulator is not running")
        self.assertFalse(Simulator.objects.get(pk=sim.pk).door_open)

    def test_send_open_door_action_triggers_simulator(self):
        sim = Simulator.objects.create(name="SIMTRIG", cp_path="SIMTRIG")
        stub = SimpleNamespace(trigger_door_open=Mock())
        store.simulators[sim.pk] = stub
        url = reverse("admin:ocpp_simulator_changelist")
        resp = self.client.post(
            url,
            {"action": "send_open_door", "_selected_action": [sim.pk]},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        stub.trigger_door_open.assert_called_once()
        self.assertContains(resp, "DoorOpen status notification sent")
        self.assertFalse(Simulator.objects.get(pk=sim.pk).door_open)
        store.simulators.pop(sim.pk, None)

    @patch("ocpp.admin.asyncio.get_running_loop", side_effect=RuntimeError)
    def test_stop_simulator_runs_without_event_loop(self, mock_get_loop):
        sim = Simulator.objects.create(name="SIMSTOP", cp_path="SIMSTOP")
        stopper = SimpleNamespace(stop=AsyncMock())
        store.simulators[sim.pk] = stopper
        url = reverse("admin:ocpp_simulator_changelist")
        resp = self.client.post(
            url,
            {"action": "stop_simulator", "_selected_action": [sim.pk]},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        stopper.stop.assert_awaited_once()
        self.assertTrue(mock_get_loop.called)
        self.assertNotIn(sim.pk, store.simulators)

    @patch("ocpp.admin.asyncio.get_running_loop", side_effect=RuntimeError)
    def test_stop_simulator_change_action(self, mock_get_loop):
        sim = Simulator.objects.create(name="SIMCHGSTOP", cp_path="SIMCHGSTOP")
        stopper = SimpleNamespace(stop=AsyncMock())
        store.simulators[sim.pk] = stopper
        resp = self._post_simulator_change(
            sim,
            _action="stop_simulator_action",
        )
        self.assertEqual(resp.status_code, 200)
        stopper.stop.assert_awaited_once()
        self.assertTrue(mock_get_loop.called)
        self.assertNotIn(sim.pk, store.simulators)

    def test_as_config_includes_custom_fields(self):
        sim = Simulator.objects.create(
            name="SIM3",
            cp_path="S3",
            interval=3.5,
            kw_max=70,
            duration=500,
            pre_charge_delay=5,
            vin="WP0ZZZ99999999999",
            configuration_keys=[
                {"key": "HeartbeatInterval", "value": "300", "readonly": True}
            ],
            configuration_unknown_keys=["Bogus"],
        )
        cfg = sim.as_config()
        self.assertEqual(cfg.interval, 3.5)
        self.assertEqual(cfg.kw_max, 70)
        self.assertEqual(cfg.duration, 500)
        self.assertEqual(cfg.pre_charge_delay, 5)
        self.assertEqual(cfg.vin, "WP0ZZZ99999999999")
        self.assertEqual(
            cfg.configuration_keys,
            [{"key": "HeartbeatInterval", "value": "300", "readonly": True}],
        )
        self.assertEqual(cfg.configuration_unknown_keys, ["Bogus"])

    def _post_simulator_change(self, sim: Simulator, **overrides):
        url = reverse("admin:ocpp_simulator_change", args=[sim.pk])
        data = {
            "name": sim.name,
            "cp_path": sim.cp_path,
            "host": sim.host,
            "ws_port": sim.ws_port or "",
            "rfid": sim.rfid,
            "duration": sim.duration,
            "interval": sim.interval,
            "pre_charge_delay": sim.pre_charge_delay,
            "kw_max": sim.kw_max,
            "repeat": "on" if sim.repeat else "",
            "username": sim.username,
            "password": sim.password,
            "door_open": "on" if overrides.get("door_open", False) else "",
            "configuration_keys": json.dumps(sim.configuration_keys or []),
            "configuration_unknown_keys": json.dumps(
                sim.configuration_unknown_keys or []
            ),
            "_save": "Save",
        }
        data.update(overrides)
        return self.client.post(url, data, follow=True)

    def test_save_model_triggers_door_open(self):
        sim = Simulator.objects.create(name="SIMSAVE", cp_path="SIMSAVE")
        stub = SimpleNamespace(trigger_door_open=Mock())
        store.simulators[sim.pk] = stub
        resp = self._post_simulator_change(sim, door_open="on")
        self.assertEqual(resp.status_code, 200)
        stub.trigger_door_open.assert_called_once()
        self.assertContains(resp, "DoorOpen status notification sent")
        self.assertFalse(Simulator.objects.get(pk=sim.pk).door_open)
        store.simulators.pop(sim.pk, None)

    def test_save_model_reports_error_when_not_running(self):
        sim = Simulator.objects.create(name="SIMERR", cp_path="SIMERR")
        resp = self._post_simulator_change(sim, door_open="on")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "simulator is not running")
        self.assertFalse(Simulator.objects.get(pk=sim.pk).door_open)

    async def test_unknown_charger_auto_registered(self):
        communicator = WebsocketCommunicator(application, "/NEWCHG/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        exists = await database_sync_to_async(
            Charger.objects.filter(charger_id="NEWCHG").exists
        )()
        self.assertTrue(exists)

        charger = await database_sync_to_async(Charger.objects.get)(charger_id="NEWCHG")
        self.assertEqual(charger.last_path, "/NEWCHG/")

        await communicator.disconnect()

    async def test_query_string_cid_supported(self):
        communicator = WebsocketCommunicator(application, "/?cid=QSERIAL")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

        charger = await database_sync_to_async(Charger.objects.get)(charger_id="QSERIAL")
        self.assertEqual(charger.last_path, "/")

    async def test_query_string_charge_point_id_supported(self):
        communicator = WebsocketCommunicator(
            application, "/?chargePointId=QCHARGE"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

        charger = await database_sync_to_async(Charger.objects.get)(charger_id="QCHARGE")
        self.assertEqual(charger.last_path, "/")

    async def test_query_string_charge_box_id_supported(self):
        communicator = WebsocketCommunicator(
            application, "/?chargeBoxId=QBOX"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

        charger = await database_sync_to_async(Charger.objects.get)(charger_id="QBOX")
        self.assertEqual(charger.last_path, "/")

    async def test_query_string_charge_box_id_case_insensitive(self):
        communicator = WebsocketCommunicator(
            application, "/?CHARGEBOXID=CaseSense"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

        charger = await database_sync_to_async(Charger.objects.get)(
            charger_id="CaseSense"
        )
        self.assertEqual(charger.last_path, "/")

    async def test_query_string_charge_box_id_snake_case_supported(self):
        communicator = WebsocketCommunicator(
            application, "/?charge_box_id=SnakeCase"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

        charger = await database_sync_to_async(Charger.objects.get)(
            charger_id="SnakeCase"
        )
        self.assertEqual(charger.last_path, "/")

    async def test_query_string_charge_box_id_strips_whitespace(self):
        communicator = WebsocketCommunicator(
            application, "/?chargeBoxId=%20Trimmed%20Value%20"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

        charger = await database_sync_to_async(Charger.objects.get)(
            charger_id="Trimmed Value"
        )
        self.assertEqual(charger.last_path, "/")

    async def test_query_string_cid_overrides_path_segment(self):
        communicator = WebsocketCommunicator(application, "/ocpp?cid=QSEGOVR")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

        charger = await database_sync_to_async(Charger.objects.get)(charger_id="QSEGOVR")
        self.assertEqual(charger.last_path, "/ocpp")

    async def test_query_string_charge_point_id_overrides_path_segment(self):
        communicator = WebsocketCommunicator(
            application, "/ocpp?chargePointId=QPSEG"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

        charger = await database_sync_to_async(Charger.objects.get)(charger_id="QPSEG")
        self.assertEqual(charger.last_path, "/ocpp")

    async def test_nested_path_accepted_and_recorded(self):
        communicator = WebsocketCommunicator(application, "/foo/NEST/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

        charger = await database_sync_to_async(Charger.objects.get)(charger_id="NEST")
        self.assertEqual(charger.last_path, "/foo/NEST/")

    async def test_authorize_requires_rfid_accepts_known_account(self):
        await database_sync_to_async(Charger.objects.create)(
            charger_id="AUTHREQ", require_rfid=True
        )
        User = get_user_model()
        user = await database_sync_to_async(User.objects.create_user)(
            username="authuser", password="pwd"
        )
        account = await database_sync_to_async(EnergyAccount.objects.create)(
            user=user, name="Authorized"
        )
        await database_sync_to_async(EnergyCredit.objects.create)(
            account=account, amount_kw=10
        )
        tag = await database_sync_to_async(RFID.objects.create)(rfid="CAFE01")
        await database_sync_to_async(account.rfids.add)(tag)

        communicator = WebsocketCommunicator(application, "/AUTHREQ/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        message_id = "auth-1"
        await communicator.send_json_to(
            [2, message_id, "Authorize", {"idTag": "CAFE01"}]
        )
        response = await communicator.receive_json_from()
        self.assertEqual(response[0], 3)
        self.assertEqual(response[1], message_id)
        self.assertEqual(response[2], {"idTagInfo": {"status": "Accepted"}})

        await communicator.disconnect()

    async def test_authorize_requires_rfid_rejects_unknown_account(self):
        await database_sync_to_async(Charger.objects.create)(
            charger_id="AUTHINV", require_rfid=True
        )

        communicator = WebsocketCommunicator(application, "/AUTHINV/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        message_id = "auth-2"
        await communicator.send_json_to(
            [2, message_id, "Authorize", {"idTag": "DEAD00"}]
        )
        response = await communicator.receive_json_from()
        self.assertEqual(response[0], 3)
        self.assertEqual(response[1], message_id)
        self.assertEqual(response[2], {"idTagInfo": {"status": "Invalid"}})

        await communicator.disconnect()

    async def test_authorize_requires_rfid_accepts_allowed_tag_without_account(self):
        charger_id = "AUTHWARN"
        tag_value = "WARN01"
        await database_sync_to_async(Charger.objects.create)(
            charger_id=charger_id, require_rfid=True
        )
        await database_sync_to_async(RFID.objects.create)(rfid=tag_value, allowed=True)

        pending_key = store.pending_key(charger_id)
        store.clear_log(pending_key, log_type="charger")

        communicator = WebsocketCommunicator(application, f"/{charger_id}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        message_id = "auth-unlinked"
        await communicator.send_json_to(
            [2, message_id, "Authorize", {"idTag": tag_value}]
        )
        response = await communicator.receive_json_from()
        self.assertEqual(response[0], 3)
        self.assertEqual(response[1], message_id)
        self.assertEqual(response[2], {"idTagInfo": {"status": "Accepted"}})

        log_entries = store.get_logs(pending_key, log_type="charger")
        self.assertTrue(
            any(
                "Authorized RFID" in entry
                and tag_value in entry
                and charger_id in entry
                for entry in log_entries
            ),
            log_entries,
        )

        await communicator.disconnect()
        store.clear_log(pending_key, log_type="charger")

    async def test_authorize_without_requirement_records_rfid(self):
        await database_sync_to_async(Charger.objects.create)(
            charger_id="AUTHOPT", require_rfid=False
        )
        tag = await database_sync_to_async(RFID.objects.create)(rfid="BEEF02")
        old_seen = timezone.now() - timedelta(days=1)
        await database_sync_to_async(RFID.objects.filter(pk=tag.pk).update)(
            last_seen_on=old_seen
        )

        communicator = WebsocketCommunicator(application, "/AUTHOPT/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        message_id = "auth-3"
        await communicator.send_json_to(
            [2, message_id, "Authorize", {"idTag": "BEEF02"}]
        )
        response = await communicator.receive_json_from()
        self.assertEqual(response[0], 3)
        self.assertEqual(response[1], message_id)
        self.assertEqual(response[2], {"idTagInfo": {"status": "Accepted"}})

        updated_tag = await database_sync_to_async(RFID.objects.get)(rfid="BEEF02")
        self.assertIsNotNone(updated_tag.last_seen_on)
        self.assertGreater(updated_tag.last_seen_on, old_seen)

        await communicator.disconnect()

    async def test_rfid_required_rejects_invalid(self):
        await database_sync_to_async(Charger.objects.create)(
            charger_id="RFID", require_rfid=True
        )
        communicator = WebsocketCommunicator(application, "/RFID/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [
                2,
                "1",
                "StartTransaction",
                {"meterStart": 0},
            ]
        )
        response = await communicator.receive_json_from()
        self.assertEqual(response[2]["idTagInfo"]["status"], "Invalid")

        exists = await database_sync_to_async(
            Transaction.objects.filter(charger__charger_id="RFID").exists
        )()
        self.assertFalse(exists)

        await communicator.disconnect()

    async def test_rfid_required_accepts_known_tag(self):
        User = get_user_model()
        user = await database_sync_to_async(User.objects.create_user)(
            username="bob", password="pwd"
        )
        acc = await database_sync_to_async(EnergyAccount.objects.create)(
            user=user, name="BOB"
        )
        await database_sync_to_async(EnergyCredit.objects.create)(
            account=acc, amount_kw=10
        )
        tag = await database_sync_to_async(RFID.objects.create)(rfid="CARDX")
        await database_sync_to_async(acc.rfids.add)(tag)
        await database_sync_to_async(Charger.objects.create)(
            charger_id="RFIDOK", require_rfid=True
        )
        communicator = WebsocketCommunicator(application, "/RFIDOK/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            [
                2,
                "1",
                "StartTransaction",
                {"meterStart": 5, "idTag": "CARDX"},
            ]
        )
        response = await communicator.receive_json_from()
        self.assertEqual(response[2]["idTagInfo"]["status"], "Accepted")
        tx_id = response[2]["transactionId"]

        tx = await database_sync_to_async(Transaction.objects.get)(
            pk=tx_id, charger__charger_id="RFIDOK"
        )
        self.assertEqual(tx.account_id, user.energy_account.id)

    async def test_start_transaction_allows_allowed_tag_without_account(self):
        charger_id = "STARTWARN"
        tag_value = "WARN02"
        await database_sync_to_async(Charger.objects.create)(
            charger_id=charger_id, require_rfid=True
        )
        await database_sync_to_async(RFID.objects.create)(rfid=tag_value, allowed=True)

        pending_key = store.pending_key(charger_id)
        store.clear_log(pending_key, log_type="charger")

        communicator = WebsocketCommunicator(application, f"/{charger_id}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        start_payload = {
            "meterStart": 5,
            "idTag": tag_value,
            "connectorId": 1,
        }
        await communicator.send_json_to([2, "start-1", "StartTransaction", start_payload])
        response = await communicator.receive_json_from()
        self.assertEqual(response[0], 3)
        self.assertEqual(response[2]["idTagInfo"]["status"], "Accepted")
        tx_id = response[2]["transactionId"]

        tx = await database_sync_to_async(Transaction.objects.get)(
            pk=tx_id, charger__charger_id=charger_id
        )
        self.assertIsNone(tx.account_id)

        log_entries = store.get_logs(pending_key, log_type="charger")
        self.assertTrue(
            any(
                "Authorized RFID" in entry
                and tag_value in entry
                and charger_id in entry
                for entry in log_entries
            ),
            log_entries,
        )

        await communicator.send_json_to(
            [
                2,
                "stop-1",
                "StopTransaction",
                {"transactionId": tx_id, "meterStop": 6},
            ]
        )
        await communicator.receive_json_from()

        await communicator.disconnect()
        store.clear_log(pending_key, log_type="charger")

    async def test_status_fields_updated(self):
        communicator = WebsocketCommunicator(application, "/STAT/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to([2, "1", "Heartbeat", {}])
        await communicator.receive_json_from()

        charger = await database_sync_to_async(Charger.objects.get)(charger_id="STAT")
        self.assertIsNotNone(charger.last_heartbeat)

        payload = {
            "meterValue": [
                {
                    "timestamp": "2025-01-01T00:00:00Z",
                    "sampledValue": [{"value": "42"}],
                }
            ]
        }
        await communicator.send_json_to([2, "2", "MeterValues", payload])
        await communicator.receive_json_from()

        await database_sync_to_async(charger.refresh_from_db)()
        self.assertEqual(
            charger.last_meter_values.get("meterValue")[0]["sampledValue"][0]["value"],
            "42",
        )

        await communicator.disconnect()

    async def test_heartbeat_refreshes_aggregate_after_connector_status(self):
        store.ip_connections.clear()
        store.connections.clear()
        await database_sync_to_async(Charger.objects.create)(charger_id="HBAGG")
        communicator = WebsocketCommunicator(application, "/HBAGG/")
        connect_result = await communicator.connect()
        self.assertTrue(connect_result[0], connect_result)

        status_payload = {
            "connectorId": 2,
            "status": "Faulted",
            "errorCode": "ReaderFailure",
        }
        await communicator.send_json_to(
            [2, "1", "StatusNotification", status_payload]
        )
        await communicator.receive_json_from()

        aggregate = await database_sync_to_async(Charger.objects.get)(
            charger_id="HBAGG", connector_id=None
        )
        connector = await database_sync_to_async(Charger.objects.get)(
            charger_id="HBAGG", connector_id=2
        )
        previous_heartbeat = aggregate.last_heartbeat

        await communicator.send_json_to([2, "2", "Heartbeat", {}])
        await communicator.receive_json_from()

        await database_sync_to_async(aggregate.refresh_from_db)()
        await database_sync_to_async(connector.refresh_from_db)()

        self.assertIsNotNone(aggregate.last_heartbeat)
        if previous_heartbeat:
            self.assertNotEqual(aggregate.last_heartbeat, previous_heartbeat)
        self.assertEqual(connector.last_heartbeat, aggregate.last_heartbeat)

        await communicator.disconnect()


class ChargerLocationTests(TestCase):
    def test_lat_lon_fields_saved(self):
        loc = Location.objects.create(
            name="Loc1", latitude=10.123456, longitude=-20.654321
        )
        charger = Charger.objects.create(charger_id="LOC1", location=loc)
        self.assertAlmostEqual(float(charger.latitude), 10.123456)
        self.assertAlmostEqual(float(charger.longitude), -20.654321)
        self.assertEqual(charger.name, "Loc1")

    def test_location_created_when_missing(self):
        charger = Charger.objects.create(charger_id="AUTOLOC")
        self.assertIsNotNone(charger.location)
        self.assertEqual(charger.location.name, "AUTOLOC")

    def test_location_reused_for_matching_serial(self):
        first = Charger.objects.create(charger_id="SHARE", connector_id=1)
        first.location.name = "Custom"
        first.location.save()
        second = Charger.objects.create(charger_id="SHARE", connector_id=2)
        self.assertEqual(second.location, first.location)


class MeterReadingTests(TransactionTestCase):
    async def test_meter_values_saved_as_readings(self):
        communicator = WebsocketCommunicator(application, "/MR1/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        payload = {
            "connectorId": 1,
            "transactionId": 100,
            "meterValue": [
                {
                    "timestamp": "2025-07-29T10:01:51Z",
                    "sampledValue": [
                        {
                            "value": "2.749",
                            "measurand": "Energy.Active.Import.Register",
                            "unit": "kW",
                        }
                    ],
                }
            ],
        }
        await communicator.send_json_to([2, "1", "MeterValues", payload])
        await communicator.receive_json_from()

        reading = await database_sync_to_async(MeterReading.objects.get)(
            charger__charger_id="MR1"
        )
        self.assertEqual(reading.transaction_id, 100)
        self.assertEqual(str(reading.value), "2.749")
        tx = await database_sync_to_async(Transaction.objects.get)(
            pk=100, charger__charger_id="MR1"
        )
        self.assertEqual(tx.meter_start, 2749)

        await communicator.disconnect()


class ChargePointSimulatorTests(TransactionTestCase):
    async def test_simulator_sends_messages(self):
        received = []

        async def handler(ws):
            async for msg in ws:
                data = json.loads(msg)
                received.append(data)
                action = data[2]
                if action == "BootNotification":
                    await ws.send(
                        json.dumps(
                            [
                                3,
                                data[1],
                                {
                                    "status": "Accepted",
                                    "currentTime": "2024-01-01T00:00:00Z",
                                    "interval": 300,
                                },
                            ]
                        )
                    )
                elif action == "Authorize":
                    await ws.send(
                        json.dumps(
                            [
                                3,
                                data[1],
                                {"idTagInfo": {"status": "Accepted"}},
                            ]
                        )
                    )
                elif action == "StartTransaction":
                    await ws.send(
                        json.dumps(
                            [
                                3,
                                data[1],
                                {
                                    "transactionId": 1,
                                    "idTagInfo": {"status": "Accepted"},
                                },
                            ]
                        )
                    )
                elif action == "MeterValues":
                    await ws.send(json.dumps([3, data[1], {}]))
                elif action == "StopTransaction":
                    await ws.send(
                        json.dumps(
                            [
                                3,
                                data[1],
                                {"idTagInfo": {"status": "Accepted"}},
                            ]
                        )
                    )
                    break

        server = await websockets.serve(
            handler, "127.0.0.1", 0, subprotocols=["ocpp1.6"]
        )
        port = server.sockets[0].getsockname()[1]

        try:
            cfg = SimulatorConfig(
                host="127.0.0.1",
                ws_port=port,
                cp_path="SIM1/",
                vin="WP0ZZZ12345678901",
                duration=0.2,
                interval=0.05,
                kw_min=0.1,
                kw_max=0.2,
                pre_charge_delay=0.0,
                serial_number="SN123",
                connector_id=7,
            )
            sim = ChargePointSimulator(cfg)
            await sim._run_session()
        finally:
            server.close()
            await server.wait_closed()

        actions = [msg[2] for msg in received]
        self.assertIn("BootNotification", actions)
        self.assertIn("StartTransaction", actions)
        boot_msg = next(msg for msg in received if msg[2] == "BootNotification")
        self.assertEqual(boot_msg[3].get("serialNumber"), "SN123")
        start_msg = next(msg for msg in received if msg[2] == "StartTransaction")
        self.assertEqual(start_msg[3].get("vin"), "WP0ZZZ12345678901")
        self.assertEqual(start_msg[3].get("connectorId"), 7)

    async def test_start_returns_status_and_log(self):
        async def handler(ws):
            async for msg in ws:
                data = json.loads(msg)
                action = data[2]
                if action == "BootNotification":
                    await ws.send(
                        json.dumps(
                            [
                                3,
                                data[1],
                                {
                                    "status": "Accepted",
                                    "currentTime": "2024-01-01T00:00:00Z",
                                    "interval": 300,
                                },
                            ]
                        )
                    )
                elif action == "Authorize":
                    await ws.send(
                        json.dumps([3, data[1], {"idTagInfo": {"status": "Accepted"}}])
                    )
                elif action == "StartTransaction":
                    await ws.send(
                        json.dumps(
                            [
                                3,
                                data[1],
                                {
                                    "transactionId": 1,
                                    "idTagInfo": {"status": "Accepted"},
                                },
                            ]
                        )
                    )
                elif action == "StopTransaction":
                    await ws.send(
                        json.dumps([3, data[1], {"idTagInfo": {"status": "Accepted"}}])
                    )
                    break
                else:
                    await ws.send(json.dumps([3, data[1], {}]))

        server = await websockets.serve(
            handler, "127.0.0.1", 0, subprotocols=["ocpp1.6"]
        )
        port = server.sockets[0].getsockname()[1]

        cfg = SimulatorConfig(
            host="127.0.0.1",
            ws_port=port,
            cp_path="SIMSTART/",
            duration=0.1,
            interval=0.05,
            kw_min=0.1,
            kw_max=0.2,
            pre_charge_delay=0.0,
        )
        store.register_log_name(cfg.cp_path, "SimStart", log_type="simulator")
        try:
            sim = ChargePointSimulator(cfg)
            started, status, log_file = await asyncio.to_thread(sim.start)
            self.assertTrue(started)
            self.assertEqual(status, "Connection accepted")
            self.assertEqual(sim.status, "running")
            self.assertTrue(Path(log_file).exists())
        finally:
            await sim.stop()
            store.clear_log(cfg.cp_path, log_type="simulator")
            server.close()
            await server.wait_closed()

    async def test_simulator_stops_when_charger_closes(self):
        async def handler(ws):
            async for msg in ws:
                data = json.loads(msg)
                action = data[2]
                if action == "BootNotification":
                    await ws.send(json.dumps([3, data[1], {"status": "Accepted"}]))
                elif action == "Authorize":
                    await ws.send(
                        json.dumps([3, data[1], {"idTagInfo": {"status": "Accepted"}}])
                    )
                    await ws.close()
                    break

        server = await websockets.serve(
            handler, "127.0.0.1", 0, subprotocols=["ocpp1.6"]
        )
        port = server.sockets[0].getsockname()[1]

        cfg = SimulatorConfig(
            host="127.0.0.1",
            ws_port=port,
            cp_path="SIMTERM/",
            duration=0.1,
            interval=0.05,
            kw_min=0.1,
            kw_max=0.2,
            pre_charge_delay=0.0,
        )
        sim = ChargePointSimulator(cfg)
        try:
            started, _, _ = await asyncio.to_thread(sim.start)
            self.assertTrue(started)
            # Allow time for the server to close the connection
            await asyncio.sleep(0.1)
            self.assertEqual(sim.status, "stopped")
            self.assertFalse(sim._thread.is_alive())
        finally:
            await sim.stop()
            server.close()
            await server.wait_closed()

    async def test_pre_charge_sends_heartbeat_and_meter(self):
        received = []

        async def handler(ws):
            async for msg in ws:
                data = json.loads(msg)
                received.append(data)
                action = data[2]
                if action == "BootNotification":
                    await ws.send(json.dumps([3, data[1], {"status": "Accepted"}]))
                elif action in {
                    "Authorize",
                    "StatusNotification",
                    "Heartbeat",
                    "MeterValues",
                }:
                    await ws.send(json.dumps([3, data[1], {}]))
                elif action == "StartTransaction":
                    await ws.send(
                        json.dumps(
                            [
                                3,
                                data[1],
                                {
                                    "transactionId": 1,
                                    "idTagInfo": {"status": "Accepted"},
                                },
                            ]
                        )
                    )
                elif action == "StopTransaction":
                    await ws.send(
                        json.dumps([3, data[1], {"idTagInfo": {"status": "Accepted"}}])
                    )
                    break

        server = await websockets.serve(
            handler, "127.0.0.1", 0, subprotocols=["ocpp1.6"]
        )
        port = server.sockets[0].getsockname()[1]

        try:
            cfg = SimulatorConfig(
                host="127.0.0.1",
                ws_port=port,
                cp_path="SIMPRE/",
                duration=0.1,
                interval=0.05,
                kw_min=0.1,
                kw_max=0.2,
                pre_charge_delay=0.1,
            )
            sim = ChargePointSimulator(cfg)
            await sim._run_session()
        finally:
            server.close()
            await server.wait_closed()

        actions = [msg[2] for msg in received]
        start_idx = actions.index("StartTransaction")
        pre_actions = actions[:start_idx]
        self.assertIn("Heartbeat", pre_actions)
        self.assertIn("MeterValues", pre_actions)

    async def test_simulator_times_out_without_response(self):
        async def handler(ws):
            async for _ in ws:
                pass

        server = await websockets.serve(
            handler, "127.0.0.1", 0, subprotocols=["ocpp1.6"]
        )
        port = server.sockets[0].getsockname()[1]

        cfg = SimulatorConfig(host="127.0.0.1", ws_port=port, cp_path="SIMTO/")
        sim = ChargePointSimulator(cfg)
        store.simulators[99] = sim
        try:

            async def fake_wait_for(coro, timeout):
                coro.close()
                raise asyncio.TimeoutError

            with patch("ocpp.simulator.asyncio.wait_for", fake_wait_for):
                started, status, _ = await asyncio.to_thread(sim.start)
            await asyncio.to_thread(sim._thread.join)
            self.assertFalse(started)
            self.assertIn("Timeout", status)
            self.assertNotIn(99, store.simulators)
        finally:
            await sim.stop()
            server.close()
            await server.wait_closed()

    async def test_handle_csms_call_logs_unsupported_action(self):
        cfg = SimulatorConfig(cp_path="SIMLOG/")
        sim = ChargePointSimulator(cfg)
        store.clear_log(cfg.cp_path, log_type="simulator")
        store.logs["simulator"][cfg.cp_path] = []
        sent_frames: list[str] = []

        async def send(payload: str) -> None:
            sent_frames.append(payload)

        async def recv():
            return None

        try:
            handled = await sim._handle_csms_call(
                [2, "msg1", "Reset", {}],
                send,
                recv,
            )
            self.assertTrue(handled)
            logs = store.get_logs(cfg.cp_path, log_type="simulator")
            self.assertTrue(
                any(
                    "Received unsupported action 'Reset'" in entry
                    for entry in logs
                ),
                logs,
            )
            self.assertTrue(sent_frames, "Expected a CallError response from simulator")
            frame = json.loads(sent_frames[-1])
            self.assertEqual(frame[0], 4)
            self.assertEqual(frame[1], "msg1")
            self.assertEqual(frame[2], "NotSupported")
            self.assertIn("Simulator does not implement Reset", frame[3])
            self.assertNotIn(sim, store.simulators.values())
        finally:
            store.clear_log(cfg.cp_path, log_type="simulator")
            store.logs["simulator"].pop(cfg.cp_path, None)
            for key, value in list(store.simulators.items()):
                if value is sim:
                    store.simulators.pop(key, None)

    async def test_door_open_event_sends_notifications(self):
        status_payloads = []

        async def handler(ws):
            async for msg in ws:
                data = json.loads(msg)
                action = data[2]
                if action == "BootNotification":
                    await ws.send(
                        json.dumps(
                            [
                                3,
                                data[1],
                                {"status": "Accepted", "currentTime": "2024-01-01T00:00:00Z"},
                            ]
                        )
                    )
                elif action == "Authorize":
                    await ws.send(json.dumps([3, data[1], {"idTagInfo": {"status": "Accepted"}}]))
                elif action == "StatusNotification":
                    status_payloads.append(data[3])
                    await ws.send(json.dumps([3, data[1], {}]))
                elif action == "StartTransaction":
                    await ws.send(
                        json.dumps(
                            [
                                3,
                                data[1],
                                {"transactionId": 1, "idTagInfo": {"status": "Accepted"}},
                            ]
                        )
                    )
                elif action == "MeterValues":
                    await ws.send(json.dumps([3, data[1], {}]))
                elif action == "StopTransaction":
                    await ws.send(json.dumps([3, data[1], {"idTagInfo": {"status": "Accepted"}}]))
                    break

        server = await websockets.serve(
            handler, "127.0.0.1", 0, subprotocols=["ocpp1.6"]
        )
        port = server.sockets[0].getsockname()[1]

        cfg = SimulatorConfig(
            host="127.0.0.1",
            ws_port=port,
            cp_path="SIMDOOR/",
            duration=0.2,
            interval=0.05,
            pre_charge_delay=0.0,
        )
        sim = ChargePointSimulator(cfg)
        sim.trigger_door_open()
        try:
            await sim._run_session()
        finally:
            server.close()
            await server.wait_closed()
            store.clear_log(cfg.cp_path, log_type="simulator")

        door_open_messages = [p for p in status_payloads if p.get("errorCode") == "DoorOpen"]
        door_closed_messages = [p for p in status_payloads if p.get("errorCode") == "NoError"]
        self.assertTrue(door_open_messages)
        self.assertTrue(door_closed_messages)
        first_open = next(
            idx for idx, payload in enumerate(status_payloads) if payload.get("errorCode") == "DoorOpen"
        )
        first_close = next(
            idx for idx, payload in enumerate(status_payloads) if payload.get("errorCode") == "NoError"
        )
        self.assertLess(first_open, first_close)

    async def test_get_configuration_uses_configured_keys(self):
        cfg = SimulatorConfig(
            configuration_keys=[
                {"key": "HeartbeatInterval", "value": "300", "readonly": True},
                {"key": "MeterValueSampleInterval", "value": 900},
            ],
            configuration_unknown_keys=["UnknownX"],
        )
        sim = ChargePointSimulator(cfg)
        sent: list[list[object]] = []

        async def send(msg: str):
            sent.append(json.loads(msg))

        async def recv():  # pragma: no cover - should not be called
            raise AssertionError("recv should not be called for GetConfiguration")

        handled = await sim._handle_csms_call(
            [
                2,
                "cfg-1",
                "GetConfiguration",
                {"key": ["HeartbeatInterval", "UnknownX", "MissingKey"]},
            ],
            send,
            recv,
        )
        self.assertTrue(handled)
        self.assertEqual(len(sent), 1)
        frame = sent[0]
        self.assertEqual(frame[0], 3)
        self.assertEqual(frame[1], "cfg-1")
        payload = frame[2]
        self.assertIn("configurationKey", payload)
        self.assertEqual(
            payload["configurationKey"],
            [{"key": "HeartbeatInterval", "value": "300", "readonly": True}],
        )
        self.assertIn("unknownKey", payload)
        self.assertCountEqual(payload["unknownKey"], ["UnknownX", "MissingKey"])

    async def test_get_configuration_without_filter_returns_all(self):
        cfg = SimulatorConfig(
            configuration_keys=[
                {"key": "AuthorizeRemoteTxRequests", "value": True},
                {"key": "ConnectorPhaseRotation", "value": "ABC"},
            ],
            configuration_unknown_keys=["GhostKey"],
        )
        sim = ChargePointSimulator(cfg)
        sent: list[list[object]] = []

        async def send(msg: str):
            sent.append(json.loads(msg))

        async def recv():  # pragma: no cover - should not be called
            raise AssertionError("recv should not be called for GetConfiguration")

        handled = await sim._handle_csms_call(
            [2, "cfg-2", "GetConfiguration", {}],
            send,
            recv,
        )
        self.assertTrue(handled)
        frame = sent[0]
        payload = frame[2]
        keys = payload.get("configurationKey")
        self.assertEqual(len(keys), 2)
        returned_keys = {item["key"] for item in keys}
        self.assertEqual(
            returned_keys,
            {"AuthorizeRemoteTxRequests", "ConnectorPhaseRotation"},
        )
        values = {item["key"]: item.get("value") for item in keys}
        self.assertEqual(values["AuthorizeRemoteTxRequests"], "True")
        self.assertEqual(values["ConnectorPhaseRotation"], "ABC")
        self.assertIn("unknownKey", payload)
        self.assertEqual(payload["unknownKey"], ["GhostKey"])

    async def test_unknown_action_returns_call_error(self):
        cfg = SimulatorConfig(cp_path="SIM-CALL-ERROR/")
        sim = ChargePointSimulator(cfg)
        sent: list[list[object]] = []

        async def send(msg: str):
            sent.append(json.loads(msg))

        async def recv():  # pragma: no cover - should not be called
            raise AssertionError("recv should not be called for unsupported actions")

        handled = await sim._handle_csms_call(
            [2, "msg-1", "Reset", {"type": "Soft"}],
            send,
            recv,
        )

        self.assertTrue(handled)
        self.assertEqual(len(sent), 1)
        frame = sent[0]
        self.assertEqual(frame[0], 4)
        self.assertEqual(frame[1], "msg-1")
        self.assertEqual(frame[2], "NotSupported")
        self.assertIn("Reset", frame[3])
        self.assertIsInstance(frame[4], dict)

    async def test_trigger_message_heartbeat_follow_up(self):
        cfg = SimulatorConfig()
        sim = ChargePointSimulator(cfg)
        sent: list[list[object]] = []
        recv_count = 0

        async def send(msg: str):
            sent.append(json.loads(msg))

        async def recv():
            nonlocal recv_count
            recv_count += 1
            return json.dumps([3, f"ack-{recv_count}", {}])

        handled = await sim._handle_csms_call(
            [
                2,
                "trigger-req",
                "TriggerMessage",
                {"requestedMessage": "Heartbeat"},
            ],
            send,
            recv,
        )

        self.assertTrue(handled)
        self.assertGreaterEqual(len(sent), 2)
        result_frame = sent[0]
        follow_up_frame = sent[1]
        self.assertEqual(result_frame[0], 3)
        self.assertEqual(result_frame[1], "trigger-req")
        self.assertEqual(result_frame[2].get("status"), "Accepted")
        self.assertEqual(follow_up_frame[0], 2)
        self.assertEqual(follow_up_frame[2], "Heartbeat")
        self.assertEqual(recv_count, 1)

    async def test_trigger_message_rejected_for_invalid_connector(self):
        cfg = SimulatorConfig(connector_id=5)
        sim = ChargePointSimulator(cfg)
        sent: list[list[object]] = []

        async def send(msg: str):
            sent.append(json.loads(msg))

        async def recv():  # pragma: no cover - should not be called
            raise AssertionError("recv should not be called for rejected TriggerMessage")

        handled = await sim._handle_csms_call(
            [
                2,
                "trigger-invalid",
                "TriggerMessage",
                {"requestedMessage": "StatusNotification", "connectorId": 1},
            ],
            send,
            recv,
        )

        self.assertTrue(handled)
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][0], 3)
        self.assertEqual(sent[0][1], "trigger-invalid")
        self.assertEqual(sent[0][2].get("status"), "Rejected")


class PurgeMeterReadingsTaskTests(TestCase):
    def test_purge_old_meter_readings(self):
        charger = Charger.objects.create(charger_id="PURGER")
        tx = Transaction.objects.create(
            charger=charger,
            meter_start=0,
            meter_stop=1000,
            start_time=timezone.now(),
            stop_time=timezone.now(),
        )
        old = timezone.now() - timedelta(days=8)
        recent = timezone.now() - timedelta(days=2)
        MeterReading.objects.create(
            charger=charger, transaction=tx, timestamp=old, value=1
        )
        MeterReading.objects.create(
            charger=charger, transaction=tx, timestamp=recent, value=2
        )

        purge_meter_readings()

        self.assertEqual(MeterReading.objects.count(), 1)
        self.assertTrue(
            MeterReading.objects.filter(
                timestamp__gte=recent - timedelta(minutes=1)
            ).exists()
        )
        self.assertTrue(Transaction.objects.filter(pk=tx.pk).exists())

    def test_purge_skips_open_transactions(self):
        charger = Charger.objects.create(charger_id="PURGER2")
        tx = Transaction.objects.create(
            charger=charger,
            meter_start=0,
            start_time=timezone.now() - timedelta(days=9),
        )
        old = timezone.now() - timedelta(days=8)
        reading = MeterReading.objects.create(
            charger=charger, transaction=tx, timestamp=old, value=1
        )

        purge_meter_readings()

        self.assertTrue(MeterReading.objects.filter(pk=reading.pk).exists())


class DailySessionReportTaskTests(TestCase):
    def setUp(self):
        super().setUp()
        self.locks_dir = Path(settings.BASE_DIR) / "locks"
        self.locks_dir.mkdir(parents=True, exist_ok=True)
        self.celery_lock = self.locks_dir / "celery.lck"
        self.celery_lock.write_text("")
        self.addCleanup(self._cleanup_lock)

    def _cleanup_lock(self):
        try:
            self.celery_lock.unlink()
        except FileNotFoundError:
            pass

    def test_report_sends_email_when_sessions_exist(self):
        User = get_user_model()
        User.objects.create_superuser(
            username="report-admin",
            email="report-admin@example.com",
            password="pw",
        )
        charger = Charger.objects.create(charger_id="RPT1", display_name="Pod 1")
        start = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        Transaction.objects.create(
            charger=charger,
            start_time=start,
            stop_time=start + timedelta(hours=1),
            meter_start=0,
            meter_stop=2500,
            connector_id=2,
            rfid="AA11",
        )

        with patch("core.mailer.can_send_email", return_value=True), patch(
            "core.mailer.send"
        ) as mock_send:
            count = send_daily_session_report()

        self.assertEqual(count, 1)
        self.assertTrue(mock_send.called)
        args, _kwargs = mock_send.call_args
        self.assertIn("OCPP session report", args[0])
        self.assertIn("Pod 1", args[1])
        self.assertIn("report-admin@example.com", args[2])
        self.assertGreaterEqual(len(args[2]), 1)

    def test_report_skips_when_no_sessions(self):
        with patch("core.mailer.can_send_email", return_value=True), patch(
            "core.mailer.send"
        ) as mock_send:
            count = send_daily_session_report()

        self.assertEqual(count, 0)
        mock_send.assert_not_called()

    def test_report_skips_without_celery_feature(self):
        if self.celery_lock.exists():
            self.celery_lock.unlink()

        with patch("core.mailer.can_send_email", return_value=True), patch(
            "core.mailer.send"
        ) as mock_send:
            count = send_daily_session_report()

        self.assertEqual(count, 0)
        mock_send.assert_not_called()


class TransactionKwTests(TestCase):
    def test_kw_sums_meter_readings(self):
        charger = Charger.objects.create(charger_id="SUM1")
        tx = Transaction.objects.create(
            charger=charger, start_time=timezone.now(), meter_start=0
        )
        MeterReading.objects.create(
            charger=charger,
            transaction=tx,
            timestamp=timezone.now(),
            value=Decimal("1000"),
            unit="W",
        )
        MeterReading.objects.create(
            charger=charger,
            transaction=tx,
            timestamp=timezone.now(),
            value=Decimal("1500"),
            unit="W",
        )
        self.assertAlmostEqual(tx.kw, 1.5)

    def test_kw_defaults_to_zero(self):
        charger = Charger.objects.create(charger_id="SUM2")
        tx = Transaction.objects.create(charger=charger, start_time=timezone.now())
        self.assertEqual(tx.kw, 0.0)


class TransactionIdentifierTests(TestCase):
    def test_vehicle_identifier_prefers_vid(self):
        charger = Charger.objects.create(charger_id="VIDPREF")
        tx = Transaction.objects.create(
            charger=charger,
            start_time=timezone.now(),
            vid="VID-123",
            vin="VIN-456",
        )
        self.assertEqual(tx.vehicle_identifier, "VID-123")
        self.assertEqual(tx.vehicle_identifier_source, "vid")

    def test_vehicle_identifier_falls_back_to_vin(self):
        charger = Charger.objects.create(charger_id="VINONLY")
        tx = Transaction.objects.create(
            charger=charger,
            start_time=timezone.now(),
            vin="WP0ZZZ00000000001",
        )
        self.assertEqual(tx.vehicle_identifier, "WP0ZZZ00000000001")
        self.assertEqual(tx.vehicle_identifier_source, "vin")

    def test_transaction_rfid_details_handles_vin(self):
        charger = Charger.objects.create(charger_id="VINDET")
        tx = Transaction.objects.create(
            charger=charger,
            start_time=timezone.now(),
            vin="WAUZZZ00000000002",
        )
        details = _transaction_rfid_details(tx, cache={})
        self.assertIsNotNone(details)
        assert details is not None  # for type checkers
        self.assertEqual(details["value"], "WAUZZZ00000000002")
        self.assertEqual(details["display_label"], "VIN")
        self.assertEqual(details["type"], "vin")


class DispatchActionViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(username="dispatch", password="pw")
        self.client.force_login(self.user)
        try:
            self.previous_loop = asyncio.get_event_loop()
        except RuntimeError:
            self.previous_loop = None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.addCleanup(self._close_loop)
        self.charger = Charger.objects.create(
            charger_id="DISPATCH", connector_id=1
        )
        self.ws = DummyWebSocket()
        store.set_connection(
            self.charger.charger_id, self.charger.connector_id, self.ws
        )
        self.addCleanup(
            store.pop_connection,
            self.charger.charger_id,
            self.charger.connector_id,
        )
        self.log_key = store.identity_key(
            self.charger.charger_id, self.charger.connector_id
        )
        store.clear_log(self.log_key, log_type="charger")
        self.addCleanup(store.clear_log, self.log_key, "charger")
        store.pending_calls.clear()
        self.addCleanup(store.pending_calls.clear)
        store._pending_call_events.clear()
        store._pending_call_results.clear()
        self.addCleanup(store._pending_call_events.clear)
        self.addCleanup(store._pending_call_results.clear)
        self.url = reverse(
            "charger-action-connector",
            args=[self.charger.charger_id, self.charger.connector_slug],
        )
        self.wait_patch = patch(
            "ocpp.views.store.wait_for_pending_call",
            side_effect=self._wait_success,
        )
        self.mock_wait = self.wait_patch.start()
        self.addCleanup(self.wait_patch.stop)

    def _close_loop(self):
        try:
            if not self.loop.is_closed():
                self.loop.run_until_complete(asyncio.sleep(0))
        except RuntimeError:
            pass
        finally:
            if not self.loop.is_closed():
                self.loop.close()
            asyncio.set_event_loop(self.previous_loop)

    def _wait_success(self, message_id, timeout=5.0):  # noqa: D401 - helper for patch
        metadata = store.pending_calls.pop(message_id, None)
        store._pending_call_events.pop(message_id, None)
        store._pending_call_results.pop(message_id, None)
        return {
            "success": True,
            "payload": {"status": "Accepted"},
            "metadata": dict(metadata or {}),
        }

    def test_remote_start_requires_id_tag(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"action": "remote_start"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("detail"), "idTag required")
        self.loop.run_until_complete(asyncio.sleep(0))
        self.assertEqual(self.ws.sent, [])

    def test_remote_start_dispatches_frame(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"action": "remote_start", "idTag": "RF1234"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.loop.run_until_complete(asyncio.sleep(0))
        self.assertEqual(len(self.ws.sent), 1)
        frame = json.loads(self.ws.sent[0])
        self.assertEqual(frame[0], 2)
        self.assertEqual(frame[2], "RemoteStartTransaction")
        self.assertEqual(frame[3]["idTag"], "RF1234")
        self.assertEqual(frame[3]["connectorId"], 1)
        log_entries = store.logs["charger"].get(self.log_key, [])
        self.assertTrue(
            any("RemoteStartTransaction" in entry for entry in log_entries)
        )

    def test_change_availability_dispatches_frame(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"action": "change_availability", "type": "Inoperative"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.loop.run_until_complete(asyncio.sleep(0))
        self.assertEqual(len(self.ws.sent), 1)
        frame = json.loads(self.ws.sent[0])
        self.assertEqual(frame[0], 2)
        self.assertEqual(frame[2], "ChangeAvailability")
        self.assertEqual(frame[3]["type"], "Inoperative")
        self.assertEqual(frame[3]["connectorId"], 1)
        self.charger.refresh_from_db()
        self.assertEqual(self.charger.availability_requested_state, "Inoperative")
        self.assertIsNotNone(self.charger.availability_requested_at)
        self.assertEqual(self.charger.availability_request_status, "")
        self.assertNotIn(frame[1], store.pending_calls)

    def test_remote_start_reports_rejection(self):
        def rejected(message_id, timeout=5.0):
            metadata = store.pending_calls.pop(message_id, None)
            store._pending_call_events.pop(message_id, None)
            store._pending_call_results.pop(message_id, None)
            return {
                "success": True,
                "payload": {"status": "Rejected"},
                "metadata": dict(metadata or {}),
            }

        self.mock_wait.side_effect = rejected
        response = self.client.post(
            self.url,
            data=json.dumps({"action": "remote_start", "idTag": "RF1234"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        detail = response.json().get("detail", "")
        self.assertIn("Rejected", detail)
        self.mock_wait.side_effect = self._wait_success

    def test_remote_start_reports_error_details(self):
        def call_error(message_id, timeout=5.0):
            metadata = store.pending_calls.pop(message_id, None)
            store._pending_call_events.pop(message_id, None)
            store._pending_call_results.pop(message_id, None)
            return {
                "success": False,
                "error_code": "NotSupported",
                "error_description": "Not supported",
                "error_details": {"reason": "unsupported"},
                "metadata": dict(metadata or {}),
            }

        self.mock_wait.side_effect = call_error
        response = self.client.post(
            self.url,
            data=json.dumps({"action": "remote_start", "idTag": "RF1234"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        detail = response.json().get("detail", "")
        self.assertIn("NotSupported", detail)
        self.assertIn("unsupported", detail)
        self.mock_wait.side_effect = self._wait_success

    def test_remote_start_reports_timeout(self):
        def no_response(message_id, timeout=5.0):
            return None

        self.mock_wait.side_effect = no_response
        response = self.client.post(
            self.url,
            data=json.dumps({"action": "remote_start", "idTag": "RF1234"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 504)
        detail = response.json().get("detail", "")
        self.assertIn("did not receive", detail)
        self.mock_wait.side_effect = self._wait_success

    def test_change_availability_requires_valid_type(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"action": "change_availability"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.loop.run_until_complete(asyncio.sleep(0))
        self.assertEqual(self.ws.sent, [])
        self.assertFalse(store.pending_calls)


class SimulatorStateMappingTests(TestCase):
    def tearDown(self):
        _simulators[1] = SimulatorState()
        _simulators[2] = SimulatorState()

    def test_simulate_uses_requested_state(self):
        calls = []

        async def fake(cp_idx, *args, sim_state=None, **kwargs):
            calls.append(sim_state)
            if sim_state is not None:
                sim_state.running = False

        with patch("ocpp.evcs.simulate_cp", new=fake):
            coro = simulate(cp=2, daemon=True, threads=1)
            asyncio.run(coro)

        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0], _simulators[2])


class ChargerStatusViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(username="status", password="pwd")
        self.client.force_login(self.user)

    def test_chart_data_populated_from_existing_readings(self):
        charger = Charger.objects.create(charger_id="VIEW1", connector_id=1)
        tx = Transaction.objects.create(
            charger=charger, start_time=timezone.now(), meter_start=0
        )
        t0 = timezone.now()
        MeterReading.objects.create(
            charger=charger,
            transaction=tx,
            timestamp=t0,
            value=Decimal("1000"),
            unit="W",
        )
        MeterReading.objects.create(
            charger=charger,
            transaction=tx,
            timestamp=t0 + timedelta(seconds=10),
            value=Decimal("1500"),
            unit="W",
        )
        key = store.identity_key(charger.charger_id, charger.connector_id)
        store.transactions[key] = tx
        resp = self.client.get(
            reverse(
                "charger-status-connector",
                args=[charger.charger_id, charger.connector_slug],
            )
        )
        self.assertEqual(resp.status_code, 200)
        chart = resp.context["chart_data"]
        self.assertEqual(len(chart["labels"]), 2)
        self.assertEqual(len(chart["datasets"]), 1)
        values = chart["datasets"][0]["values"]
        self.assertEqual(chart["datasets"][0]["connector_id"], 1)
        self.assertAlmostEqual(values[0], 1.0)
        self.assertAlmostEqual(values[1], 1.5)
        store.transactions.pop(key, None)

    def test_chart_data_uses_meter_start_for_register_values(self):
        charger = Charger.objects.create(charger_id="VIEWREG", connector_id=1)
        tx = Transaction.objects.create(
            charger=charger, start_time=timezone.now(), meter_start=746060
        )
        t0 = timezone.now()
        MeterReading.objects.create(
            charger=charger,
            transaction=tx,
            timestamp=t0,
            measurand="Energy.Active.Import.Register",
            value=Decimal("746.060"),
            unit="kWh",
        )
        MeterReading.objects.create(
            charger=charger,
            transaction=tx,
            timestamp=t0 + timedelta(seconds=10),
            measurand="Energy.Active.Import.Register",
            value=Decimal("746.080"),
            unit="kWh",
        )
        key = store.identity_key(charger.charger_id, charger.connector_id)
        store.transactions[key] = tx
        resp = self.client.get(
            reverse(
                "charger-status-connector",
                args=[charger.charger_id, charger.connector_slug],
            )
        )
        chart = resp.context["chart_data"]
        self.assertEqual(len(chart["labels"]), 2)
        self.assertEqual(len(chart["datasets"]), 1)
        values = chart["datasets"][0]["values"]
        self.assertEqual(chart["datasets"][0]["connector_id"], 1)
        self.assertAlmostEqual(values[0], 0.0)
        self.assertAlmostEqual(values[1], 0.02)
        self.assertAlmostEqual(resp.context["tx"].kw, 0.02)
        store.transactions.pop(key, None)

    def test_diagnostics_status_displayed(self):
        reported_at = timezone.now().replace(microsecond=0)
        charger = Charger.objects.create(
            charger_id="DIAGPAGE",
            diagnostics_status="Uploaded",
            diagnostics_location="https://example.com/report.tar",
            diagnostics_timestamp=reported_at,
        )

        resp = self.client.get(reverse("charger-status", args=[charger.charger_id]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Diagnostics")
        self.assertContains(resp, "id=\"diagnostics-status\"")
        self.assertContains(resp, "Uploaded")
        self.assertContains(resp, "id=\"diagnostics-timestamp\"")
        self.assertContains(resp, "id=\"diagnostics-location\"")
        self.assertContains(resp, "https://example.com/report.tar")

    def test_connector_status_prefers_connector_diagnostics(self):
        aggregate = Charger.objects.create(
            charger_id="DIAGCONN",
            diagnostics_status="Uploaded",
        )
        connector = Charger.objects.create(
            charger_id="DIAGCONN",
            connector_id=1,
            diagnostics_status="Uploading",
        )

        aggregate_resp = self.client.get(
            reverse("charger-status", args=[aggregate.charger_id])
        )
        self.assertContains(aggregate_resp, "Uploaded")
        self.assertNotContains(aggregate_resp, "Uploading")

        connector_resp = self.client.get(
            reverse(
                "charger-status-connector",
                args=[connector.charger_id, connector.connector_slug],
            )
        )
        self.assertContains(connector_resp, "Uploading")

    def test_sessions_are_linked(self):
        charger = Charger.objects.create(charger_id="LINK1")
        tx = Transaction.objects.create(charger=charger, start_time=timezone.now())
        resp = self.client.get(reverse("charger-status", args=[charger.charger_id]))
        self.assertContains(resp, f"?session={tx.id}")

    def test_status_links_landing_page(self):
        charger = Charger.objects.create(charger_id="LAND1")
        resp = self.client.get(reverse("charger-status", args=[charger.charger_id]))
        self.assertContains(resp, reverse("charger-page", args=[charger.charger_id]))

    def test_configuration_link_hidden_for_non_staff(self):
        charger = Charger.objects.create(charger_id="CFG-HIDE")
        response = self.client.get(reverse("charger-status", args=[charger.charger_id]))
        admin_url = reverse("admin:ocpp_charger_change", args=[charger.pk])
        self.assertNotContains(response, admin_url)
        self.assertNotContains(response, _("Configuration"))

    def test_configuration_link_visible_for_staff(self):
        charger = Charger.objects.create(charger_id="CFG-SHOW")
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        response = self.client.get(reverse("charger-status", args=[charger.charger_id]))
        admin_url = reverse("admin:ocpp_charger_change", args=[charger.pk])
        self.assertContains(response, admin_url)
        self.assertContains(response, _("Configuration"))

    def test_past_session_chart(self):
        charger = Charger.objects.create(charger_id="PAST1", connector_id=1)
        tx = Transaction.objects.create(
            charger=charger, start_time=timezone.now(), meter_start=0
        )
        t0 = timezone.now()
        MeterReading.objects.create(
            charger=charger,
            transaction=tx,
            timestamp=t0,
            value=Decimal("1000"),
            unit="W",
        )
        MeterReading.objects.create(
            charger=charger,
            transaction=tx,
            timestamp=t0 + timedelta(seconds=10),
            value=Decimal("1500"),
            unit="W",
        )
        resp = self.client.get(
            reverse(
                "charger-status-connector",
                args=[charger.charger_id, charger.connector_slug],
            )
            + f"?session={tx.id}"
        )
        self.assertContains(resp, "Back to live")
        chart = resp.context["chart_data"]
        self.assertEqual(len(chart["labels"]), 2)
        self.assertEqual(len(chart["datasets"]), 1)
        self.assertEqual(chart["datasets"][0]["connector_id"], 1)
        self.assertTrue(resp.context["past_session"])

    def test_aggregate_chart_includes_multiple_connectors(self):
        aggregate = Charger.objects.create(charger_id="VIEWAGG")
        connector_one = Charger.objects.create(charger_id="VIEWAGG", connector_id=1)
        connector_two = Charger.objects.create(charger_id="VIEWAGG", connector_id=2)
        base_time = timezone.now()
        tx_one = Transaction.objects.create(
            charger=connector_one, start_time=base_time, meter_start=0
        )
        tx_two = Transaction.objects.create(
            charger=connector_two, start_time=base_time, meter_start=0
        )
        MeterReading.objects.create(
            charger=connector_one,
            transaction=tx_one,
            timestamp=base_time,
            value=Decimal("1000"),
            unit="W",
        )
        MeterReading.objects.create(
            charger=connector_one,
            transaction=tx_one,
            timestamp=base_time + timedelta(seconds=15),
            value=Decimal("1500"),
            unit="W",
        )
        MeterReading.objects.create(
            charger=connector_two,
            transaction=tx_two,
            timestamp=base_time + timedelta(seconds=5),
            value=Decimal("2000"),
            unit="W",
        )
        MeterReading.objects.create(
            charger=connector_two,
            transaction=tx_two,
            timestamp=base_time + timedelta(seconds=20),
            value=Decimal("2600"),
            unit="W",
        )
        key_one = store.identity_key(
            connector_one.charger_id, connector_one.connector_id
        )
        key_two = store.identity_key(
            connector_two.charger_id, connector_two.connector_id
        )
        store.transactions[key_one] = tx_one
        store.transactions[key_two] = tx_two
        try:
            resp = self.client.get(
                reverse("charger-status", args=[aggregate.charger_id])
            )
            chart = resp.context["chart_data"]
            self.assertTrue(resp.context["show_chart"])
            self.assertEqual(len(chart["datasets"]), 2)
            data_map = {
                dataset["label"]: dataset["values"] for dataset in chart["datasets"]
            }
            connector_id_map = {
                dataset["label"]: dataset.get("connector_id")
                for dataset in chart["datasets"]
            }
            label_one = str(connector_one.connector_label)
            label_two = str(connector_two.connector_label)
            self.assertEqual(set(data_map), {label_one, label_two})
            self.assertEqual(len(data_map[label_one]), len(chart["labels"]))
            self.assertEqual(len(data_map[label_two]), len(chart["labels"]))
            self.assertTrue(any(value is not None for value in data_map[label_one]))
            self.assertTrue(any(value is not None for value in data_map[label_two]))
            self.assertEqual(connector_id_map[label_one], connector_one.connector_id)
            self.assertEqual(connector_id_map[label_two], connector_two.connector_id)
        finally:
            store.transactions.pop(key_one, None)
            store.transactions.pop(key_two, None)


class ChargerApiDiagnosticsTests(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(username="diagapi", password="pwd")
        self.client.force_login(self.user)

    def test_detail_includes_diagnostics_fields(self):
        reported_at = timezone.now().replace(microsecond=0)
        charger = Charger.objects.create(
            charger_id="APIDIAG",
            diagnostics_status="Uploaded",
            diagnostics_timestamp=reported_at,
            diagnostics_location="https://example.com/diag.tar",
        )

        resp = self.client.get(reverse("charger-detail", args=[charger.charger_id]))
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(payload["diagnosticsStatus"], "Uploaded")
        self.assertEqual(
            payload["diagnosticsTimestamp"], reported_at.isoformat()
        )
        self.assertEqual(
            payload["diagnosticsLocation"], "https://example.com/diag.tar"
        )

    def test_list_includes_diagnostics_fields(self):
        reported_at = timezone.now().replace(microsecond=0)
        Charger.objects.create(
            charger_id="APILIST",
            diagnostics_status="Idle",
            diagnostics_timestamp=reported_at,
            diagnostics_location="s3://bucket/diag.zip",
        )

        resp = self.client.get(reverse("charger-list"))
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn("chargers", payload)
        target = next(
            item
            for item in payload["chargers"]
            if item["charger_id"] == "APILIST" and item["connector_id"] is None
        )
        self.assertEqual(target["diagnosticsStatus"], "Idle")
        self.assertEqual(target["diagnosticsLocation"], "s3://bucket/diag.zip")
        self.assertEqual(target["diagnosticsTimestamp"], reported_at.isoformat())


class ChargerSessionPaginationTests(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(username="page", password="pwd")
        self.client.force_login(self.user)
        self.charger = Charger.objects.create(charger_id="PAGETEST")
        for i in range(15):
            Transaction.objects.create(
                charger=self.charger,
                start_time=timezone.now() - timedelta(minutes=i),
                meter_start=0,
            )

    def test_only_ten_transactions_shown(self):
        resp = self.client.get(
            reverse("charger-status", args=[self.charger.charger_id])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["transactions"]), 10)
        self.assertTrue(resp.context["page_obj"].has_next())

    def test_session_search_by_date(self):
        date_str = timezone.now().date().isoformat()
        resp = self.client.get(
            reverse("charger-session-search", args=[self.charger.charger_id]),
            {"date": date_str},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["transactions"]), 15)


class LiveUpdateViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="lu", password="pw")
        self.client.force_login(self.user)

    def test_dashboard_includes_interval(self):
        resp = self.client.get(reverse("ocpp-dashboard"))
        self.assertEqual(resp.context["request"].live_update_interval, 5)
        self.assertContains(resp, "setInterval(() => location.reload()")

    def test_dashboard_aggregate_shows_charging_when_all_connectors_busy(self):
        aggregate = Charger.objects.create(
            charger_id="DASHAGG-CHG", last_status="Available"
        )
        conn1 = Charger.objects.create(
            charger_id=aggregate.charger_id, connector_id=1, last_status="Charging"
        )
        conn2 = Charger.objects.create(
            charger_id=aggregate.charger_id, connector_id=2, last_status="Charging"
        )

        resp = self.client.get(reverse("ocpp-dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context)
        context = resp.context
        charging_label = force_str(STATUS_BADGE_MAP["charging"][0])
        aggregate_entry = next(
            item
            for item in context["chargers"]
            if item["charger"].charger_id == aggregate.charger_id
            and item["charger"].connector_id is None
        )
        self.assertEqual(aggregate_entry["state"], charging_label)

        # Ensure connector rows remain untouched
        connector_states = {
            item["charger"].connector_id: item["state"]
            for item in context["chargers"]
            if item["charger"].charger_id == aggregate.charger_id
            and item["charger"].connector_id is not None
        }
        self.assertEqual(connector_states[conn1.connector_id], charging_label)
        self.assertEqual(connector_states[conn2.connector_id], charging_label)

    def test_dashboard_aggregate_shows_available_when_any_connector_free(self):
        aggregate = Charger.objects.create(
            charger_id="DASHAGG-AVL", last_status="Charging"
        )
        Charger.objects.create(
            charger_id=aggregate.charger_id, connector_id=1, last_status="Charging"
        )
        Charger.objects.create(
            charger_id=aggregate.charger_id, connector_id=2, last_status="Available"
        )

        resp = self.client.get(reverse("ocpp-dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context)
        context = resp.context
        available_label = force_str(STATUS_BADGE_MAP["available"][0])
        aggregate_entry = next(
            item
            for item in context["chargers"]
            if item["charger"].charger_id == aggregate.charger_id
            and item["charger"].connector_id is None
        )
        self.assertEqual(aggregate_entry["state"], available_label)

    def test_dashboard_connector_treats_finishing_as_available_without_session(self):
        charger = Charger.objects.create(
            charger_id="FINISH-STATE",
            connector_id=1,
            last_status="Finishing",
        )

        resp = self.client.get(reverse("ocpp-dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context)
        context = resp.context
        available_label = force_str(STATUS_BADGE_MAP["available"][0])
        entry = next(
            item
            for item in context["chargers"]
            if item["charger"].pk == charger.pk
        )
        self.assertEqual(entry["state"], available_label)

    def test_dashboard_aggregate_treats_finishing_as_available_without_session(self):
        aggregate = Charger.objects.create(
            charger_id="FINISH-AGG",
            connector_id=None,
            last_status="Finishing",
        )
        Charger.objects.create(
            charger_id=aggregate.charger_id,
            connector_id=1,
            last_status="Finishing",
        )

        resp = self.client.get(reverse("ocpp-dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context)
        context = resp.context
        available_label = force_str(STATUS_BADGE_MAP["available"][0])
        aggregate_entry = next(
            item
            for item in context["chargers"]
            if item["charger"].pk == aggregate.pk
        )
        self.assertEqual(aggregate_entry["state"], available_label)

    def test_dashboard_aggregate_uses_connection_when_status_missing(self):
        aggregate = Charger.objects.create(
            charger_id="DASHAGG-CONN", last_status="Charging"
        )
        connector = Charger.objects.create(
            charger_id=aggregate.charger_id,
            connector_id=1,
        )
        store.set_connection(connector.charger_id, connector.connector_id, object())
        self.addCleanup(
            lambda: store.pop_connection(connector.charger_id, connector.connector_id)
        )

        resp = self.client.get(reverse("ocpp-dashboard"))
        self.assertEqual(resp.status_code, 200)
        available_label = force_str(STATUS_BADGE_MAP["available"][0])
        aggregate_entry = next(
            item
            for item in resp.context["chargers"]
            if item["charger"].charger_id == aggregate.charger_id
            and item["charger"].connector_id is None
        )
        self.assertEqual(aggregate_entry["state"], available_label)

    def test_cp_simulator_includes_interval(self):
        resp = self.client.get(reverse("cp-simulator"))
        self.assertEqual(resp.context["request"].live_update_interval, 5)
        self.assertContains(resp, "setInterval(() => location.reload()")

    def test_dashboard_hides_private_chargers(self):
        public = Charger.objects.create(charger_id="PUBLICCP")
        private = Charger.objects.create(
            charger_id="PRIVATECP", public_display=False
        )

        resp = self.client.get(reverse("ocpp-dashboard"))
        chargers = [item["charger"] for item in resp.context["chargers"]]
        self.assertIn(public, chargers)
        self.assertNotIn(private, chargers)

        list_response = self.client.get(reverse("charger-list"))
        payload = list_response.json()
        ids = [item["charger_id"] for item in payload["chargers"]]
        self.assertIn(public.charger_id, ids)
        self.assertNotIn(private.charger_id, ids)

    def test_dashboard_restricts_to_owner_users(self):
        User = get_user_model()
        owner = User.objects.create_user(username="owner", password="pw")
        other = User.objects.create_user(username="outsider", password="pw")
        unrestricted = Charger.objects.create(charger_id="UNRESTRICTED")
        restricted = Charger.objects.create(charger_id="RESTRICTED")
        restricted.owner_users.add(owner)

        self.client.force_login(owner)
        owner_resp = self.client.get(reverse("ocpp-dashboard"))
        owner_chargers = [item["charger"] for item in owner_resp.context["chargers"]]
        self.assertIn(unrestricted, owner_chargers)
        self.assertIn(restricted, owner_chargers)

        self.client.force_login(other)
        other_resp = self.client.get(reverse("ocpp-dashboard"))
        other_chargers = [item["charger"] for item in other_resp.context["chargers"]]
        self.assertIn(unrestricted, other_chargers)
        self.assertNotIn(restricted, other_chargers)

        self.client.force_login(owner)
        detail_resp = self.client.get(
            reverse("charger-page", args=[restricted.charger_id])
        )
        self.assertEqual(detail_resp.status_code, 200)

        self.client.force_login(other)
        denied_resp = self.client.get(
            reverse("charger-page", args=[restricted.charger_id])
        )
        self.assertEqual(denied_resp.status_code, 404)

    def test_dashboard_restricts_to_owner_groups(self):
        User = get_user_model()
        group = SecurityGroup.objects.create(name="Operations")
        member = User.objects.create_user(username="member", password="pw")
        outsider = User.objects.create_user(username="visitor", password="pw")
        member.groups.add(group)
        unrestricted = Charger.objects.create(charger_id="GROUPFREE")
        restricted = Charger.objects.create(charger_id="GROUPLOCKED")
        restricted.owner_groups.add(group)

        self.client.force_login(member)
        member_resp = self.client.get(reverse("ocpp-dashboard"))
        member_chargers = [item["charger"] for item in member_resp.context["chargers"]]
        self.assertIn(unrestricted, member_chargers)
        self.assertIn(restricted, member_chargers)

        self.client.force_login(outsider)
        outsider_resp = self.client.get(reverse("ocpp-dashboard"))
        outsider_chargers = [item["charger"] for item in outsider_resp.context["chargers"]]
        self.assertIn(unrestricted, outsider_chargers)
        self.assertNotIn(restricted, outsider_chargers)

        self.client.force_login(member)
        status_resp = self.client.get(
            reverse("charger-status", args=[restricted.charger_id])
        )
        self.assertEqual(status_resp.status_code, 200)

        self.client.force_login(outsider)
        group_denied = self.client.get(
            reverse("charger-status", args=[restricted.charger_id])
        )
        self.assertEqual(group_denied.status_code, 404)

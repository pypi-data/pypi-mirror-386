from __future__ import annotations

from pathlib import Path
import tempfile
from unittest import mock

from django.contrib import messages
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import SimpleTestCase, RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone

from core import system


class UpgradeReportTests(SimpleTestCase):
    databases = {"default"}

    def setUp(self):
        self.factory = RequestFactory()

    def test_build_auto_upgrade_report_reads_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            locks_dir = base / "locks"
            logs_dir = base / "logs"
            locks_dir.mkdir()
            logs_dir.mkdir()

            (locks_dir / "auto_upgrade.lck").write_text("latest", encoding="utf-8")
            (locks_dir / "auto_upgrade_skip_revisions.lck").write_text(
                "abc123\n\nxyz789\n",
                encoding="utf-8",
            )
            (logs_dir / "auto-upgrade.log").write_text(
                "2024-01-01T00:00:00+00:00 first run\n"
                "2024-01-01T01:00:00+00:00 second run\n",
                encoding="utf-8",
            )

            schedule_stub = {
                "available": False,
                "configured": False,
                "enabled": False,
                "one_off": False,
                "queue": "",
                "schedule": "",
                "start_time": "",
                "last_run_at": "",
                "next_run": "",
                "total_run_count": 0,
                "description": "",
                "expires": "",
                "task": "",
                "name": system.AUTO_UPGRADE_TASK_NAME,
                "error": "",
            }

            with override_settings(BASE_DIR=str(base)):
                with mock.patch(
                    "core.system._load_auto_upgrade_schedule",
                    return_value=schedule_stub,
                ):
                    report = system._build_auto_upgrade_report(limit=10)

        self.assertTrue(report["settings"]["enabled"])
        self.assertTrue(report["settings"]["is_latest"])
        self.assertEqual(report["settings"]["mode"], "latest")
        self.assertEqual(
            report["settings"]["skip_revisions"],
            ["abc123", "xyz789"],
        )
        self.assertEqual(
            [entry["message"] for entry in report["log_entries"]],
            ["first run", "second run"],
        )
        self.assertFalse(report["log_error"])
        self.assertTrue(report["settings"]["log_path"].endswith("auto-upgrade.log"))

    def test_load_auto_upgrade_schedule_uses_task_metadata(self):
        class DummySchedule:
            def __str__(self) -> str:
                return "every 5 minutes"

        class DummyTask:
            def __init__(self):
                self.enabled = True
                self.one_off = False
                self.queue = "default"
                self.total_run_count = 7
                self.description = "Auto-upgrade"
                self.task = "core.tasks.check_github_updates"
                self.name = system.AUTO_UPGRADE_TASK_NAME
                self.start_time = timezone.now()
                self.last_run_at = timezone.now()
                self.expires = None
                self._schedule = DummySchedule()

            @property
            def schedule(self):
                return self._schedule

        dummy_task = DummyTask()
        expected_start = system._format_timestamp(dummy_task.start_time)
        expected_last_run = system._format_timestamp(dummy_task.last_run_at)

        with mock.patch(
            "core.system._get_auto_upgrade_periodic_task",
            return_value=(dummy_task, True, ""),
        ), mock.patch(
            "core.system._auto_upgrade_next_check",
            return_value="Soon",
        ):
            info = system._load_auto_upgrade_schedule()

        self.assertTrue(info["available"])
        self.assertTrue(info["configured"])
        self.assertTrue(info["enabled"])
        self.assertEqual(info["schedule"], "every 5 minutes")
        self.assertEqual(info["next_run"], "Soon")
        self.assertEqual(info["total_run_count"], 7)
        self.assertEqual(info["task"], dummy_task.task)
        self.assertEqual(info["name"], dummy_task.name)
        self.assertEqual(info["start_time"], expected_start)
        self.assertEqual(info["last_run_at"], expected_last_run)

    def test_trigger_upgrade_check_uses_async_queue(self):
        with mock.patch("core.system.check_github_updates") as mock_task:
            mock_task.delay = mock.Mock()

            queued = system._trigger_upgrade_check()

        self.assertTrue(queued)
        mock_task.delay.assert_called_once_with()
        mock_task.assert_not_called()

    def test_trigger_upgrade_check_falls_back_to_sync(self):
        with mock.patch("core.system.check_github_updates") as mock_task:
            mock_task.delay = mock.Mock(side_effect=RuntimeError("broker down"))

            queued = system._trigger_upgrade_check()

        self.assertFalse(queued)
        mock_task.delay.assert_called_once_with()
        mock_task.assert_called_once_with()

    def test_trigger_upgrade_check_view_adds_success_message(self):
        request = self.factory.post(reverse("admin:system-upgrade-run-check"))
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        setattr(request, "_messages", FallbackStorage(request))
        request.user = mock.Mock(is_staff=True, is_active=True)

        with mock.patch("core.system._trigger_upgrade_check", return_value=True):
            response = system._system_trigger_upgrade_check_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin:system-upgrade-report"))
        stored = list(messages.get_messages(request))
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].level, messages.SUCCESS)

    def test_trigger_upgrade_check_view_reports_error(self):
        request = self.factory.post(reverse("admin:system-upgrade-run-check"))
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        setattr(request, "_messages", FallbackStorage(request))
        request.user = mock.Mock(is_staff=True, is_active=True)

        with mock.patch(
            "core.system._trigger_upgrade_check",
            side_effect=RuntimeError("oops"),
        ):
            response = system._system_trigger_upgrade_check_view(request)

        self.assertEqual(response.status_code, 302)
        stored = list(messages.get_messages(request))
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].level, messages.ERROR)

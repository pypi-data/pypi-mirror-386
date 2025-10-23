import pathlib

import pytest

from config import settings_helpers


def _original_validate(host, allowed_hosts):
    return host in allowed_hosts


class TestValidateHostWithSubnets:
    def test_accepts_ipv4_within_allowed_subnet(self):
        allowed = ["example.com", "192.168.1.0/24"]

        assert settings_helpers.validate_host_with_subnets(
            "192.168.1.42",
            allowed,
            original_validate=_original_validate,
        )

    def test_accepts_ipv6_literal_with_port(self):
        allowed = ["2001:db8::/32"]

        assert settings_helpers.validate_host_with_subnets(
            "[2001:db8::1]:8443",
            allowed,
            original_validate=_original_validate,
        )

    def test_falls_back_to_original_validator(self):
        allowed = ["example.com", "10.0.0.0/24"]

        assert not settings_helpers.validate_host_with_subnets(
            "10.1.0.5",
            allowed,
            original_validate=_original_validate,
        )


class TestLoadSecretKey:
    def test_prefers_environment_variables(self, tmp_path: pathlib.Path):
        env = {"DJANGO_SECRET_KEY": "env-secret"}

        result = settings_helpers.load_secret_key(tmp_path, env=env)

        assert result == "env-secret"

    def test_reads_existing_secret_file(self, tmp_path: pathlib.Path):
        secret_file = tmp_path / "locks" / "django-secret.key"
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        secret_file.write_text("stored-secret", encoding="utf-8")

        result = settings_helpers.load_secret_key(tmp_path, env={})

        assert result == "stored-secret"

    def test_generates_and_persists_secret(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
        generated = "generated-secret"
        monkeypatch.setattr(
            settings_helpers,
            "get_random_secret_key",
            lambda: generated,
        )

        result = settings_helpers.load_secret_key(tmp_path, env={})

        secret_file = tmp_path / "locks" / "django-secret.key"
        assert result == generated
        assert secret_file.read_text(encoding="utf-8") == generated

    def test_regenerates_when_secret_file_blank(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        secret_file = tmp_path / "locks" / "django-secret.key"
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        secret_file.write_text("\n", encoding="utf-8")

        regenerated = "regenerated-secret"
        monkeypatch.setattr(
            settings_helpers,
            "get_random_secret_key",
            lambda: regenerated,
        )

        result = settings_helpers.load_secret_key(tmp_path, env={})

        assert result == regenerated
        assert secret_file.read_text(encoding="utf-8") == regenerated

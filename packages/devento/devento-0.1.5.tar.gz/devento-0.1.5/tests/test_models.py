"""Tests for Devento models."""

from datetime import datetime
import pytest

from devento import (
    Box,
    BoxStatus,
    BoxConfig,
    CommandResult,
    CommandStatus,
    CommandOptions,
    Domain,
    DomainKind,
    DomainStatus,
    DomainMeta,
    DomainResponse,
    DomainsResponse,
)


class TestModels:
    """Test data models."""

    def test_box_status_enum(self):
        """Test BoxStatus enum values."""
        assert BoxStatus.CREATING.value == "creating"
        assert BoxStatus.QUEUED.value == "queued"
        assert BoxStatus.PROVISIONING.value == "provisioning"
        assert BoxStatus.BOOTING.value == "booting"
        assert BoxStatus.RUNNING.value == "running"
        assert BoxStatus.PAUSED.value == "paused"
        assert BoxStatus.STOPPED.value == "stopped"
        assert BoxStatus.FAILED.value == "failed"
        assert BoxStatus.FINISHED.value == "finished"
        assert BoxStatus.ERROR.value == "error"

    def test_command_status_enum(self):
        """Test CommandStatus enum values."""
        assert CommandStatus.QUEUED.value == "queued"
        assert CommandStatus.RUNNING.value == "running"
        assert CommandStatus.DONE.value == "done"
        assert CommandStatus.FAILED.value == "failed"
        assert CommandStatus.ERROR.value == "error"

    def test_box_config_defaults(self):
        """Test BoxConfig default values."""
        config = BoxConfig()
        assert config.cpu is None
        assert config.mib_ram is None
        assert config.timeout == 600
        assert config.metadata is None

    def test_box_config_with_cpu(self):
        """Test BoxConfig with specific CPU."""
        config = BoxConfig(cpu=4)
        assert config.cpu == 4
        assert config.mib_ram is None

    def test_box_config_with_mib_ram(self):
        """Test BoxConfig with specific RAM."""
        config = BoxConfig(mib_ram=8192)
        assert config.cpu is None
        assert config.mib_ram == 8192

    def test_box_config_with_cpu_and_ram(self):
        """Test BoxConfig with both CPU and RAM."""
        config = BoxConfig(cpu=2, mib_ram=4096)
        assert config.cpu == 2
        assert config.mib_ram == 4096

    def test_box_config_with_metadata(self):
        """Test BoxConfig with metadata."""
        metadata = {"project": "test", "user": "john"}
        config = BoxConfig(metadata=metadata)
        assert config.metadata == metadata

    def test_command_result(self):
        """Test CommandResult dataclass."""
        result = CommandResult(
            id="cmd-123",
            command="echo 'hello'",
            status=CommandStatus.DONE,
            stdout="hello\n",
            stderr="",
            exit_code=0,
            created_at=datetime.now(),
        )

        assert result.id == "cmd-123"
        assert result.command == "echo 'hello'"
        assert result.status == CommandStatus.DONE
        assert result.stdout == "hello\n"
        assert result.stderr == ""
        assert result.exit_code == 0
        assert isinstance(result.created_at, datetime)

    def test_box_model(self):
        """Test Box dataclass."""
        box = Box(
            id="box-123",
            status=BoxStatus.RUNNING,
            timeout=600,
            created_at=datetime.now(),
            metadata={"test": "value"},
            details="Running successfully",
        )

        assert box.id == "box-123"
        assert box.status == BoxStatus.RUNNING
        assert box.timeout == 600
        assert isinstance(box.created_at, datetime)
        assert box.metadata == {"test": "value"}
        assert box.details == "Running successfully"

    def test_box_model_with_hostname(self):
        """Test Box dataclass with hostname."""
        box = Box(
            id="box-456",
            status=BoxStatus.RUNNING,
            hostname="box456.deven.to",
        )

        assert box.id == "box-456"
        assert box.hostname == "box456.deven.to"

    def test_box_get_public_url(self):
        """Test Box.get_public_url method."""
        box = Box(
            id="box-789",
            status=BoxStatus.RUNNING,
            hostname="box789.deven.to",
        )

        # Test valid port
        url = box.get_public_url(8080)
        assert url == "https://8080-box789.deven.to"

        # Test another port
        url = box.get_public_url(3000)
        assert url == "https://3000-box789.deven.to"

    def test_box_get_public_url_without_hostname(self):
        """Test Box.get_public_url raises error when hostname is None."""
        box = Box(
            id="box-999",
            status=BoxStatus.RUNNING,
            hostname=None,
        )

        with pytest.raises(ValueError, match="Box does not have a hostname"):
            box.get_public_url(8080)

    def test_command_options(self):
        """Test CommandOptions dataclass."""

        def stdout_handler(line):
            print(line)

        def stderr_handler(line):
            print(line)

        options = CommandOptions(
            timeout=30.0,
            on_stdout=stdout_handler,
            on_stderr=stderr_handler,
            poll_interval=0.5,
        )

        assert options.timeout == 30.0
        assert options.on_stdout == stdout_handler
        assert options.on_stderr == stderr_handler
        assert options.poll_interval == 0.5

    def test_command_options_defaults(self):
        """Test CommandOptions default values."""
        options = CommandOptions()
        assert options.timeout is None
        assert options.on_stdout is None
        assert options.on_stderr is None
        assert options.poll_interval == 1.0

    def test_domain_enums(self):
        """Test domain enum values."""
        assert DomainKind.MANAGED.value == "managed"
        assert DomainKind.CUSTOM.value == "custom"
        assert DomainStatus.PENDING_DNS.value == "pending_dns"
        assert DomainStatus.PENDING_SSL.value == "pending_ssl"
        assert DomainStatus.ACTIVE.value == "active"
        assert DomainStatus.FAILED.value == "failed"
        assert DomainStatus.DISABLED.value == "disabled"

    def test_domain_dataclass(self):
        """Test Domain dataclass construction."""
        domain = Domain(
            id="dom_123",
            hostname="app.deven.to",
            slug="app",
            kind=DomainKind.MANAGED,
            status=DomainStatus.ACTIVE,
            target_port=443,
            box_id="box_123",
            cloudflare_id=None,
            verification_payload={"cname": "edge.deven.to"},
            verification_errors={},
            inserted_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T12:00:00Z",
        )

        assert domain.kind is DomainKind.MANAGED
        assert domain.status is DomainStatus.ACTIVE
        assert domain.hostname == "app.deven.to"
        assert domain.verification_payload == {"cname": "edge.deven.to"}

    def test_domain_response_wrappers(self):
        """Test domain response dataclasses."""
        domain = Domain(
            id="dom_123",
            hostname="app.deven.to",
            slug="app",
            kind=DomainKind.MANAGED,
            status=DomainStatus.ACTIVE,
            target_port=80,
            box_id="box_123",
            cloudflare_id="cf_123",
            verification_payload=None,
            verification_errors=None,
            inserted_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:30:00Z",
        )
        meta = DomainMeta(managed_suffix="deven.to", cname_target="edge.deven.to")

        domains_response = DomainsResponse(data=[domain], meta=meta)
        domain_response = DomainResponse(data=domain, meta=meta)

        assert domains_response.data[0].id == "dom_123"
        assert domains_response.meta.cname_target == "edge.deven.to"
        assert domain_response.data.hostname == "app.deven.to"

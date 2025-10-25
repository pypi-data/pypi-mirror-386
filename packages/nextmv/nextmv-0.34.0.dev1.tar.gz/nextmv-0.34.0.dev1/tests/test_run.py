import datetime
import time
import unittest

from nextmv.run import (
    Format,
    FormatInput,
    FormatOutput,
    Metadata,
    Run,
    RunInformation,
    RunTypeConfiguration,
    run_duration,
)
from nextmv.status import Status, StatusV2


class TestRunDuration(unittest.TestCase):
    def test_run_duration_convenience_func(self):
        before_t, before_dt = time.time(), datetime.datetime.now()
        diff = 0.25
        after_t, after_dt = before_t + diff, before_dt + datetime.timedelta(seconds=diff)
        duration_t = run_duration(before_t, after_t)
        duration_dt = run_duration(before_dt, after_dt)
        self.assertAlmostEqual(duration_t, 250.0, delta=1.0)
        self.assertAlmostEqual(duration_dt, 250.0, delta=1.0)
        self.assertIsInstance(duration_t, int)
        self.assertIsInstance(duration_dt, int)


class TestRunInformationToRun(unittest.TestCase):
    def setUp(self):
        """Set up test data for RunInformation to_run() tests."""
        self.created_at = datetime.datetime(2023, 10, 15, 14, 30, 0)

        # Create a complete metadata object
        self.metadata = Metadata(
            application_id="app-12345",
            application_instance_id="instance-67890",
            application_version_id="version-11111",
            created_at=self.created_at,
            duration=5000.0,
            error="",
            input_size=1024.0,
            output_size=2048.0,
            format=Format(format_input=FormatInput(), format_output=FormatOutput()),
            status_v2=StatusV2.succeeded,
            status=Status.succeeded,
        )

        # Create a RunInformation instance
        self.run_info = RunInformation(
            id="run-98765",
            description="Test optimization run",
            name="Test Run",
            user_email="test@example.com",
            metadata=self.metadata,
            console_url="https://console.nextmv.io/run/run-98765",
            synced_run_id="synced-12345",
            synced_at=datetime.datetime(2023, 10, 15, 15, 0, 0),
        )

    def test_to_run_basic_transformation(self):
        """Test basic transformation from RunInformation to Run."""
        run = self.run_info.to_run()

        # Test that the result is a Run instance
        self.assertIsInstance(run, Run)

        # Test direct mappings from RunInformation
        self.assertEqual(run.id, self.run_info.id)
        self.assertEqual(run.user_email, self.run_info.user_email)
        self.assertEqual(run.name, self.run_info.name)
        self.assertEqual(run.description, self.run_info.description)

        # Test mappings from metadata
        self.assertEqual(run.created_at, self.metadata.created_at)
        self.assertEqual(run.application_id, self.metadata.application_id)
        self.assertEqual(run.application_instance_id, self.metadata.application_instance_id)
        self.assertEqual(run.application_version_id, self.metadata.application_version_id)
        self.assertEqual(run.status, self.metadata.status)
        self.assertEqual(run.status_v2, self.metadata.status_v2)

    def test_to_run_default_values(self):
        """Test that unavailable attributes are set to appropriate defaults."""
        run = self.run_info.to_run()

        # Test default RunTypeConfiguration
        self.assertIsInstance(run.run_type, RunTypeConfiguration)
        self.assertIsNone(run.run_type.run_type)
        self.assertIsNone(run.run_type.definition_id)
        self.assertIsNone(run.run_type.reference_id)

        # Test empty string defaults
        self.assertEqual(run.execution_class, "")
        self.assertEqual(run.runtime, "")

        # Test None defaults for optional fields
        self.assertIsNone(run.queuing_priority)
        self.assertIsNone(run.queuing_disabled)
        self.assertIsNone(run.experiment_id)
        self.assertIsNone(run.statistics)
        self.assertIsNone(run.input_id)
        self.assertIsNone(run.option_set)
        self.assertIsNone(run.options)
        self.assertIsNone(run.request_options)
        self.assertIsNone(run.options_summary)
        self.assertIsNone(run.scenario_id)
        self.assertIsNone(run.repetition)
        self.assertIsNone(run.input_set_id)

    def test_to_run_with_minimal_metadata(self):
        """Test transformation with minimal metadata (only status without deprecated status)."""
        minimal_metadata = Metadata(
            application_id="app-minimal",
            application_instance_id="instance-minimal",
            application_version_id="version-minimal",
            created_at=self.created_at,
            duration=1000.0,
            error="Test error",
            input_size=512.0,
            output_size=1024.0,
            format=Format(format_input=FormatInput(), format_output=FormatOutput()),
            status_v2=StatusV2.failed,
            status=Status.failed,  # Add required status field
        )

        run_info_minimal = RunInformation(
            id="run-minimal",
            description="Minimal test",
            name="Minimal",
            user_email="minimal@example.com",
            metadata=minimal_metadata,
        )

        run = run_info_minimal.to_run()

        # Test that transformation works with minimal data
        self.assertEqual(run.id, "run-minimal")
        self.assertEqual(run.application_id, "app-minimal")
        self.assertEqual(run.status_v2, StatusV2.failed)
        self.assertEqual(run.status, Status.failed)  # Status is now provided

    def test_to_run_preserves_datetime_objects(self):
        """Test that datetime objects are properly preserved during transformation."""
        run = self.run_info.to_run()

        # Test that datetime objects are preserved and are the same instance
        self.assertIs(run.created_at, self.metadata.created_at)
        self.assertEqual(run.created_at, self.created_at)
        self.assertIsInstance(run.created_at, datetime.datetime)

    def test_to_run_multiple_transformations(self):
        """Test that multiple transformations from the same RunInformation work correctly."""
        run1 = self.run_info.to_run()
        run2 = self.run_info.to_run()

        # Test that both transformations produce equivalent results
        self.assertEqual(run1.id, run2.id)
        self.assertEqual(run1.user_email, run2.user_email)
        self.assertEqual(run1.name, run2.name)
        self.assertEqual(run1.description, run2.description)
        self.assertEqual(run1.created_at, run2.created_at)
        self.assertEqual(run1.application_id, run2.application_id)
        self.assertEqual(run1.status_v2, run2.status_v2)

        # Test that they are different instances
        self.assertIsNot(run1, run2)
        self.assertIsNot(run1.run_type, run2.run_type)

    def test_to_run_with_different_status_values(self):
        """Test transformation with different status values."""
        # Test with different StatusV2 values
        status_values = [StatusV2.succeeded, StatusV2.failed, StatusV2.running, StatusV2.queued]

        for status_v2 in status_values:
            with self.subTest(status_v2=status_v2):
                # Map StatusV2 to Status for compatibility
                status_mapping = {
                    StatusV2.succeeded: Status.succeeded,
                    StatusV2.failed: Status.failed,
                    StatusV2.running: Status.running,
                    StatusV2.queued: Status.running,  # Map queued to running since Status doesn't have queued
                }
                metadata = Metadata(
                    application_id="app-test",
                    application_instance_id="instance-test",
                    application_version_id="version-test",
                    created_at=self.created_at,
                    duration=2000.0,
                    error="",
                    input_size=256.0,
                    output_size=512.0,
                    format=Format(format_input=FormatInput(), format_output=FormatOutput()),
                    status_v2=status_v2,
                    status=status_mapping[status_v2],
                )

                run_info = RunInformation(
                    id=f"run-{status_v2.value}",
                    description=f"Test with {status_v2.value}",
                    name="Status Test",
                    user_email="status@example.com",
                    metadata=metadata,
                )

                run = run_info.to_run()
                self.assertEqual(run.status_v2, status_v2)

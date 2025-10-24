import random
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from core.choices import DataSourceStatusChoices
from core.choices import JobStatusChoices
from core.models import Job
from dcim.models import Device
from dcim.models import DeviceRole
from dcim.models import DeviceType
from dcim.models import Manufacturer
from dcim.models import Site
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models import Model
from django.forms.models import model_to_dict
from django.test import override_settings
from django.utils import timezone
from netbox_branching.models import Branch
from netbox_branching.models import ChangeDiff
from utilities.testing import ModelTestCase
from utilities.testing import ViewTestCases

from ipfabric_netbox.choices import IPFabricSnapshotStatusModelChoices
from ipfabric_netbox.choices import IPFabricSourceTypeChoices
from ipfabric_netbox.forms import dcim_parameters
from ipfabric_netbox.forms import ipam_parameters
from ipfabric_netbox.forms import tableChoices
from ipfabric_netbox.jobs import merge_ipfabric_ingestion
from ipfabric_netbox.models import IPFabricData
from ipfabric_netbox.models import IPFabricIngestion
from ipfabric_netbox.models import IPFabricRelationshipField
from ipfabric_netbox.models import IPFabricSnapshot
from ipfabric_netbox.models import IPFabricSource
from ipfabric_netbox.models import IPFabricSync
from ipfabric_netbox.models import IPFabricTransformField
from ipfabric_netbox.models import IPFabricTransformMap
from ipfabric_netbox.models import IPFabricTransformMapGroup
from ipfabric_netbox.tables import DeviceIPFTable


class PluginPathMixin:
    """Mixin to correct URL Paths for plugin test."""

    maxDiff = 1000

    model: Model  # To avoid unresolved attribute warning

    def _get_model_name(self):
        return self.model._meta.model_name

    def _get_base_url(self):
        return f"plugins:ipfabric_netbox:{self._get_model_name()}_{{}}"  # noqa: E231


class IPFabricSourceTestCase(
    PluginPathMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
    ViewTestCases.BulkRenameObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    # ViewTestCases.BulkImportObjectsViewTestCase,
):
    model = IPFabricSource
    user_permissions = ("ipfabric_netbox.sync_ipfabricsource",)

    @classmethod
    def setUpTestData(cls):
        # Create three IPFabricSource instances for testing
        sources = (
            IPFabricSource(
                name="IP Fabric Source 1",
                type=IPFabricSourceTypeChoices.LOCAL,
                url="https://ipfabric1.example.com",
                status=DataSourceStatusChoices.NEW,
                parameters={"auth": "token1", "verify": True, "timeout": 30},
                last_synced=timezone.now(),
            ),
            IPFabricSource(
                name="IP Fabric Source 2",
                type=IPFabricSourceTypeChoices.LOCAL,
                url="https://ipfabric2.example.com",
                status=DataSourceStatusChoices.COMPLETED,
                parameters={"auth": "token2", "verify": False, "timeout": 60},
                last_synced=timezone.now(),
            ),
            IPFabricSource(
                name="IP Fabric Source 3",
                type=IPFabricSourceTypeChoices.LOCAL,
                url="https://ipfabric3.example.com",
                status=DataSourceStatusChoices.FAILED,
                parameters={"auth": "token3", "verify": True, "timeout": 45},
            ),
        )
        for source in sources:
            source.save()
            Job.objects.create(
                job_id=uuid4(),
                object_id=source.pk,
                object_type=ContentType.objects.get_for_model(IPFabricSource),
                name=f"Test Sync Job {source.pk}",
                status=JobStatusChoices.STATUS_COMPLETED,
                completed=timezone.now(),
                created=timezone.now(),
            )
        IPFabricSnapshot.objects.create(
            source=IPFabricSource.objects.first(),
            name="Snapshot 1",
            snapshot_id="$last",
            data={
                "version": "6.0.0",
                "sites": ["Site A", "Site B", "Site C"],
                "total_dev_count": 100,
                "interface_count": 500,
                "note": "Test snapshot 1",
            },
            date=timezone.now(),
            status=IPFabricSnapshotStatusModelChoices.STATUS_LOADED,
        )

        cls.site = Site.objects.create(name="Test Site", slug="test-site")

        cls.form_data = {
            "name": "IP Fabric Source X",
            "type": IPFabricSourceTypeChoices.LOCAL,
            "url": "https://ipfabricx.example.com",
            "auth": "tokenX",
            "verify": True,
            "timeout": 30,
            "comments": "This is a test IP Fabric source",
        }

        cls.csv_data = (
            "name,type,url,parameters",
            'IP Fabric Source 4,local,https://ipfabric4.example.com,"{""auth"": ""token4"", ""verify"": true}"',
            'IP Fabric Source 5,remote,https://ipfabric5.example.com,"{""auth"": ""token5"", ""verify"": false}"',
            'IP Fabric Source 6,local,https://ipfabric6.example.com,"{""auth"": ""token6"", ""verify"": true}"',
        )

        cls.csv_update_data = (
            "id,name,url",
            f"{sources[0].pk},IP Fabric Source 7,https://ipfabric7.example.com",  # noqa: E231
            f"{sources[1].pk},IP Fabric Source 8,https://ipfabric8.example.com",  # noqa: E231
            f"{sources[2].pk},IP Fabric Source 9,https://ipfabric9.example.com",  # noqa: E231
        )

        cls.bulk_edit_data = {
            "type": IPFabricSourceTypeChoices.REMOTE,
            "comments": "Bulk updated comment",
        }

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_topology(self):
        response = self.client.get(
            self._get_queryset().first().get_absolute_url()
            + f"topology/{self.site.pk}/"
        )
        self.assertHttpStatus(response, 200)
        # Verify the response contains expected modal structure
        self.assertContains(response, "modal-body")
        # Check that the context contains the site object
        self.assertIn("site", response.context)
        self.assertEqual(response.context["site"], self.site.id)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    @patch("ipfabric_netbox.utilities.ipfutils.IPFClient")
    def test_get_topology_htmx(self, mock_ipfclient_class):
        # Mock the IPFClient instance that gets created inside IPFabric.__init__
        mock_ipfclient_instance = mock_ipfclient_class.return_value
        mock_ipfclient_instance._client.headers = {"user-agent": "test-user-agent"}

        # Mock snapshot data - this is what ipf.ipf.snapshots.get(snapshot) returns
        mock_snapshot_data = {
            "id": "$last",
            "name": "Test Snapshot",
            "status": "done",
            "finish_status": "done",
            "end": "2024-01-15T10:30:00Z",
            "snapshot_id": "snapshot123",
            "version": "6.0.0",
            "sites": ["Test Site"],
            "total_dev_count": 10,
            "interface_count": 50,
        }
        mock_ipfclient_instance.snapshots.get.return_value = mock_snapshot_data

        # Mock site data - this is what ipf.ipf.inventory.sites.all() returns
        mock_sites_data = [
            {
                "siteName": "Test Site",
                "siteKey": "site123",
                "location": "Test Location",
                "deviceCount": 5,
            }
        ]
        mock_ipfclient_instance.inventory.sites.all.return_value = mock_sites_data

        # Mock diagram methods to avoid actual diagram generation
        mock_ipfclient_instance.diagram.share_link.return_value = (
            "https://ipfabric.example.com/diagram/share/123"
        )
        mock_ipfclient_instance.diagram.svg.return_value = (
            b'<svg><rect width="100" height="100" fill="blue"/></svg>'
        )

        response = self.client.get(
            self._get_queryset().first().get_absolute_url()
            + f"topology/{self.site.pk}/",
            **{"HTTP_HX-Request": "true"},
            query_params={
                "source": IPFabricSource.objects.first().pk,
                "snapshot": "$last",
            },
        )
        self.assertHttpStatus(response, 200)

        # Verify that the API calls were made with correct parameters
        mock_ipfclient_instance.snapshots.get.assert_called_once_with("$last")
        mock_ipfclient_instance.inventory.sites.all.assert_called_once_with(
            filters={"siteName": ["eq", "Test Site"]}
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    @patch("ipfabric_netbox.utilities.ipfutils.IPFClient")
    def test_get_topology_htmx_empty_snapshot_data(self, mock_ipfclient_class):
        # Mock the IPFClient instance that gets created inside IPFabric.__init__
        mock_ipfclient_instance = mock_ipfclient_class.return_value
        mock_ipfclient_instance._client.headers = {"user-agent": "test-user-agent"}

        # Mock empty snapshot data - this is what ipf.ipf.snapshots.get(snapshot) returns when snapshot doesn't exist
        mock_ipfclient_instance.snapshots.get.return_value = None

        response = self.client.get(
            self._get_queryset().first().get_absolute_url()
            + f"topology/{self.site.pk}/",
            **{"HTTP_HX-Request": "true"},
            query_params={
                "source": IPFabricSource.objects.first().pk,
                "snapshot": "$last",
            },
        )
        self.assertHttpStatus(response, 200)

        # Verify that the snapshot API was called but sites API was not called due to early exit
        mock_ipfclient_instance.snapshots.get.assert_called_once_with("$last")
        mock_ipfclient_instance.inventory.sites.all.assert_not_called()

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    @patch("ipfabric_netbox.utilities.ipfutils.IPFClient")
    def test_get_topology_htmx_empty_sites_data(self, mock_ipfclient_class):
        # Mock the IPFClient instance that gets created inside IPFabric.__init__
        mock_ipfclient_instance = mock_ipfclient_class.return_value
        mock_ipfclient_instance._client.headers = {"user-agent": "test-user-agent"}

        # Mock valid snapshot data
        mock_snapshot_data = {
            "id": "$last",
            "name": "Test Snapshot",
            "status": "done",
            "finish_status": "done",
            "end": "2024-01-15T10:30:00Z",
            "snapshot_id": "snapshot123",
            "version": "6.0.0",
            "sites": ["Test Site"],
            "total_dev_count": 10,
            "interface_count": 50,
        }
        mock_ipfclient_instance.snapshots.get.return_value = mock_snapshot_data

        # Mock empty site data - this is what ipf.ipf.inventory.sites.all() returns when site doesn't exist in snapshot
        mock_ipfclient_instance.inventory.sites.all.return_value = []

        response = self.client.get(
            self._get_queryset().first().get_absolute_url()
            + f"topology/{self.site.pk}/",
            **{"HTTP_HX-Request": "true"},
            query_params={
                "source": IPFabricSource.objects.first().pk,
                "snapshot": "$last",
            },
        )
        self.assertHttpStatus(response, 200)

        # Verify that both API calls were made
        mock_ipfclient_instance.snapshots.get.assert_called_once_with("$last")
        mock_ipfclient_instance.inventory.sites.all.assert_called_once_with(
            filters={"siteName": ["eq", "Test Site"]}
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_topology_htmx_no_source(self):
        response = self.client.get(
            self._get_queryset().first().get_absolute_url()
            + f"topology/{self.site.pk}/",
            **{"HTTP_HX-Request": "true"},
        )
        self.assertHttpStatus(response, 200)
        # Verify response contains HTMX content for no source scenario
        self.assertContains(response, "Source ID not available in request")
        # Check that context indicates no source selected
        self.assertIn("source", response.context)
        self.assertIsNone(response.context.get("source"))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_topology_htmx_no_snapshot(self):
        response = self.client.get(
            self._get_queryset().first().get_absolute_url()
            + f"topology/{self.site.pk}/",
            **{"HTTP_HX-Request": "true"},
            query_params={"source": IPFabricSource.objects.first().pk},
        )
        self.assertHttpStatus(response, 200)
        # Verify response contains HTMX content for no snapshot scenario
        self.assertContains(response, "Snapshot ID not available in request.")
        # Verify response indicates no snapshot selected
        self.assertIn("snapshot", response.context)
        self.assertIsNone(response.context.get("snapshot"))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_sync_view_get_redirect(self):
        """Test that GET request to sync view redirects to source detail page."""
        source = self._get_queryset().first()
        response = self.client.get(source.get_absolute_url() + "sync/")
        self.assertHttpStatus(response, 302)
        self.assertRedirects(response, source.get_absolute_url())

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    @patch("ipfabric_netbox.models.IPFabricSource.enqueue_sync_job")
    def test_sync_view_post_valid(self, mock_enqueue_sync_job):
        """Test POST request to sync view successfully enqueues sync job."""

        # Set up mock job
        mock_job = Job(pk=123, name="Test Source Sync Job")
        mock_enqueue_sync_job.return_value = mock_job

        source = self._get_queryset().first()

        response = self.client.post(source.get_absolute_url() + "sync/", follow=True)

        # Should redirect to source detail page
        self.assertHttpStatus(response, 200)
        self.assertRedirects(response, source.get_absolute_url())

        # Should have called enqueue_sync_job with correct parameters
        mock_enqueue_sync_job.assert_called_once()
        call_args = mock_enqueue_sync_job.call_args
        self.assertIn("request", call_args[1])

        # Should show success message
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn(f"Queued job #{mock_job.pk}", str(messages[0]))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_sync_view_nonexistent_source(self):
        """Test sync view with non-existent source returns 404."""
        nonexistent_pk = 99999
        response = self.client.post(
            f"/plugins/ipfabric-netbox/ipfabricsource/{nonexistent_pk}/sync/"
        )
        self.assertHttpStatus(response, 404)


class IPFabricSnapshotTestCase(
    PluginPathMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    # ViewTestCases.CreateObjectViewTestCase,
    # ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
    # ViewTestCases.BulkRenameObjectsViewTestCase,
    # ViewTestCases.BulkEditObjectsViewTestCase,
    # ViewTestCases.BulkImportObjectsViewTestCase,
):
    model = IPFabricSnapshot

    @classmethod
    def setUpTestData(cls):
        # Create IPFabricSource instances needed for snapshots
        source1 = IPFabricSource.objects.create(
            name="Test Source 1",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://ipfabric1.example.com",
            status=DataSourceStatusChoices.NEW,
        )
        source2 = IPFabricSource.objects.create(
            name="Test Source 2",
            type=IPFabricSourceTypeChoices.REMOTE,
            url="https://ipfabric2.example.com",
            status=DataSourceStatusChoices.COMPLETED,
        )

        # Create three IPFabricSnapshot instances for testing
        snapshots = (
            IPFabricSnapshot(
                source=source1,
                name="Snapshot 1",
                snapshot_id="snap001",
                data={
                    "version": "6.0.0",
                    "sites": ["Site A", "Site B", "Site C"],
                    "total_dev_count": 100,
                    "interface_count": 500,
                    "note": "Test snapshot 1",
                },
                date=timezone.now(),
                status=IPFabricSnapshotStatusModelChoices.STATUS_LOADED,
            ),
            IPFabricSnapshot(
                source=source1,
                name="Snapshot 2",
                snapshot_id="snap002",
                data={
                    "version": "6.0.1",
                    "sites": ["Site D", "Site E"],
                    "total_dev_count": 150,
                    "interface_count": 750,
                    "note": "Test snapshot 2",
                },
                date=timezone.now(),
                status=IPFabricSnapshotStatusModelChoices.STATUS_UNLOADED,
            ),
            IPFabricSnapshot(
                source=source2,
                name="Snapshot 3",
                snapshot_id="snap003",
                data={
                    "version": "6.1.0",
                    "sites": ["Site F", "Site G", "Site H", "Site I"],
                    "total_dev_count": 200,
                    "interface_count": 1000,
                    "note": "Test snapshot 3",
                },
                date=timezone.now(),
                status=IPFabricSnapshotStatusModelChoices.STATUS_LOADED,
            ),
        )
        for snapshot in snapshots:
            snapshot.save()
            IPFabricData.objects.create(snapshot_data=snapshot, type="device", data={})

        cls.form_data = {
            "source": source1.pk,
            "name": "Test Snapshot X",
            "snapshot_id": "snapX",
            "data": '{"version": "6.0.0", "sites": ["Site X"], "total_dev_count": 75, "interface_count": 375, "note": "Test snapshot X"}',
            "status": IPFabricSnapshotStatusModelChoices.STATUS_LOADED,
        }

        cls.csv_data = (
            "source,name,snapshot_id,status",
            f"{source1.pk},Snapshot CSV 1,snapcsv001,{IPFabricSnapshotStatusModelChoices.STATUS_LOADED}",  # noqa: E231
            f"{source1.pk},Snapshot CSV 2,snapcsv002,{IPFabricSnapshotStatusModelChoices.STATUS_UNLOADED}",  # noqa: E231
            f"{source2.pk},Snapshot CSV 3,snapcsv003,{IPFabricSnapshotStatusModelChoices.STATUS_LOADED}",  # noqa: E231
        )

        cls.csv_update_data = (
            "id,name,snapshot_id",
            f"{snapshots[0].pk},Updated Snapshot 1,updsnap001",  # noqa: E231
            f"{snapshots[1].pk},Updated Snapshot 2,updsnap002",  # noqa: E231
            f"{snapshots[2].pk},Updated Snapshot 3,updsnap003",  # noqa: E231
        )

        cls.bulk_edit_data = {
            "status": IPFabricSnapshotStatusModelChoices.STATUS_UNLOADED,
        }

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_data(self):
        snapshot = self._get_queryset().first()
        response = self.client.get(snapshot.get_absolute_url() + "data/")
        self.assertHttpStatus(response, 200)
        # Verify the response contains expected data view elements
        self.assertContains(response, "Raw Data")
        # Check that context contains the snapshot object
        self.assertIn("object", response.context)
        response_snapshot = response.context["object"]
        self.assertEqual(response_snapshot.name, snapshot.name)
        # Verify related data is accessible
        self.assertTrue(response_snapshot.ipf_data.exists())


class IPFabricDataTestCase(
    PluginPathMixin,
    # ViewTestCases.GetObjectViewTestCase,
    # ViewTestCases.GetObjectChangelogViewTestCase,
    # ViewTestCases.CreateObjectViewTestCase,
    # ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    # ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
    # ViewTestCases.BulkRenameObjectsViewTestCase,
    # ViewTestCases.BulkEditObjectsViewTestCase,
    # ViewTestCases.BulkImportObjectsViewTestCase,
):
    model = IPFabricData

    @classmethod
    def setUpTestData(cls):
        # Create required dependencies
        source = IPFabricSource.objects.create(
            name="Test Source",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://ipfabric.example.com",
            status=DataSourceStatusChoices.NEW,
        )

        snapshot = IPFabricSnapshot.objects.create(
            source=source,
            name="Test Snapshot",
            snapshot_id="data_snap001",
            data={"version": "6.0.0", "sites": ["Site A"], "total_dev_count": 100},
            date=timezone.now(),
            status=IPFabricSnapshotStatusModelChoices.STATUS_LOADED,
        )

        # Create three IPFabricData instances for testing
        data_instances = (
            IPFabricData(
                snapshot_data=snapshot,
                type="devices",
                data={"hostname": "device1", "vendor": "cisco", "model": "ISR4331"},
            ),
            IPFabricData(
                snapshot_data=snapshot,
                type="interfaces",
                data={"name": "GigabitEthernet0/0/0", "type": "ethernet"},
            ),
            IPFabricData(
                snapshot_data=snapshot,
                type="sites",
                data={"name": "Main Site", "location": "New York"},
            ),
        )
        for data_instance in data_instances:
            data_instance.save()

        cls.form_data = {
            "snapshot_data": snapshot.pk,
            "type": "devices",
            "data": '{"hostname": "test-device", "vendor": "juniper"}',
        }

        cls.csv_data = (
            "snapshot_data,type,data",
            f'{snapshot.pk},devices,"{{\\"hostname\\": \\"csv-device1\\", \\"vendor\\": \\"cisco\\"}}"',  # noqa: E231
            f'{snapshot.pk},interfaces,"{{\\"name\\": \\"Eth0/0\\", \\"type\\": \\"ethernet\\"}}"',  # noqa: E231
            f'{snapshot.pk},sites,"{{\\"name\\": \\"CSV Site\\", \\"location\\": \\"Boston\\"}}"',  # noqa: E231
        )

        cls.csv_update_data = (
            "id,type,data",
            f'{data_instances[0].pk},devices,"{{\\"hostname\\": \\"updated-device1\\", \\"vendor\\": \\"juniper\\"}}"',  # noqa: E231
            f'{data_instances[1].pk},interfaces,"{{\\"name\\": \\"Updated-Eth0/0\\", \\"type\\": \\"ethernet\\"}}"',  # noqa: E231
            f'{data_instances[2].pk},sites,"{{\\"name\\": \\"Updated Site\\", \\"location\\": \\"Chicago\\"}}"',  # noqa: E231
        )

        cls.bulk_edit_data = {
            "type": "devices",
        }

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_json(self):
        data = self._get_queryset().first()
        response = self.client.get(
            # No need to add +"json/" thanks to path="json" in @register_model_view
            data.get_absolute_url()
        )
        self.assertHttpStatus(response, 200)
        # Verify response contains expected content
        self.assertContains(response, "JSON Output")
        # Verify the data contains expected device information
        for value in data.data.values():
            self.assertContains(response, value)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_json_htmx(self):
        data = self._get_queryset().first()
        response = self.client.get(
            # No need to add +"json/" thanks to path="json" in @register_model_view
            data.get_absolute_url(),
            **{"HTTP_HX-Request": "true"},
        )
        self.assertHttpStatus(response, 200)
        # Verify HTMX response contains expected content
        self.assertContains(response, "JSON Output")
        # Verify the data contains expected device information
        for value in data.data.values():
            self.assertContains(response, value)


class IPFabricSyncTestCase(
    PluginPathMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
    ViewTestCases.BulkRenameObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    # ViewTestCases.BulkImportObjectsViewTestCase,
):
    model = IPFabricSync
    user_permissions = ("ipfabric_netbox.sync_ipfabricsync",)

    @classmethod
    def setUpTestData(cls):
        def get_parameters() -> dict:
            """Create dict of randomized but expected parameters for testing."""
            parameters = {}
            for param in list(ipam_parameters.keys()) + list(dcim_parameters.keys()):
                parameters[param] = bool(random.getrandbits(1))
            return parameters

        # Create required dependencies
        source = IPFabricSource.objects.create(
            name="Test Source",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://ipfabric.example.com",
            status=DataSourceStatusChoices.NEW,
        )

        snapshot1 = IPFabricSnapshot.objects.create(
            source=source,
            name="Test Snapshot 1",
            snapshot_id="sync_snap001",
            data={"version": "6.0.0", "sites": ["Site A"], "devices": 100},
            date=timezone.now(),
            status=IPFabricSnapshotStatusModelChoices.STATUS_LOADED,
        )

        snapshot2 = IPFabricSnapshot.objects.create(
            source=source,
            name="Test Snapshot 2",
            snapshot_id="sync_snap002",
            data={"version": "6.0.1", "sites": ["Site B"], "devices": 120},
            date=timezone.now(),
            status=IPFabricSnapshotStatusModelChoices.STATUS_LOADED,
        )

        # Create three IPFabricSync instances for testing
        cls.syncs = (
            IPFabricSync(
                name="Sync Job 1",
                snapshot_data=snapshot1,
                status=DataSourceStatusChoices.NEW,
                parameters=get_parameters(),
                last_synced=timezone.now(),
                scheduled=timezone.now() + timedelta(hours=6),
                interval=123456,
            ),
            IPFabricSync(
                name="Sync Job 2",
                snapshot_data=snapshot1,
                status=DataSourceStatusChoices.COMPLETED,
                parameters=get_parameters(),
                last_synced=timezone.now(),
            ),
            IPFabricSync(
                name="Sync Job 3",
                snapshot_data=snapshot2,
                status=DataSourceStatusChoices.FAILED,
                parameters=get_parameters(),
            ),
        )
        for sync in cls.syncs:
            sync.save()
            job = Job.objects.create(
                job_id=uuid4(),
                name="Test Ingestion Job 1",
                object_id=sync.pk,
                object_type=ContentType.objects.get_for_model(IPFabricSync),
                status=JobStatusChoices.STATUS_COMPLETED,
                completed=timezone.now(),
                created=timezone.now(),
            )
            IPFabricIngestion.objects.create(
                sync=sync,
                job=job,
            )

        cls.form_data = {
            "name": "Test Sync X",
            "source": source.pk,
            "snapshot_data": snapshot1.pk,
            "auto_merge": False,
            "update_custom_fields": True,
            **{f"ipf_{k}": v for k, v in get_parameters().items()},
        }

        cls.csv_data = (
            "name,snapshot_data,status,parameters",
            f'Sync CSV 1,{snapshot1.pk},{DataSourceStatusChoices.NEW},"{{\\"auto_merge\\": true}}"',  # noqa: E231
            f'Sync CSV 2,{snapshot1.pk},{DataSourceStatusChoices.COMPLETED},"{{\\"auto_merge\\": false}}"',  # noqa: E231
            f'Sync CSV 3,{snapshot2.pk},{DataSourceStatusChoices.NEW},"{{\\"auto_merge\\": true}}"',  # noqa: E231
        )

        cls.csv_update_data = (
            "id,name,status",
            f"{cls.syncs[0].pk},Updated Sync 1,{DataSourceStatusChoices.COMPLETED}",  # noqa: E231
            f"{cls.syncs[1].pk},Updated Sync 2,{DataSourceStatusChoices.FAILED}",  # noqa: E231
            f"{cls.syncs[2].pk},Updated Sync 3,{DataSourceStatusChoices.COMPLETED}",  # noqa: E231
        )

        cls.bulk_edit_data = {
            "auto_merge": True,
        }

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_htmx_request(self):
        instance = self._get_queryset().last()
        # Try GET with HTMX
        response = self.client.get(
            instance.get_absolute_url(), **{"HTTP_HX-Request": "true"}
        )
        self.assertHttpStatus(response, 200)

        # Verify HTMX response doesn't include full page structure
        self.assertNotContains(response, "<html>")
        self.assertNotContains(response, "<head>")

        # Verify the response contains the sync instance data
        self.assertContains(response, instance.name)
        self.assertContains(response, instance.last_ingestion.name)
        self.assertContains(response, instance.last_ingestion.get_absolute_url())

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_yaml_format(self):
        self.assertIsNone(self.user.config.get("data_format"))

        instance = self._get_queryset().first()

        # Try GET with yaml format
        self.assertHttpStatus(
            self.client.get(
                instance.get_absolute_url(), query_params={"format": "yaml"}
            ),
            200,
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_authenticated)
        self.assertEqual(self.user.config.get("data_format"), "yaml")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_transformmaps(self):
        sync = self._get_queryset().first()
        response = self.client.get(sync.get_absolute_url() + "transformmaps/")
        self.assertHttpStatus(response, 200)

        # Check that context contains the sync object
        self.assertIn("object", response.context)
        self.assertEqual(response.context["object"], sync)

        # Check if transform maps are displayed if they exist
        if hasattr(sync, "transform_maps") and sync.transform_maps.exists():
            for transform_map in sync.transform_maps.all():
                self.assertContains(response, transform_map.name)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_ingestions(self):
        sync = self._get_queryset().first()
        response = self.client.get(sync.get_absolute_url() + "ingestion/")
        self.assertHttpStatus(response, 200)

        # Verify the response contains expected elements
        self.assertContains(response, "Ingestions")

        # Check that context contains the sync object
        self.assertIn("object", response.context)
        self.assertEqual(response.context["object"], sync)

        # Check if ingestions are displayed if they exist
        ingestions = sync.ipfabricingestion_set.all()
        if ingestions.exists():
            for ingestion in ingestions:
                self.assertContains(response, str(ingestion))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_sync_view_get_redirect(self):
        """Test that GET request to sync view redirects to sync detail page."""
        sync = self._get_queryset().first()
        response = self.client.get(sync.get_absolute_url() + "sync/")
        self.assertHttpStatus(response, 302)
        self.assertRedirects(response, sync.get_absolute_url())

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    @patch("ipfabric_netbox.models.IPFabricSync.enqueue_sync_job")
    def test_sync_view_post_valid(self, mock_enqueue_sync_job):
        """Test POST request to sync view successfully enqueues sync job."""

        # Set up mock job
        mock_job = Job(pk=123, name="Test Sync Job")
        mock_enqueue_sync_job.return_value = mock_job

        sync = self._get_queryset().first()

        response = self.client.post(sync.get_absolute_url() + "sync/", follow=True)

        # Should redirect to sync detail page
        self.assertHttpStatus(response, 200)
        self.assertRedirects(response, sync.get_absolute_url())

        # Should have called enqueue_sync_job with correct parameters
        mock_enqueue_sync_job.assert_called_once()
        call_args = mock_enqueue_sync_job.call_args
        self.assertEqual(call_args[1]["user"], self.user)
        self.assertEqual(call_args[1]["adhoc"], True)

        # Should show success message
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn(f"Queued job #{mock_job.pk}", str(messages[0]))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_sync_view_nonexistent_sync(self):
        """Test sync view with non-existent sync returns 404."""
        nonexistent_pk = 99999
        response = self.client.post(
            f"/plugins/ipfabric-netbox/ipfabricsync/{nonexistent_pk}/sync/"
        )
        self.assertHttpStatus(response, 404)


class IPFabricTransformMapGroupTestCase(
    PluginPathMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
    ViewTestCases.BulkRenameObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkImportObjectsViewTestCase,
):
    model = IPFabricTransformMapGroup

    @classmethod
    def setUpTestData(cls):
        # Create three IPFabricTransformMapGroup instances for testing
        groups = (
            IPFabricTransformMapGroup(
                name="Device Transform Group",
                description="Group for device transformations",
            ),
            IPFabricTransformMapGroup(
                name="Interface Transform Group",
                description="Group for interface transformations",
            ),
            IPFabricTransformMapGroup(
                name="IP Address Transform Group",
                description="Group for IP address transformations",
            ),
        )
        for group in groups:
            group.save()

        cls.form_data = {
            "name": "Test Transform Group X",
            "description": "Test group description",
        }

        cls.bulk_edit_data = {
            "description": "Bulk updated description",
        }

        cls.csv_data = (
            "name,description",
            "First imported group,import test 1",
            "Second imported group,import test 2",
        )
        cls.csv_update_data = (
            "id,name,description",
            f"{groups[0].pk},First renamed group,changed import test 1",  # noqa: E231
            f"{groups[1].pk},Second renamed group,changed import test 2",  # noqa: E231
        )


class IPFabricTransformMapTestCase(
    PluginPathMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
    ViewTestCases.BulkRenameObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkImportObjectsViewTestCase,
):
    model = IPFabricTransformMap
    user_permissions = (
        "ipfabric_netbox.clone_ipfabrictransformmap",
        "ipfabric_netbox.restore_ipfabrictransformmap",
    )

    @classmethod
    def setUpTestData(cls):
        # Number of IPFabricTransformMaps created during migration
        # Hardcoded since we need to make sure we have the correct count
        cls.default_maps = IPFabricTransformMap.objects.filter(group__isnull=True)
        assert cls.default_maps.count() == 14
        # Remove all transform maps created in migrations to not interfere with tests
        IPFabricTransformMap.objects.filter(group__isnull=True).delete()

        # Create required dependencies
        group = IPFabricTransformMapGroup.objects.create(
            name="Test Group",
            description="Test group for transform maps",
        )
        cls.clone_group = IPFabricTransformMapGroup.objects.create(
            name="Test Cloning Group",
            description="Test group for cloning transform maps",
        )
        bulk_edit_group = IPFabricTransformMapGroup.objects.create(
            name="Test Bulk Edit Group",
            description="Test group for bulk editing transform maps",
        )

        maps = (
            IPFabricTransformMap(
                name="Device Transform Map",
                source_model="device",
                target_model=ContentType.objects.get(app_label="dcim", model="device"),
            ),
            IPFabricTransformMap(
                name="Site Transform Map",
                source_model="site",
                target_model=ContentType.objects.get(app_label="dcim", model="site"),
                group=group,
            ),
            IPFabricTransformMap(
                name="VLAN Transform Map",
                source_model="vlan",
                target_model=ContentType.objects.get(app_label="ipam", model="vlan"),
                group=group,
            ),
        )
        for map_obj in maps:
            map_obj.save()

        IPFabricTransformField.objects.create(
            transform_map=maps[0],
            source_field="hostname",
            target_field="name",
            template="{{ object.hostname }}",
        )
        IPFabricRelationshipField.objects.create(
            transform_map=maps[0],
            source_model=ContentType.objects.get(app_label="dcim", model="site"),
            target_field="site",
            template="{{ object.siteName }}",
            coalesce=True,
        )

        cls.form_data = {
            "name": "Test Transform Map X",
            "source_model": "device",
            "target_model": ContentType.objects.get(
                app_label="dcim", model="manufacturer"
            ).pk,
            "group": group.pk,
        }

        cls.bulk_edit_data = {
            "group": bulk_edit_group.pk,
        }

        cls.csv_data = (
            "name,source_model,target_model,group",
            "Manufacturer Transform Map,device,dcim.manufacturer,Test Group",
            "IPAddress Transform Map,ipaddress,ipam.ipaddress,Test Group",
            "Platform Transform Map,device,dcim.platform,",
        )
        cls.csv_update_data = (
            "id,name,source_model,target_model,group",
            f"{maps[0].pk},Prefix Transform Map,prefix,ipam.prefix,Test Group",  # noqa: E231
            f"{maps[1].pk},Manufacturer Transform Map,device,dcim.manufacturer,",  # noqa: E231
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_relationships(self):
        transform_map = self._get_queryset().first()
        response = self.client.get(transform_map.get_absolute_url() + "relationships/")
        self.assertHttpStatus(response, 200)

        # Check that context contains the transform map object
        self.assertIn("object", response.context)
        self.assertEqual(response.context["object"], transform_map)

        # Verify the template used is correct (using the actual template)
        self.assertTemplateUsed(
            response, "ipfabric_netbox/inc/transform_map_relationship_map.html"
        )

        # Check if relationship fields are displayed if they exist
        if transform_map.relationship_maps.exists():
            for relationship in transform_map.relationship_maps.all():
                self.assertContains(response, relationship.target_field)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_fields(self):
        transform_map = self._get_queryset().first()
        response = self.client.get(transform_map.get_absolute_url() + "fields/")
        self.assertHttpStatus(response, 200)

        # Check that context contains the transform map object
        self.assertIn("object", response.context)
        self.assertEqual(response.context["object"], transform_map)

        # Verify the template used is correct (using the actual template)
        self.assertTemplateUsed(
            response, "ipfabric_netbox/inc/transform_map_field_map.html"
        )

        # Check if transform fields are displayed if they exist
        if transform_map.field_maps.exists():
            for field in transform_map.field_maps.all():
                self.assertContains(response, field.source_field)
                self.assertContains(response, field.target_field)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_clone_view_get_redirect(self):
        """Test that GET request to clone view redirects to transform map detail page."""
        transform_map = self._get_queryset().first()
        response = self.client.get(transform_map.get_absolute_url() + "clone/")
        self.assertHttpStatus(response, 302)
        self.assertRedirects(response, transform_map.get_absolute_url())

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_clone_view_get_htmx(self):
        """Test that HTMX GET request to clone view returns form."""
        transform_map = self._get_queryset().first()
        response = self.client.get(
            transform_map.get_absolute_url() + "clone/",
            **{"HTTP_HX-Request": "true"},
        )
        self.assertHttpStatus(response, 200)
        self.assertContains(response, f"Clone of {transform_map.name}")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_clone_view_post_valid_form(self):
        """Test POST request with valid form data successfully clones transform map."""
        # Get a TransformMap with at least one field and one relationship
        transform_map = None
        for transform_map in self._get_queryset():
            if (
                transform_map.field_maps.count() > 0
                and transform_map.relationship_maps.count() > 0
            ):
                break
            transform_map = None
        self.assertIsNotNone(transform_map)

        # Valid form data
        form_data = {
            "name": "Cloned Transform Map",
            "group": self.clone_group.pk,
            "clone_fields": True,
            "clone_relationships": True,
        }

        response = self.client.post(
            transform_map.get_absolute_url() + "clone/",
            data=form_data,
            follow=True,
            **{"HTTP_HX-Request": "true"},
        )

        # Should redirect to old transform map detail page since it's HTMX
        self.assertHttpStatus(response, 200)
        self.assertIn("HX-Redirect", response)

        # Verify new transform map was created
        cloned_map = IPFabricTransformMap.objects.get(name="Cloned Transform Map")
        self.assertEqual(cloned_map.source_model, transform_map.source_model)
        self.assertEqual(cloned_map.target_model, transform_map.target_model)
        self.assertNotEqual(cloned_map.group, transform_map.group)

        # Verify fields were cloned
        self.assertEqual(
            IPFabricTransformField.objects.filter(transform_map=cloned_map).count(),
            transform_map.field_maps.count(),
        )

        # Verify relationships were cloned
        self.assertEqual(
            IPFabricRelationshipField.objects.filter(transform_map=cloned_map).count(),
            transform_map.relationship_maps.count(),
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_clone_view_post_without_fields_and_relationships(self):
        """Test POST request with clone_fields=False and clone_relationships=False."""
        transform_map = self._get_queryset().first()

        # Create some fields and relationships
        IPFabricTransformField.objects.create(
            transform_map=transform_map,
            source_field="vendor",
            target_field="manufacturer",
            template="{{ object.vendor }}",
        )
        IPFabricRelationshipField.objects.create(
            transform_map=transform_map,
            source_model=ContentType.objects.get(app_label="dcim", model="site"),
            target_field="site",
            template="{{ object.site_id }}",
        )

        # Form data without cloning fields and relationships
        form_data = {
            "name": "Cloned Map No Fields",
            "clone_fields": False,
            "clone_relationships": False,
            "group": self.clone_group.pk,
        }

        response = self.client.post(
            transform_map.get_absolute_url() + "clone/",
            data=form_data,
            follow=True,
        )

        cloned_map = IPFabricTransformMap.objects.get(name="Cloned Map No Fields")

        # Should redirect to new transform map detail page
        self.assertHttpStatus(response, 200)
        self.assertRedirects(response, cloned_map.get_absolute_url())

        # Verify new transform map was created but without fields/relationships
        self.assertEqual(cloned_map.source_model, transform_map.source_model)
        self.assertEqual(cloned_map.target_model, transform_map.target_model)

        # Verify fields were not cloned
        self.assertEqual(
            IPFabricTransformField.objects.filter(transform_map=cloned_map).count(), 0
        )

        # Verify relationships were not cloned
        self.assertEqual(
            IPFabricRelationshipField.objects.filter(transform_map=cloned_map).count(),
            0,
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_clone_view_post_htmx_valid(self):
        """Test HTMX POST request with valid form data."""
        transform_map = self._get_queryset().first()

        form_data = {
            "name": "HTMX Cloned Map",
            "clone_fields": False,
            "clone_relationships": False,
            "group": self.clone_group.pk,
        }

        response = self.client.post(
            transform_map.get_absolute_url() + "clone/",
            data=form_data,
            **{"HTTP_HX-Request": "true"},
        )

        # Should return HX-Redirect header
        self.assertHttpStatus(response, 200)
        self.assertIn("HX-Redirect", response)

        # Verify new transform map was created
        cloned_map = IPFabricTransformMap.objects.get(name="HTMX Cloned Map")
        self.assertEqual(cloned_map.source_model, transform_map.source_model)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_clone_view_post_invalid_form(self):
        """Test POST request with invalid form data."""
        transform_map = self._get_queryset().first()

        # Invalid form data - missing name
        form_data = {
            "group": self.clone_group.pk,
            "clone_fields": True,
            "clone_relationships": True,
        }

        response = self.client.post(
            transform_map.get_absolute_url() + "clone/",
            data=form_data,
        )

        # Should show form errors
        self.assertHttpStatus(response, 200)
        self.assertContains(response, "This field is required")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_clone_view_post_invalid_form_htmx(self):
        """Test POST request with invalid form data."""
        transform_map = IPFabricTransformMap.objects.filter(group__isnull=False).first()

        # Invalid form data - same group as original
        form_data = {
            "name": "HTMX Cloned Map",
            "group": transform_map.group.pk,
            "clone_fields": True,
            "clone_relationships": True,
        }

        response = self.client.post(
            transform_map.get_absolute_url() + "clone/",
            data=form_data,
            **{"HTTP_HX-Request": "true"},
        )

        # Should show form errors
        self.assertHttpStatus(response, 200)
        self.assertContains(
            response,
            "A transform map with group &#x27;Test Group&#x27; and target model &#x27;DCIM | site&#x27; already exists.",
        )
        self.assertIn("X-Debug-HTMX-Partial", response)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_clone_view_nonexistent_transform_map(self):
        """Test clone view with non-existent transform map returns 404."""
        nonexistent_pk = 99999
        response = self.client.get(
            f"/plugins/ipfabric-netbox/ipfabrictransformmap/{nonexistent_pk}/clone/"
        )
        self.assertHttpStatus(response, 404)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_clone_view_post_general_validation_error(self):
        transform_map = self._get_queryset().first()

        # Use valid form data but patch full_clean to raise ValidationError without error_dict
        form_data = {
            "name": "Test Clone General Error",
            "clone_fields": False,
            "clone_relationships": False,
            "group": self.clone_group.pk,
        }

        # Patch full_clean to raise ValidationError without error_dict
        with patch.object(
            IPFabricTransformMap,
            "full_clean",
            side_effect=ValidationError("Test error"),
        ):
            response = self.client.post(
                transform_map.get_absolute_url() + "clone/",
                data=form_data,
            )

        # Should show form with general error
        self.assertHttpStatus(response, 200)
        self.assertContains(response, "Test error")

        # Verify no new transform map was created due to validation error
        self.assertFalse(
            IPFabricTransformMap.objects.filter(
                name="Test Clone General Error"
            ).exists()
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_restore_view_get_non_htmx(self):
        """Test that GET request to restore view without HTMX returns empty response."""
        response = self.client.get(self._get_url(action="restore"))
        self.assertHttpStatus(response, 302)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_restore_view_get_htmx(self):
        """Test that HTMX GET request to restore view returns confirmation form."""
        response = self.client.get(
            self._get_url(action="restore"),
            **{"HTTP_HX-Request": "true"},
        )

        self.assertHttpStatus(response, 200)
        self.assertContains(response, self._get_url(action="restore"))
        # Check that dependent objects are included in context
        self.assertIn("dependent_objects", response.context)
        self.assertIn("form", response.context)
        self.assertIn("form_url", response.context)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_restore_view_post_success(self):
        """Test POST request to restore view successfully deletes ungrouped maps and rebuilds them."""
        # Remove all existing transform maps
        IPFabricTransformMap.objects.filter(group__isnull=True).delete()
        self.assertEqual(
            IPFabricTransformMap.objects.filter(group__isnull=True).count(), 0
        )

        response = self.client.post(
            self._get_url(action="restore"),
            follow=True,
        )

        # Should redirect to transform map list
        self.assertHttpStatus(response, 200)
        self.assertRedirects(response, "/plugins/ipfabric/transform-map/")

        # Verify ungrouped transform maps were restored
        self.assertEqual(
            IPFabricTransformMap.objects.filter(group__isnull=True).count(),
            self.default_maps.count(),
        )
        for map in self.default_maps:
            self.assertTrue(
                IPFabricTransformMap.objects.filter(
                    name=map.name,
                    source_model=map.source_model,
                    target_model=map.target_model,
                    group__isnull=True,
                ).exists()
            )

        # Verify grouped transform map still exists
        self.assertGreater(
            IPFabricTransformMap.objects.filter(group__isnull=True).count(), 0
        )

    def test_restore_view_requires_permission(self):
        """Test that restore view requires 'ipfabric_netbox.tm_restore' permission."""
        # Test without required permission
        response = self.client.get(self._get_url(action="restore"))
        # Should get permission denied (403) or redirect to login depending on settings
        self.assertIn(response.status_code, [302, 403])

        # Test POST without required permission
        response = self.client.post(self._get_url(action="restore"))
        # Should get permission denied (403) or redirect to login depending on settings
        self.assertIn(response.status_code, [302, 403])


class IPFabricTransformFieldTestCase(
    PluginPathMixin,
    # ViewTestCases.GetObjectViewTestCase,
    # ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    # ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
    # ViewTestCases.BulkRenameObjectsViewTestCase,
    # ViewTestCases.BulkEditObjectsViewTestCase,
    # ViewTestCases.BulkImportObjectsViewTestCase,
):
    model = IPFabricTransformField

    @classmethod
    def setUpTestData(cls):
        # Create required dependencies
        group = IPFabricTransformMapGroup.objects.create(
            name="Test Group",
            description="Test group for transform fields",
        )

        transform_map = IPFabricTransformMap.objects.create(
            name="Test Transform Map",
            source_model="devices",
            target_model=ContentType.objects.get(app_label="dcim", model="device"),
            group=group,
        )

        # Create three IPFabricTransformField instances for testing
        fields = (
            IPFabricTransformField(
                transform_map=transform_map,
                source_field="hostname",
                target_field="name",
                coalesce=False,
                template="{{ object.hostname }}",
            ),
            IPFabricTransformField(
                transform_map=transform_map,
                source_field="vendor",
                target_field="manufacturer",
                coalesce=True,
                template="{{ object.vendor }}",
            ),
            IPFabricTransformField(
                transform_map=transform_map,
                source_field="model",
                target_field="device_type",
                coalesce=False,
                template="{{ object.model }}",
            ),
        )
        for field in fields:
            field.save()

        cls.form_data = {
            "transform_map": transform_map.pk,
            "source_field": "serial_number",
            "target_field": "serial",
            "coalesce": False,
            "template": "{{ object.serial_number }}",
        }


class IPFabricRelationshipFieldTestCase(
    PluginPathMixin,
    # ViewTestCases.GetObjectViewTestCase,
    # ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    # ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
    # ViewTestCases.BulkRenameObjectsViewTestCase,
    # ViewTestCases.BulkEditObjectsViewTestCase,
    # ViewTestCases.BulkImportObjectsViewTestCase,
):
    model = IPFabricRelationshipField

    @classmethod
    def setUpTestData(cls):
        # Create required dependencies
        group = IPFabricTransformMapGroup.objects.create(
            name="Test Group",
            description="Test group for relationship fields",
        )

        device_ct = ContentType.objects.get(app_label="dcim", model="device")
        site_ct = ContentType.objects.get(app_label="dcim", model="site")

        transform_map = IPFabricTransformMap.objects.create(
            name="Test Transform Map",
            source_model="devices",
            target_model=device_ct,
            group=group,
        )

        # Create three IPFabricRelationshipField instances for testing
        fields = (
            IPFabricRelationshipField(
                transform_map=transform_map,
                source_model=site_ct,
                target_field="site",
                coalesce=False,
                template="{{ object.site_id }}",
            ),
            IPFabricRelationshipField(
                transform_map=transform_map,
                source_model=device_ct,
                target_field="parent_device",
                coalesce=True,
                template="{{ object.parent_id }}",
            ),
            IPFabricRelationshipField(
                transform_map=transform_map,
                source_model=site_ct,
                target_field="location",
                coalesce=False,
                template="{{ object.location_id }}",
            ),
        )
        for field in fields:
            field.save()

        cls.form_data = {
            "transform_map": transform_map.pk,
            "source_model": site_ct.pk,
            "target_field": "site",
            "coalesce": False,
            "template": "{{ object.site_id }}",
        }


class IPFabricIngestionTestCase(
    PluginPathMixin,
    ViewTestCases.GetObjectViewTestCase,
    # ViewTestCases.GetObjectChangelogViewTestCase,
    # ViewTestCases.CreateObjectViewTestCase,
    # ViewTestCases.EditObjectViewTestCase,
    # ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
    # ViewTestCases.BulkRenameObjectsViewTestCase,
    # ViewTestCases.BulkEditObjectsViewTestCase,
    # ViewTestCases.BulkImportObjectsViewTestCase,
):
    model = IPFabricIngestion
    user_permissions = ("ipfabric_netbox.merge_ipfabricingestion",)

    @classmethod
    def setUpTestData(cls):
        # Create required dependencies
        source = IPFabricSource.objects.create(
            name="Test Source",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://ipfabric.example.com",
            status=DataSourceStatusChoices.NEW,
        )

        snapshot = IPFabricSnapshot.objects.create(
            source=source,
            name="Test Snapshot",
            snapshot_id="ingest_snap001",
            data={"devices": 100},
            date=timezone.now(),
            status=IPFabricSnapshotStatusModelChoices.STATUS_LOADED,
        )

        # Create Sync instances for each ingestion
        sync1 = IPFabricSync.objects.create(
            name="Test Sync 1",
            snapshot_data=snapshot,
            status=DataSourceStatusChoices.NEW,
            parameters={"batch_size": 100},
            last_synced=timezone.now(),
        )

        sync2 = IPFabricSync.objects.create(
            name="Test Sync 2",
            snapshot_data=snapshot,
            status=DataSourceStatusChoices.COMPLETED,
            parameters={"batch_size": 200},
            last_synced=timezone.now(),
        )

        sync3 = IPFabricSync.objects.create(
            name="Test Sync 3",
            snapshot_data=snapshot,
            status=DataSourceStatusChoices.FAILED,
            parameters={"batch_size": 50},
        )

        # Create Job instances for each ingestion
        job1 = Job.objects.create(
            job_id=uuid4(),
            name="Test Ingestion Job 1",
            object_id=sync1.pk,
            object_type=ContentType.objects.get_for_model(IPFabricSync),
            status=JobStatusChoices.STATUS_COMPLETED,
            completed=timezone.now(),
            created=timezone.now(),
        )

        job2 = Job.objects.create(
            job_id=uuid4(),
            name="Test Ingestion Job 2",
            object_id=sync2.pk,
            object_type=ContentType.objects.get_for_model(IPFabricSync),
            status=JobStatusChoices.STATUS_RUNNING,
            created=timezone.now(),
        )

        job3 = Job.objects.create(
            job_id=uuid4(),
            name="Test Ingestion Job 3",
            object_id=sync3.pk,
            object_type=ContentType.objects.get_for_model(IPFabricSync),
            status=JobStatusChoices.STATUS_FAILED,
            created=timezone.now(),
        )

        branch1 = Branch.objects.create(name="Test Branch 1")
        branch2 = Branch.objects.create(name="Test Branch 2")
        branch3 = Branch.objects.create(name="Test Branch 3")

        site = Site.objects.create(name="Default Site", slug="default-site")
        modified = model_to_dict(site)
        modified["name"] = "Updated Site Name"
        for branch in (branch1, branch2, branch3):
            ChangeDiff.objects.create(
                branch=branch,
                object=site,
                object_type=ContentType.objects.get_for_model(site),
                object_repr=repr(site),
                original=model_to_dict(site),
                modified=modified,
            )

        # Create three IPFabricIngestion instances for testing (linked to sync and job instances)
        ingestions = (
            IPFabricIngestion(sync=sync1, job=job1, branch=branch1),
            IPFabricIngestion(sync=sync2, job=job2, branch=branch2),
            IPFabricIngestion(sync=sync3, job=job3, branch=branch3),
        )
        for ingestion in ingestions:
            ingestion.save()

        cls.form_data = {
            "snapshot": snapshot.pk,
            "status": DataSourceStatusChoices.NEW,
            "parameters": '{"batch_size": 150}',
        }

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_ingestion_issues(self):
        ingestion = self._get_queryset().first()
        response = self.client.get(ingestion.get_absolute_url() + "ingestion_issues/")
        self.assertHttpStatus(response, 200)

        # Verify the response contains expected elements
        self.assertContains(response, "Ingestion Issues")

        # Check that context contains the ingestion object
        self.assertIn("object", response.context)
        self.assertEqual(response.context["object"], ingestion)

        # Check if issues table or empty state is displayed
        if hasattr(ingestion, "issues") and ingestion.issues.exists():
            for issue in ingestion.issues.all():
                self.assertContains(response, issue.model)
        else:
            # Should contain table structure even if empty
            self.assertContains(response, "table")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_logs(self):
        ingestion = self._get_queryset().first()
        response = self.client.get(ingestion.get_absolute_url() + "logs/")
        self.assertHttpStatus(response, 200)

        # Verify the response contains expected elements
        self.assertContains(response, "Ingestion progress pending...")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_logs_htmx(self):
        ingestion = self._get_queryset().first()
        response = self.client.get(
            ingestion.get_absolute_url() + "logs/",
            **{"HTTP_HX-Request": "true"},
        )
        self.assertHttpStatus(response, 200)

        # Verify HTMX-specific response characteristics
        self.assertIn("object", response.context)
        self.assertEqual(response.context["object"], ingestion)

        # Verify HTMX response doesn't include full page structure
        self.assertNotContains(response, "<html>")
        self.assertNotContains(response, "<head>")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_changes(self):
        ingestion = self._get_queryset().first()
        response = self.client.get(ingestion.get_absolute_url() + "change/")
        self.assertHttpStatus(response, 200)

        # Verify the response contains expected elements
        self.assertContains(response, "Changes")

        # Check that context contains the ingestion object
        self.assertIn("object", response.context)
        self.assertEqual(response.context["object"], ingestion)

        # Check if branch changes are displayed
        if (
            ingestion.branch
            and hasattr(ingestion.branch, "changes")
            and ingestion.branch.changes.exists()
        ):
            for change in ingestion.branch.changes.all():
                self.assertContains(response, str(change.id))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_change(self):
        ingestion = self._get_queryset().first()
        change = ChangeDiff.objects.get(branch=ingestion.branch)
        response = self.client.get(
            ingestion.get_absolute_url() + f"change/{change.pk}/"
        )
        self.assertHttpStatus(response, 200)

        # Verify we remove empty change diff since it's not HTMX
        self.assertNotContains(response, str(change))
        self.assertContains(response, "Change Diff None")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_change_htmx(self):
        ingestion = self._get_queryset().first()
        change = ChangeDiff.objects.get(branch=ingestion.branch)
        response = self.client.get(
            ingestion.get_absolute_url() + f"change/{change.pk}/",
            **{"HTTP_HX-Request": "true"},
        )
        self.assertHttpStatus(response, 200)

        # Verify HTMX response doesn't include full page structure
        self.assertNotContains(response, "<html>")
        self.assertNotContains(response, "<head>")

        # Check that change diff content is displayed
        self.assertContains(response, str(change))
        if change.modified:
            for key, value in change.modified.items():
                if isinstance(value, str):
                    self.assertContains(response, value)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_change_htmx_empty_diff(self):
        ingestion = self._get_queryset().first()
        change = ChangeDiff.objects.get(branch=ingestion.branch)
        change.original = {}
        change.modified = {}
        change.save()
        response = self.client.get(
            ingestion.get_absolute_url() + f"change/{change.pk}/",
            **{"HTTP_HX-Request": "true"},
        )
        self.assertHttpStatus(response, 200)

        # Verify HTMX response handles empty diff gracefully
        self.assertContains(response, str(change))

        # Should contain some indication of empty changes
        self.assertContains(response, "No Changes")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_change_htmx_no_change(self):
        ingestion = self._get_queryset().first()
        response = self.client.get(
            ingestion.get_absolute_url() + "change/0/",
            **{"HTTP_HX-Request": "true"},
        )
        self.assertHttpStatus(response, 200)

        # Should contain some indication that change was not found
        self.assertContains(response, "Change Diff None")
        self.assertContains(response, "No Changes")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_merge_view_get_redirect(self):
        """Test that GET request to merge view redirects to ingestion detail page."""
        ingestion = self._get_queryset().first()
        response = self.client.get(ingestion.get_absolute_url() + "merge/")
        self.assertHttpStatus(response, 302)
        self.assertRedirects(response, ingestion.get_absolute_url())

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_merge_view_get_htmx(self):
        """Test that HTMX GET request to merge view returns form."""

        ingestion = self._get_queryset().first()
        response = self.client.get(
            ingestion.get_absolute_url() + "merge/",
            **{"HTTP_HX-Request": "true"},
        )
        self.assertHttpStatus(response, 200)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    @patch("ipfabric_netbox.forms.IPFabricIngestionMergeForm.clean")
    def test_merge_view_post_invalid_form(self, mock_clean):
        """Test POST request with invalid form data."""
        # Mock the clean method to raise ValidationError to make form invalid
        mock_clean.side_effect = ValidationError("Mocked validation error")

        ingestion = self._get_queryset().first()

        # Valid form data (but form will be invalid due to mocked clean method)
        form_data = {"confirm": True, "remove_branch": True}

        # The view should handle invalid form gracefully and redirect back
        response = self.client.post(
            ingestion.get_absolute_url() + "merge/", data=form_data, follow=True
        )

        # Should redirect to ingestion detail page
        self.assertHttpStatus(response, 200)
        self.assertRedirects(response, ingestion.get_absolute_url())

        # Should show error message for the validation error, 1 per field
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 2)
        self.assertIn("Mocked validation error", str(messages[0]))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    @patch("ipfabric_netbox.models.Job.enqueue")
    def test_merge_view_post_valid_form(self, mock_enqueue):
        """Test POST request with valid form data successfully enqueues merge job."""

        # Set up mock job
        mock_job = Job(pk=123, name="Test Merge Job")
        mock_enqueue.return_value = mock_job

        ingestion = self._get_queryset().first()

        # Valid form data
        form_data = {"confirm": True, "remove_branch": True}

        response = self.client.post(
            ingestion.get_absolute_url() + "merge/", data=form_data, follow=True
        )

        # Should redirect to ingestion detail page
        self.assertHttpStatus(response, 200)
        self.assertRedirects(response, ingestion.get_absolute_url())

        # Should have called Job.enqueue with correct parameters
        mock_enqueue.assert_called_once()
        call_args = mock_enqueue.call_args
        self.assertEqual(call_args[1]["instance"], ingestion)
        self.assertEqual(call_args[1]["remove_branch"], True)
        self.assertIn("user", call_args[1])

        # Should show success message
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn(f"Queued job #{mock_job.pk}", str(messages[0]))

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    @patch("ipfabric_netbox.models.Job.enqueue")
    def test_merge_view_post_valid_form_keep_branch(self, mock_enqueue):
        """Test POST request with remove_branch=False."""

        # Set up mock job
        mock_job = Job(pk=124, name="Test Merge Job Keep Branch")
        mock_enqueue.return_value = mock_job

        ingestion = self._get_queryset().first()

        # Valid form data with remove_branch=False
        form_data = {"confirm": True, "remove_branch": False}

        response = self.client.post(
            ingestion.get_absolute_url() + "merge/", data=form_data, follow=True
        )

        # Should redirect to ingestion detail page
        self.assertHttpStatus(response, 200)

        # Should have called Job.enqueue with remove_branch=False
        mock_enqueue.assert_called_once()
        call_args = mock_enqueue.call_args
        self.assertEqual(call_args[1]["remove_branch"], False)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_merge_view_nonexistent_ingestion(self):
        """Test merge view with non-existent ingestion returns 404."""
        response = self.client.get(
            "/plugins/ipfabric-netbox/ipfabricingestion/99999/merge/"
        )
        self.assertHttpStatus(response, 404)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    @patch("ipfabric_netbox.models.Job.enqueue")
    def test_merge_view_job_enqueue_parameters(self, mock_enqueue):
        """Test that Job.enqueue is called with correct parameters."""

        # Set up mock job with all expected attributes
        mock_job = Job(pk=125, name="Test Merge Job Parameters", job_id=uuid4())
        mock_enqueue.return_value = mock_job

        ingestion = self._get_queryset().first()

        form_data = {
            "confirm": True,
            "remove_branch": True,
        }

        self.client.post(
            ingestion.get_absolute_url() + "merge/", data=form_data, follow=True
        )

        # Verify Job.enqueue was called exactly once
        mock_enqueue.assert_called_once()

        # Get the call arguments
        call_args, call_kwargs = mock_enqueue.call_args

        # Check that the first argument is the correct job function
        self.assertEqual(call_args[0], merge_ipfabric_ingestion)

        # Check keyword arguments
        self.assertEqual(call_kwargs["name"], f"{ingestion.name} Merge")
        self.assertEqual(call_kwargs["instance"], ingestion)
        self.assertEqual(call_kwargs["remove_branch"], True)
        self.assertIsNotNone(call_kwargs["user"])


class IPFabricTableViewTestCase(PluginPathMixin, ModelTestCase):
    model = Device

    @classmethod
    def setUpTestData(cls):
        """Prepare a single Device with all required data filled."""

        manufacturer = Manufacturer.objects.create(
            name="Test Manufacturer", slug="test-manufacturer"
        )

        device_role = DeviceRole.objects.create(
            name="Test Device Role",
            slug="test-device-role",
            color="ff0000",  # Red color
        )

        site = Site.objects.create(name="Test Site", slug="test-site")

        device_type = DeviceType.objects.create(
            model="Test Device Model",
            slug="test-device-model",
            manufacturer=manufacturer,
            u_height=1,
        )

        cls.source = IPFabricSource.objects.create(
            name="IP Fabric Source 1",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://ipfabric1.example.com",
            status=DataSourceStatusChoices.NEW,
            parameters={"auth": "token1", "verify": True, "timeout": 30},
            last_synced=timezone.now(),
        )
        cls.snapshot = IPFabricSnapshot.objects.create(
            source=cls.source,
            name="Snapshot 1",
            snapshot_id="snap001",
            data={
                "version": "6.0.0",
                "sites": [site.name, "Site B", "Site C"],
                "total_dev_count": 100,
                "interface_count": 500,
                "note": "Test snapshot 1",
            },
            date=timezone.now(),
            status=IPFabricSnapshotStatusModelChoices.STATUS_LOADED,
        )
        cls.device = Device.objects.create(
            name="test-device-001",
            device_type=device_type,
            role=device_role,
            site=site,
            serial="TST123456789",
            asset_tag="ASSET-001",
            custom_field_data={"ipfabric_source": cls.source.pk},
        )

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_table(self):
        response = self.client.get(
            self.device.get_absolute_url() + "ipfabric/",
        )
        self.assertHttpStatus(response, 200)

        # Validate template used
        self.assertTemplateUsed(response, "ipfabric_netbox/ipfabric_table.html")

        # Validate context variables
        self.assertEqual(response.context["object"], self.device)
        self.assertIsNotNone(response.context["form"])
        self.assertIsNotNone(response.context["table"])
        self.assertIn("tab", response.context)

        # Validate that the source is retrieved from custom field
        expected_source = IPFabricSource.objects.filter(
            pk=self.device.custom_field_data.get("ipfabric_source")
        ).first()
        self.assertEqual(response.context["source"], expected_source)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_table_without_cf(self):
        self.device.custom_field_data = {}
        self.device.save()
        response = self.client.get(
            self.device.get_absolute_url() + "ipfabric/",
        )
        self.assertHttpStatus(response, 200)

        # Validate template used
        self.assertTemplateUsed(response, "ipfabric_netbox/ipfabric_table.html")

        # Validate context variables
        self.assertEqual(response.context["object"], self.device)
        self.assertIsNotNone(response.context["form"])
        self.assertIsNotNone(response.context["table"])

        # When no custom field is set, source should be retrieved from site
        expected_source = IPFabricSource.get_for_site(self.device.site).first()
        self.assertEqual(response.context["source"], expected_source)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_table_with_table_param(self):
        response = self.client.get(
            self.device.get_absolute_url() + "ipfabric/",
            query_params={"table": tableChoices[0][0]},
        )
        self.assertHttpStatus(response, 200)

        # Validate template used
        self.assertTemplateUsed(response, "ipfabric_netbox/ipfabric_table.html")

        # Validate context variables
        self.assertEqual(response.context["object"], self.device)
        self.assertIsNotNone(response.context["form"])
        self.assertIsNotNone(response.context["table"])

        # Validate that form has the correct initial table value
        form = response.context["form"]
        self.assertEqual(form.initial.get("table"), None)

        # Validate that the source is retrieved from custom field
        expected_source = IPFabricSource.objects.filter(
            pk=self.device.custom_field_data.get("ipfabric_source")
        ).first()
        self.assertEqual(response.context["source"], expected_source)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_table_without_source(self):
        self.device.custom_field_data = {}
        self.device.save()
        self.source.delete()
        response = self.client.get(
            self.device.get_absolute_url() + "ipfabric/",
            query_params={"table": tableChoices[0][0]},
        )
        self.assertHttpStatus(response, 200)

        # Validate template used
        self.assertTemplateUsed(response, "ipfabric_netbox/ipfabric_table.html")

        # Validate context variables
        self.assertEqual(response.context["object"], self.device)
        self.assertIsNotNone(response.context["form"])

        table = response.context["table"]
        self.assertIsInstance(table, DeviceIPFTable)

        # Verify the table has the expected structure for empty data scenario
        self.assertEqual(len(table.data), 0)  # Should be empty when no source
        self.assertIn(
            "hostname", [col.name for col in table.columns]
        )  # Should have default hostname column

        # Verify table meta attributes
        self.assertEqual(table.empty_text, "No results found")
        self.assertIn("table-hover", table.attrs.get("class", ""))

        # When no source is available, source should be None
        self.assertIsNone(response.context["source"])

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_table_with_snapshot_data(self):
        response = self.client.get(
            self.device.get_absolute_url() + "ipfabric/",
            query_params={
                "table": tableChoices[0][0],
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
            },
        )
        self.assertHttpStatus(response, 200)

        # Validate template used
        self.assertTemplateUsed(response, "ipfabric_netbox/ipfabric_table.html")

        # Validate context variables
        self.assertEqual(response.context["object"], self.device)
        self.assertIsNotNone(response.context["form"])
        self.assertIsNotNone(response.context["table"])
        self.assertEqual(response.context["source"], self.source)

        # Note: The actual implementation doesn't set form initial values,
        # it validates the form and uses cleaned_data instead
        form = response.context["form"]
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get("source"), self.source)
        self.assertEqual(form.cleaned_data.get("snapshot_data"), self.snapshot)

        # Validate that the response contains expected elements
        self.assertContains(response, self.device.name)
        self.assertContains(response, self.source.name)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    @patch("ipfabric_netbox.utilities.ipfutils.IPFClient")
    def test_get_table_with_cache(self, mock_ipfclient_class):
        # Clear cache before the test
        cache.clear()

        table_name = tableChoices[0][0]

        # Mock the IPFClient instance that gets created inside IPFabric.__init__
        mock_ipfclient_instance = mock_ipfclient_class.return_value
        mock_ipfclient_instance._client.headers = {"user-agent": "test-user-agent"}
        mock_ipfclient_instance.get_columns.return_value = [
            "id",
            "hostname",
            "vendor",
            "model",
        ]

        mock_table = getattr(mock_ipfclient_instance.inventory, table_name)
        mock_table.all.return_value = [
            {"hostname": "mock-device-1", "vendor": "cisco", "model": "ISR4331"},
        ]
        mock_table.endpoint = f"inventory/{table_name}"

        response = self.client.get(
            self.device.get_absolute_url() + "ipfabric/",
            query_params={
                "table": table_name,
                "cache_enable": "True",
            },
        )
        self.assertHttpStatus(response, 200)

        mock_ipfclient_class.assert_called_once()
        mock_table.all.assert_called_once()

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_table_htmx(self):
        response = self.client.get(
            self.device.get_absolute_url() + "ipfabric/",
            query_params={"table": tableChoices[0][0]},
            **{"HTTP_HX-Request": "true"},
        )
        self.assertHttpStatus(response, 200)

        # Validate HTMX-specific behavior - should not include full page structure
        self.assertNotContains(response, "<html>")
        self.assertNotContains(response, "<head>")

        # Validate that response contains the htmx form elements
        self.assertContains(response, "hx-target")  # HTMX attributes should be present

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    @patch("ipfabric_netbox.utilities.ipfutils.IPFClient")
    def test_get_table_with_snapshot_data_and_api_call(self, mock_ipfclient_class):
        """Test that snapshot data properly triggers API calls when needed."""
        # Mock the IPFClient instance
        mock_ipfclient_instance = mock_ipfclient_class.return_value
        mock_ipfclient_instance._client.headers = {"user-agent": "test-user-agent"}
        mock_ipfclient_instance.get_columns.return_value = ["id", "hostname", "vendor"]

        table_name = tableChoices[0][0]
        mock_table = getattr(mock_ipfclient_instance.inventory, table_name)
        mock_table.all.return_value = [
            {"hostname": "test-device-001", "vendor": "cisco", "model": "ISR4331"},
        ]
        mock_table.endpoint = f"inventory/{table_name}"

        response = self.client.get(
            self.device.get_absolute_url() + "ipfabric/",
            query_params={
                "table": table_name,
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
                "cache_enable": "False",  # Disable cache to force API call
            },
        )
        self.assertHttpStatus(response, 200)

        # Validate that API was called
        mock_ipfclient_class.assert_called_once()
        mock_table.all.assert_called_once()

        # Validate that response contains the mocked data
        self.assertContains(response, "test-device-001")
        self.assertContains(response, "cisco")

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_table_htmx_with_empty_table_param(self):
        """Test HTMX request with empty table parameter."""
        response = self.client.get(
            self.device.get_absolute_url() + "ipfabric/",
            query_params={"table": ""},
            **{"HTTP_HX-Request": "true"},
        )
        self.assertHttpStatus(response, 200)

        # For HTMX requests with empty table, it still returns a table context
        self.assertIn("table", response.context)
        self.assertIsNotNone(response.context["table"])

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_table_with_invalid_snapshot_data(self):
        """Test behavior with invalid snapshot data parameter."""
        response = self.client.get(
            self.device.get_absolute_url() + "ipfabric/",
            query_params={
                "table": tableChoices[0][0],
                "source": self.source.pk,
                "snapshot_data": 99999,  # Non-existent snapshot ID
            },
        )
        self.assertHttpStatus(response, 200)

        # Should handle invalid snapshot gracefully
        self.assertEqual(response.context["object"], self.device)
        self.assertEqual(response.context["source"], self.source)

        # The form should be invalid due to invalid snapshot_data
        form = response.context["form"]
        self.assertFalse(form.is_valid())

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_get_table_htmx_form_validation(self):
        """Test HTMX request form validation and data handling."""
        response = self.client.get(
            self.device.get_absolute_url() + "ipfabric/",
            query_params={
                "table": tableChoices[0][0],
                "source": self.source.pk,
                "cache_enable": "True",
            },
            **{"HTTP_HX-Request": "true"},
        )
        self.assertHttpStatus(response, 200)

        # For HTMX requests, context only contains table object
        self.assertIn("table", response.context)
        self.assertIsNotNone(response.context["table"])

        # HTMX requests don't include full page structure
        self.assertNotContains(response, "<html>")
        self.assertNotContains(response, "<body>")

import json
import sys
import pathlib
import pytest

# Ensure tests can import the local wemo_project modules when running under pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import api as api_module


class FakeDiscovery:
    def discover_devices(self):
        return []

    @property
    def device_list(self):
        return []

    def get_all_devices_info(self):
        return []

    def get_device_by_id(self, _):
        return None


class FakeController:
    def register_device(self, *a, **k):
        return None


@pytest.fixture(autouse=True)
def patch_discovery_and_controller(monkeypatch):
    monkeypatch.setattr(api_module, 'get_discovery', lambda: FakeDiscovery())
    monkeypatch.setattr(api_module, 'get_controller', lambda: FakeController())


def test_health_endpoint():
    client = api_module.app.test_client()
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'ok'


def _empty_days():
    return [{'enabled': False, 'onTime': '', 'offTime': ''} for _ in range(7)]


def test_save_and_get_schedule(tmp_path):
    # Point schedule storage to a temporary file
    tmp_file = tmp_path / 'schedules.json'
    api_module.SCHEDULE_FILE = tmp_file

    client = api_module.app.test_client()

    device_id = 'test-device-123'
    days = _empty_days()

    # Save schedule
    res = client.post(f'/api/devices/{device_id}/schedule', json={'days': days})
    assert res.status_code == 201
    body = res.get_json()
    assert body['success'] is True

    # Retrieve schedule
    res2 = client.get(f'/api/devices/{device_id}/schedule')
    assert res2.status_code == 200
    body2 = res2.get_json()
    assert body2['success'] is True
    assert 'schedule' in body2
    assert isinstance(body2['schedule']['days'], list)
    assert len(body2['schedule']['days']) == 7


def test_schedule_file_written(tmp_path):
    tmp_file = tmp_path / 'schedules.json'
    api_module.SCHEDULE_FILE = tmp_file
    client = api_module.app.test_client()

    device_id = 'persist-device'
    days = _empty_days()
    client.post(f'/api/devices/{device_id}/schedule', json={'days': days})

    assert tmp_file.exists()
    content = json.loads(tmp_file.read_text(encoding='utf-8'))
    assert device_id in content

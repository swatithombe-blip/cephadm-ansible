from mock.mock import patch, MagicMock
import pytest
import common
import ceph_orch_host


class TestCephOrchHost(object):
    @patch('ceph_orch_host.get_current_state')
    @patch('ceph_orch_host.update_host')
    def test_state_absent_host_exists(self, m_update_host, m_get_current_state):
        module = MagicMock()
        module.params = {
            'state': 'absent',
            'name': 'ceph-node5',
            'address': None,
            'labels': [],
            'set_admin_label': False,
            'docker': False,
            'fsid': None,
            'image': None,
        }
        module.check_mode = False

        module.exit_json.side_effect = common.exit_json
        module.fail_json.side_effect = common.fail_json

        m_get_current_state.return_value = (
            0,
            ['cephadm', 'shell', 'ceph', 'orch', 'host', 'ls', '--format', 'json'],
            '[{"addr": "10.10.10.11", "hostname": "ceph-node5", "labels": [], "status": ""}]',
            '',
        )

        m_update_host.return_value = (
            0,
            ["cephadm", "shell", "ceph", "orch", "host", "rm", "ceph-node5"],
            "Removed host 'ceph-node5'",
            '',
        )

        with pytest.raises(common.AnsibleExitJson) as result:
            ceph_orch_host.run(module)

        res = result.value.args[0]
        assert res['changed'] is True
        assert res['cmd'] == ["cephadm", "shell", "ceph", "orch", "host", "rm", "ceph-node5"]
        assert res['stdout'] == "Removed host 'ceph-node5'"
        assert res['rc'] == 0

    @patch('ceph_orch_host.get_current_state')
    def test_state_absent_host_doesnt_exist(self, m_get_current_state):
        module = MagicMock()
        module.params = {
            'state': 'absent',
            'name': 'ceph-node1',
            'address': None,
            'labels': [],
            'set_admin_label': False,
            'docker': False,
            'fsid': None,
            'image': None,
        }
        module.check_mode = False

        module.exit_json.side_effect = common.exit_json
        module.fail_json.side_effect = common.fail_json

        m_get_current_state.return_value = (
            0,
            ['cephadm', 'shell', 'ceph', 'orch', 'host', 'ls', '--format', 'json'],
            '[{"addr": "10.10.10.11", "hostname": "ceph-node5", "labels": [], "status": ""}]',
            '',
        )

        with pytest.raises(common.AnsibleExitJson) as result:
            ceph_orch_host.run(module)

        res = result.value.args[0]
        assert res['changed'] is False
        assert res['stdout'] == 'ceph-node1 is not present, skipping.'
        assert res['rc'] == 0

    @patch('ceph_orch_host.get_current_state')
    @patch('ceph_orch_host.update_host')
    def test_state_drain(self, m_update_host, m_get_current_state):
        module = MagicMock()
        module.params = {
            'state': 'drain',
            'name': 'ceph-node5',
            'address': None,
            'labels': [],
            'set_admin_label': False,
            'docker': False,
            'fsid': None,
            'image': None,
        }
        module.check_mode = False

        module.exit_json.side_effect = common.exit_json
        module.fail_json.side_effect = common.fail_json

        stdout = """\
Scheduled to remove the following daemons from host 'ceph-node5'
type                 id
-------------------- ---------------
crash                ceph-node5
osd                  3
osd                  5
osd                  7"""
        stderr = ''
        rc = 0

        m_get_current_state.return_value = (
            rc,
            ['cephadm', 'shell', 'ceph', 'orch', 'host', 'ls', '--format', 'json'],
            '[{"addr": "10.10.10.11", "hostname": "ceph-node5", "labels": [], "status": ""}]',
            stderr,
        )

        m_update_host.return_value = (
            rc,
            ["cephadm", "shell", "ceph", "orch", "host", "drain", "ceph-node5"],
            stdout,
            stderr,
        )

        with pytest.raises(common.AnsibleExitJson) as result:
            ceph_orch_host.run(module)

        res = result.value.args[0]
        assert res['changed'] is True
        assert res['cmd'] == ["cephadm", "shell", "ceph", "orch", "host", "drain", "ceph-node5"]
        assert res['stdout'] == stdout
        assert res['rc'] == 0

    @patch('ceph_orch_host.get_current_state')
    @patch('ceph_orch_host.update_label')
    @patch('ceph_orch_host.update_host')
    def test_state_present_no_label_diff(
        self,
        m_update_host,
        m_update_label,
        m_get_current_state,
    ):
        module = MagicMock()
        module.params = {
            'state': 'present',
            'name': 'ceph-node5',
            'address': None,
            'labels': [],
            'set_admin_label': False,
            'docker': False,
            'fsid': None,
            'image': None,
        }
        module.check_mode = False

        module.exit_json.side_effect = common.exit_json
        module.fail_json.side_effect = common.fail_json

        m_get_current_state.return_value = (
            0,
            ['cephadm', 'shell', 'ceph', 'orch', 'host', 'ls', '--format', 'json'],
            '[{"addr": "10.10.10.11", "hostname": "ceph-node5", "labels": [], "status": ""}]',
            '',
        )

        with pytest.raises(common.AnsibleExitJson) as result:
            ceph_orch_host.run(module)

        res = result.value.args[0]
        assert res['changed'] is False
        assert res['stdout'] == 'ceph-node5 is already present, skipping.'
        assert res['rc'] == 0

        m_update_host.assert_not_called()
        m_update_label.assert_not_called()

    @patch('ceph_orch_host.get_current_state')
    @patch('ceph_orch_host.update_label')
    @patch('ceph_orch_host.update_host')
    def test_state_present_label_diff(
        self,
        m_update_host,
        m_update_label,
        m_get_current_state,
    ):
        module = MagicMock()
        module.params = {
            'state': 'present',
            'name': 'ceph-node5',
            'address': None,
            'labels': ['label1', 'label2'],
            'set_admin_label': False,
            'docker': False,
            'fsid': None,
            'image': None,
        }
        module.check_mode = False

        module.exit_json.side_effect = common.exit_json
        module.fail_json.side_effect = common.fail_json

        m_get_current_state.return_value = (
            0,
            ['cephadm', 'shell', 'ceph', 'orch', 'host', 'ls', '--format', 'json'],
            '[{"addr": "10.10.10.11", "hostname": "ceph-node5", "labels": [], "status": ""}]',
            '',
        )

        m_update_label.side_effect = [
            (0, ['cmd'], 'Added label label1 to host ceph-node5', ''),
            (0, ['cmd'], 'Added label label2 to host ceph-node5', ''),
        ]

        with pytest.raises(common.AnsibleExitJson) as result:
            ceph_orch_host.run(module)

        res = result.value.args[0]
        assert res['changed'] is True
        assert 'Label(s) updated:' in res['stdout']
        assert 'label1' in res['stdout']
        assert 'label2' in res['stdout']
        assert res['rc'] == 0

        m_update_host.assert_not_called()
        assert m_update_label.call_count == 2

    @patch('ceph_orch_host.get_current_state')
    @patch('ceph_orch_host.update_label')
    def test_state_present_label_diff_error(
        self,
        m_update_label,
        m_get_current_state,
    ):
        module = MagicMock()
        module.params = {
            'state': 'present',
            'name': 'ceph-node5',
            'address': None,
            'labels': ['label1', 'label2'],
            'set_admin_label': False,
            'docker': False,
            'fsid': None,
            'image': None,
        }
        module.check_mode = False

        module.exit_json.side_effect = common.exit_json
        module.fail_json.side_effect = common.fail_json

        m_get_current_state.return_value = (
            0,
            ['cephadm', 'shell', 'ceph', 'orch', 'host', 'ls', '--format', 'json'],
            '[{"addr": "10.10.10.11", "hostname": "ceph-node5", "labels": [], "status": ""}]',
            '',
        )

        m_update_label.side_effect = RuntimeError('fake error')

        with pytest.raises(RuntimeError) as exc:
            ceph_orch_host.run(module)

        assert str(exc.value) == 'fake error'

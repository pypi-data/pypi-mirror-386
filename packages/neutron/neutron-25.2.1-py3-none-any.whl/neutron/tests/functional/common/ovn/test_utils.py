# Copyright 2022 Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import ddt
from neutron_lib.api.definitions import portbindings
from oslo_utils import uuidutils
from ovsdbapp.backend.ovs_idl import event
from ovsdbapp.backend.ovs_idl import idlutils

from neutron.common.ovn import constants as ovn_const
from neutron.common.ovn import utils
from neutron.tests.functional import base


class WaitForPortGroupDropEvent(event.WaitEvent):
    event_name = 'WaitForPortGroupDropEvent'

    def __init__(self):
        table = 'Port_Group'
        events = (self.ROW_CREATE, self.ROW_UPDATE)
        conditions = (('name', '=', ovn_const.OVN_DROP_PORT_GROUP_NAME),)
        super().__init__(events, table, conditions, timeout=5)


class TestCreateNeutronPgDrop(base.TestOVNFunctionalBase):
    def _create_and_check_pg_drop(self, wait_event=True):
        pg_event = WaitForPortGroupDropEvent()
        self.mech_driver.nb_ovn.idl.notify_handler.watch_event(pg_event)
        utils.create_neutron_pg_drop()
        if wait_event:
            self.assertTrue(pg_event.wait())
        pg = self.nb_api.pg_get(ovn_const.OVN_DROP_PORT_GROUP_NAME).execute()
        self.assertIsNotNone(pg)
        return pg

    def test_already_existing(self):
        # Make sure pre-fork initialize created the table
        existing_pg = self.nb_api.pg_get(
            ovn_const.OVN_DROP_PORT_GROUP_NAME).execute()
        self.assertIsNotNone(existing_pg)

        # make an attempt to create it again
        pg = self._create_and_check_pg_drop(wait_event=False)
        self.assertEqual(existing_pg.uuid, pg.uuid)

    def test_non_existing(self):
        # Delete the neutron_pg_drop created by pre-fork initialize
        self.nb_api.pg_del(ovn_const.OVN_DROP_PORT_GROUP_NAME).execute()
        pg = self.nb_api.pg_get(ovn_const.OVN_DROP_PORT_GROUP_NAME).execute()
        self.assertIsNone(pg)

        pg = self._create_and_check_pg_drop()

        directions = ['to-lport', 'from-lport']
        matches = ['outport == @neutron_pg_drop && ip',
                   'inport == @neutron_pg_drop && ip']

        # Make sure ACLs are correct
        self.assertEqual(2, len(pg.acls))
        acl1, acl2 = pg.acls

        self.assertEqual('drop', acl1.action)
        self.assertIn(acl1.direction, directions)
        directions.remove(acl1.direction)
        self.assertIn(acl1.match, matches)
        matches.remove(acl1.match)

        self.assertEqual(directions[0], acl2.direction)
        self.assertEqual('drop', acl2.action)
        self.assertEqual(matches[0], acl2.match)


class TestSyncHaChassisGroup(base.TestOVNFunctionalBase):

    def test_sync_ha_chassis_group_network(self):
        net = self._make_network(self.fmt, 'n1', True)['network']
        port_id = 'fake-port-id'
        hcg_name = utils.ovn_name(net['id'])
        chassis1 = self.add_fake_chassis('host1', azs=[],
                                         enable_chassis_as_gw=True)
        chassis2 = self.add_fake_chassis('host2', azs=[],
                                         enable_chassis_as_gw=True)
        self.add_fake_chassis('host3')

        with self.nb_api.transaction(check_error=True) as txn:
            utils.sync_ha_chassis_group_network(
                self.context, self.nb_api, self.sb_api,
                port_id, net['id'], txn)

        ha_chassis = self.nb_api.db_find('HA_Chassis').execute(
            check_error=True)
        ha_chassis_names = [hc['chassis_name'] for hc in ha_chassis]
        self.assertEqual(2, len(ha_chassis))
        self.assertEqual(sorted([chassis1, chassis2]),
                         sorted(ha_chassis_names))

        hcg = self.nb_api.ha_chassis_group_get(hcg_name).execute(
            check_error=True)
        self.assertEqual(hcg_name, hcg.name)
        ha_chassis_exp = sorted([str(hc['_uuid']) for hc in ha_chassis])
        ha_chassis_ret = sorted([str(hc.uuid) for hc in hcg.ha_chassis])
        self.assertEqual(ha_chassis_exp, ha_chassis_ret)

        # Delete one GW chassis and resync the HA chassis group associated to
        # the same network. The method will now not create again the existing
        # HA Chassis Group register but will update the "ha_chassis" list.
        self.del_fake_chassis(chassis2)
        with self.nb_api.transaction(check_error=True) as txn:
            utils.sync_ha_chassis_group_network(
                self.context, self.nb_api, self.sb_api, port_id,
                net['id'], txn)

        ha_chassis = self.nb_api.db_find('HA_Chassis').execute(
            check_error=True)
        ha_chassis_names = [hc['chassis_name'] for hc in ha_chassis]
        self.assertEqual(1, len(ha_chassis))
        self.assertEqual([chassis1], ha_chassis_names)

        hcg = self.nb_api.ha_chassis_group_get(hcg_name).execute(
            check_error=True)
        self.assertEqual(hcg_name, hcg.name)
        ha_chassis_exp = str(ha_chassis[0]['_uuid'])
        ha_chassis_ret = str(hcg.ha_chassis[0].uuid)
        self.assertEqual(ha_chassis_exp, ha_chassis_ret)

    def test_sync_ha_chassis_group_network_extport(self):
        # Create a network and an external port
        net = self._make_network(self.fmt, 'n1', True)['network']
        port_data = {
            'port': {'network_id': net['id'],
                     'tenant_id': self._tenant_id,
                     portbindings.VNIC_TYPE: portbindings.VNIC_DIRECT}}
        port_req = self.new_create_request('ports', port_data, self.fmt)
        port_res = port_req.get_response(self.api)
        port = self.deserialize(self.fmt, port_res)['port']

        # Add 3 chassis, two eligible for hosting the external port
        chassis1 = self.add_fake_chassis('host1', azs=[],
                                         enable_chassis_as_extport=True)
        chassis2 = self.add_fake_chassis('host2', azs=[],
                                         enable_chassis_as_extport=True)
        self.add_fake_chassis('host3')

        # Invoke the sync method
        with self.nb_api.transaction(check_error=True) as txn:
            utils.sync_ha_chassis_group_network(
                self.context, self.nb_api, self.sb_api, port['id'],
                net['id'], txn)

        # Assert only the eligible chassis are present in HA Chassis
        ha_chassis = self.nb_api.db_find('HA_Chassis').execute(
            check_error=True)
        ha_chassis_names = [hc['chassis_name'] for hc in ha_chassis]
        self.assertEqual(2, len(ha_chassis))
        self.assertEqual(sorted([chassis1, chassis2]),
                         sorted(ha_chassis_names))

        # Assert the HA Chassis Group has the correct name and the
        # eligible chassis are included in it
        hcg_name = utils.ovn_extport_chassis_group_name(port['id'])
        hcg = self.nb_api.ha_chassis_group_get(hcg_name).execute(
            check_error=True)
        self.assertEqual(hcg_name, hcg.name)
        ha_chassis_exp = sorted([str(hc['_uuid']) for hc in ha_chassis])
        ha_chassis_ret = sorted([str(hc.uuid) for hc in hcg.ha_chassis])
        self.assertEqual(ha_chassis_exp, ha_chassis_ret)

        # Delete one eligible Chassis and resync the HA chassis group
        # associated to the external port. The method should not re-create
        # the existing HA Chassis Group but only update the "ha_chassis" list
        self.del_fake_chassis(chassis2)
        with self.nb_api.transaction(check_error=True) as txn:
            utils.sync_ha_chassis_group_network(
                self.context, self.nb_api, self.sb_api, port['id'],
                net['id'], txn)

        # Assert the chassis deletion reflects in the HA Chassis and
        # HA Chassis Group
        ha_chassis = self.nb_api.db_find('HA_Chassis').execute(
            check_error=True)
        ha_chassis_names = [hc['chassis_name'] for hc in ha_chassis]
        self.assertEqual(1, len(ha_chassis))
        self.assertEqual([chassis1], ha_chassis_names)

        hcg = self.nb_api.ha_chassis_group_get(hcg_name).execute(
            check_error=True)
        self.assertEqual(hcg_name, hcg.name)
        ha_chassis_exp = str(ha_chassis[0]['_uuid'])
        ha_chassis_ret = str(hcg.ha_chassis[0].uuid)
        self.assertEqual(ha_chassis_exp, ha_chassis_ret)

        # Delete the external port, assert that the HA Chassis and HA Chassis
        # Group were also deleted
        self.plugin.delete_port(self.context, port['id'])
        ha_chassis = self.nb_api.db_find('HA_Chassis').execute(
            check_error=True)
        self.assertEqual(0, len(ha_chassis))
        self.assertRaises(
            idlutils.RowNotFound,
            self.nb_api.ha_chassis_group_get(hcg_name).execute,
            check_error=True)


@utils.ovn_context()
def method_with_idl_and_default_txn(ls_name, idl, txn=None):
    txn.add(idl.ls_add(ls_name))


@utils.ovn_context()
def method_with_txn_and_default_idl(ls_name, txn, idl=None):
    # NOTE(ralonsoh): the test with the default "idl" cannot be executed. A
    # default value should be provided in a non-testing implementation.
    txn.add(idl.ls_add(ls_name))


@utils.ovn_context()
def method_with_idl_and_txn(ls_name, idl, txn):
    txn.add(idl.ls_add(ls_name))


@utils.ovn_context(txn_var_name='custom_txn', idl_var_name='custom_idl')
def method_with_custom_idl_and_custom_txn(ls_name, custom_idl, custom_txn):
    custom_txn.add(custom_idl.ls_add(ls_name))


@utils.ovn_context()
def update_ls(ls_name, idl, txn):
    txn.add(idl.db_set('Logical_Switch', ls_name,
                       ('external_ids', {'random_key': 'random_value'})
                       )
            )


@ddt.ddt()
class TestOvnContext(base.TestOVNFunctionalBase):

    scenarios = (
        {'name': 'idl_and_default_txn',
         'method': method_with_idl_and_default_txn,
         '_args': ['ls_name', 'idl'], '_kwargs': ['txn']},
        {'name': 'idl_and_default_txn__positional_txn',
         'method': method_with_idl_and_default_txn,
         '_args': ['ls_name', 'idl', 'txn'], '_kwargs': []},
        {'name': 'idl_and_default_txn__default_txn',
         'method': method_with_idl_and_default_txn,
         '_args': ['ls_name', 'idl'], '_kwargs': []},

        {'name': 'txn_and_default_idl',
         'method': method_with_txn_and_default_idl,
         '_args': ['ls_name', 'txn'], '_kwargs': ['idl']},
        {'name': 'txn_and_default_idl__positional_idl',
         'method': method_with_txn_and_default_idl,
         '_args': ['ls_name', 'txn', 'idl'], '_kwargs': []},

        {'name': 'txn_and_idl',
         'method': method_with_idl_and_txn,
         '_args': ['ls_name', 'idl', 'txn'], '_kwargs': []},

        {'name': 'custom_idl_and_custom_txn',
         'method': method_with_custom_idl_and_custom_txn,
         '_args': ['ls_name', 'custom_idl', 'custom_txn'], '_kwargs': []},
    )

    scenarios2 = (
        {'name': method_with_idl_and_default_txn.__name__,
         'method': method_with_idl_and_default_txn},
        {'name': method_with_txn_and_default_idl.__name__,
         'method': method_with_txn_and_default_idl},
        {'name': method_with_idl_and_txn.__name__,
         'method': method_with_idl_and_txn},
        {'name': method_with_custom_idl_and_custom_txn.__name__,
         'method': method_with_custom_idl_and_custom_txn},
    )

    @ddt.unpack
    @ddt.named_data(*scenarios)
    def test_with_transaction(self, method, _args, _kwargs):
        ls_name = uuidutils.generate_uuid()
        custom_idl = idl = self.nb_api
        with self.nb_api.transaction(check_error=True) as txn:
            custom_txn = txn
            _locals = locals()
            args = [_locals[_arg] for _arg in _args]
            kwargs = {_kwarg: _locals[_kwarg] for _kwarg in _kwargs}
            # Create a LS and update it.
            method(*args, **kwargs)
            update_ls(ls_name, self.nb_api, txn)

        ls = self.nb_api.lookup('Logical_Switch', ls_name)
        self.assertEqual('random_value', ls.external_ids['random_key'])

    @ddt.unpack
    @ddt.named_data(*scenarios)
    def test_without_transaction(self, method, _args, _kwargs):
        ls_name = uuidutils.generate_uuid()
        custom_idl = idl = self.nb_api
        custom_txn = txn = None
        _locals = locals()
        args = [_locals[_arg] for _arg in _args]
        kwargs = {_kwarg: _locals[_kwarg] for _kwarg in _kwargs}
        # Create a LS and update it.
        method(*args, **kwargs)
        update_ls(ls_name, self.nb_api, txn)

        ls = self.nb_api.lookup('Logical_Switch', ls_name)
        self.assertEqual('random_value', ls.external_ids['random_key'])

    @ddt.unpack
    @ddt.named_data(*scenarios2)
    def test_needed_parameters(self, method):
        self.assertRaises(RuntimeError, method, uuidutils.generate_uuid(),
                          None, None)

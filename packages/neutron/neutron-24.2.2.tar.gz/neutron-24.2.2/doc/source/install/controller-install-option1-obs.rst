Networking Option 1: Provider networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install and configure the Networking components on the *controller* node.

Install the components
----------------------


.. code-block:: console

   # zypper install --no-recommends openstack-neutron \
     openstack-neutron-server openstack-neutron-openvswitch-agent \
     openstack-neutron-dhcp-agent openstack-neutron-metadata-agent \
     bridge-utils

.. end

Configure the server component
------------------------------

The Networking server component configuration includes the database,
authentication mechanism, message queue, topology change notifications,
and plug-in.

.. include:: shared/note_configuration_vary_by_distribution.rst

* Edit the ``/etc/neutron/neutron.conf`` file and complete the following
  actions:

  * In the ``[database]`` section, configure database access:

    .. path /etc/neutron/neutron.conf
    .. code-block:: ini

       [database]
       # ...
       connection = mysql+pymysql://neutron:NEUTRON_DBPASS@controller/neutron

    .. end

    Replace ``NEUTRON_DBPASS`` with the password you chose for the
    database.

    .. note::

       Comment out or remove any other ``connection`` options in the
       ``[database]`` section.

  * In the ``[DEFAULT]`` section, enable the Modular Layer 2 (ML2)
    plug-in and disable additional plug-ins:

    .. path /etc/neutron/neutron.conf
    .. code-block:: ini

       [DEFAULT]
       # ...
       core_plugin = ml2
       service_plugins =

    .. end

  * In the ``[DEFAULT]`` section, configure ``RabbitMQ``
    message queue access:

    .. path /etc/neutron/neutron.conf
    .. code-block:: ini

       [DEFAULT]
       # ...
       transport_url = rabbit://openstack:RABBIT_PASS@controller

    .. end

    Replace ``RABBIT_PASS`` with the password you chose for the
    ``openstack`` account in RabbitMQ.

  * In the ``[DEFAULT]`` and ``[keystone_authtoken]`` sections, configure
    Identity service access:

    .. path /etc/neutron/neutron.conf
    .. code-block:: ini

       [DEFAULT]
       # ...
       auth_strategy = keystone

       [keystone_authtoken]
       # ...
       www_authenticate_uri = http://controller:5000
       auth_url = http://controller:5000
       memcached_servers = controller:11211
       auth_type = password
       project_domain_name = Default
       user_domain_name = Default
       project_name = service
       username = neutron
       password = NEUTRON_PASS

    .. end

    Replace ``NEUTRON_PASS`` with the password you chose for the ``neutron``
    user in the Identity service.

    .. note::

       Comment out or remove any other options in the
       ``[keystone_authtoken]`` section.

  * In the ``[DEFAULT]`` and ``[nova]`` sections, configure Networking to
    notify Compute of network topology changes:

    .. path /etc/neutron/neutron.conf
    .. code-block:: ini

       [DEFAULT]
       # ...
       notify_nova_on_port_status_changes = true
       notify_nova_on_port_data_changes = true

       [nova]
       # ...
       auth_url = http://controller:5000
       auth_type = password
       project_domain_name = Default
       user_domain_name = Default
       region_name = RegionOne
       project_name = service
       username = nova
       password = NOVA_PASS

    .. end

    Replace ``NOVA_PASS`` with the password you chose for the ``nova``
    user in the Identity service.


* In the ``[oslo_concurrency]`` section, configure the lock path:

  .. path /etc/neutron/neutron.conf
  .. code-block:: ini

     [oslo_concurrency]
     # ...
     lock_path = /var/lib/neutron/tmp

  .. end

Configure the Modular Layer 2 (ML2) plug-in
-------------------------------------------

The ML2 plug-in uses the Linux bridge mechanism to build layer-2 (bridging
and switching) virtual networking infrastructure for instances.

* Edit the ``/etc/neutron/plugins/ml2/ml2_conf.ini`` file and complete the
  following actions:

  * In the ``[ml2]`` section, enable flat and VLAN networks:

    .. path /etc/neutron/plugins/ml2/ml2_conf.ini
    .. code-block:: ini

       [ml2]
       # ...
       type_drivers = flat,vlan

    .. end

  * In the ``[ml2]`` section, disable self-service networks:

    .. path /etc/neutron/plugins/ml2/ml2_conf.ini
    .. code-block:: ini

       [ml2]
       # ...
       tenant_network_types =

    .. end

  * In the ``[ml2]`` section, enable the Linux bridge mechanism:

    .. path /etc/neutron/plugins/ml2/ml2_conf.ini
    .. code-block:: ini

       [ml2]
       # ...
       mechanism_drivers = openvswitch

    .. end

    .. warning::

       After you configure the ML2 plug-in, removing values in the
       ``type_drivers`` option can lead to database inconsistency.

  * In the ``[ml2]`` section, enable the port security extension driver:

    .. path /etc/neutron/plugins/ml2/ml2_conf.ini
    .. code-block:: ini

       [ml2]
       # ...
       extension_drivers = port_security

    .. end

  * In the ``[ml2_type_flat]`` section, configure the provider virtual
    network as a flat network:

    .. path /etc/neutron/plugins/ml2/ml2_conf.ini
    .. code-block:: ini

       [ml2_type_flat]
       # ...
       flat_networks = provider

    .. end

Configure the Open vSwitch agent
--------------------------------

The Linux bridge agent builds layer-2 (bridging and switching) virtual
networking infrastructure for instances and handles security groups.

* Edit the ``/etc/neutron/plugins/ml2/openvswitch_agent.ini`` file and
  complete the following actions:

  * In the ``[ovs]`` section, map the provider virtual network to the
    provider physical bridge:

    .. path /etc/neutron/plugins/ml2/openvswitch_agent.ini
    .. code-block:: ini

      [ovs]
      bridge_mappings = provider:PROVIDER_BRIDGE_NAME

    .. end

    Replace ``PROVIDER_BRIDGE_NAME`` with the name of the bridge connected to
    the underlying provider physical network.
    See :doc:`environment-networking-obs`
    and :doc:`../admin/deploy-ovs-provider` for more information.

  * Ensure ``PROVIDER_BRIDGE_NAME`` external bridge is created and
    ``PROVIDER_INTERFACE_NAME`` is added to that bridge

    .. code-block:: bash

       # ovs-vsctl add-br $PROVIDER_BRIDGE_NAME
       # ovs-vsctl add-port $PROVIDER_BRIDGE_NAME $PROVIDER_INTERFACE_NAME

    .. end

  * In the ``[securitygroup]`` section, enable security groups and
    configure the Open vSwitch native or the hybrid iptables firewall driver:

    .. path /etc/neutron/plugins/ml2/openvswitch_agent.ini
    .. code-block:: ini

       [securitygroup]
       # ...
       enable_security_group = true
       firewall_driver = openvswitch
       #firewall_driver = iptables_hybrid

    .. end

  * In the case of using the hybrid iptables firewall driver, ensure your
    Linux operating system kernel supports network bridge filters by verifying
    all the following ``sysctl`` values are set to ``1``:

    .. code-block:: ini

        net.bridge.bridge-nf-call-iptables
        net.bridge.bridge-nf-call-ip6tables

    .. end

    To enable networking bridge support, typically the ``br_netfilter`` kernel
    module needs to be loaded. Check your operating system's documentation for
    additional details on enabling this module.

Configure the DHCP agent
------------------------

The DHCP agent provides DHCP services for virtual networks.

* Edit the ``/etc/neutron/dhcp_agent.ini`` file and complete the following
  actions:

  * In the ``[DEFAULT]`` section, configure the Linux bridge interface driver,
    Dnsmasq DHCP driver, and enable isolated metadata so instances on provider
    networks can access metadata over the network:

    .. path /etc/neutron/dhcp_agent.ini
    .. code-block:: ini

       [DEFAULT]
       # ...
       interface_driver = openvswitch
       dhcp_driver = neutron.agent.linux.dhcp.Dnsmasq
       enable_isolated_metadata = true

    .. end

Create the provider network
---------------------------

Follow `this provider network document <https://docs.openstack.org/install-guide/launch-instance-networks-provider.html>`_ from the General Installation Guide.


Return to *Networking controller node configuration*.

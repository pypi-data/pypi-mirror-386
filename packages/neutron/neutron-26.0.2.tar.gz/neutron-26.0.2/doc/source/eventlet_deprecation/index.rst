..
      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

      Convention for heading levels in Neutron devref:
      =======  Heading 0 (reserved for the title in a document)
      -------  Heading 1
      ~~~~~~~  Heading 2
      +++++++  Heading 3
      '''''''  Heading 4
      (Avoid deeper levels because they do not render well.)

==============================
Eventlet Deprecation Reference
==============================

This document contains the information related to the ``eventlet`` library
deprecation. Each section describes how each module has been migrated, the
caveats, the pending technical debt and the missing parts.


OVN Agent
---------

Launch process
~~~~~~~~~~~~~~

The execution of the OVN agent has been replaced. Instead of using
``oslo_services.launch``, that is still using eventlet, the agent creates
a ``threading.Event`` instance and holds the main thread execution by waiting
for this event.

.. note::

  Once the ``oslo_services`` library removes the usage of
  eventlet, the previous implementation will be restored. The
  ``oslo_services.service.ProcessLauncher`` service launcher implements a
  signal handler.


Metadata proxy
~~~~~~~~~~~~~~

The ``UnixDomainWSGIServer`` class has been replaced with a new implementation.
This implementation does not rely on ``neutron.api.wsgi.Server`` nor
``eventlet.wsgi.server``. It inherits from the built-in library class
``socketserver.StreamRequestHandler``.

.. note::

  This implementation doesn't use ``oslo_services`` to spawn the
  processes or the local threads depending on the ``metadata_workers``
  configuration variable. Right now only the embedded form (local thread)
  is implemented (``metadata_workers=0``, the default value). Future
  implementations will enable again this configuration variable.


OVN metadata agent
------------------

Metadata proxy
~~~~~~~~~~~~~~

The OVN metadata agent uses the same implementation as the OVN agent. The same
limitations apply.


Metadata agent
--------------

The Metadata agent uses the same implementation as the OVN agent and the same
limitations apply. The ``MetadataProxyHandler`` class is now instantiated every
time a new request is done; after the call, the instance is destroyed. The
cache used to store the previous RPC calls results is no longer relevant and
has been removed. In order to implement an RPC cache, it should be implemented
outside the mentioned class.


Neutron API
-----------

The Neutron API currently can be executed only with the uWSGI module; the
eventlet executor has been deprecated, although the code has not been removed
from the repository yet. It is now mandatory to define the configuration
variable ``start-time`` in the uWSGI configuration file, using the magic
variable [1]_ "%t" that provides the *unix time (in seconds, gathered at
instance startup)*.

.. code::

  [uwsgi]
  start-time = %t


The Neutron API consists of the following executables:

* The API server: is a multiprocess worker; each process is created by the
  ``uWSGI`` server.

* The periodic worker: a mult process worker that spawns several threads to
  execute the periodic workers.

* The RPC worker: a multiprocess process worker that attends the requests from
  the RPC clients, for example the Neutron agents.

* The ML2/OVN maintenance worker: single process worker, needed by the ML2/OVN
  mechanism driver.


ML2/OVN
~~~~~~~

The mechanism driver ML2/OVN requires a synchronization method between all
nodes (controllers) and workers. The OVN database events will be received by
all workers in all nodes; however, only one worker should process this event.
The ``HashRingManager``, locally instantiated in each worker, is in charge of
hashing the event received and decide what worker will process the event.

The ``HashRingManager`` uses the information stored in the Neutron database to
determine how many workers are alive at this time. Each worker will register
itself in the Neutron database, creating a register in the table
``ovn_hash_ring``. The UUID of each register is created using a deterministic
method that depends on (1) the hash ring group (always "mechanism_driver" for
the API workers), (2) the host name and (3) the worker ID. If the worker is
restarted, this method will provide the same register UUID and the previous
register (if present in the database) will be overwritten.


.. note::

  Right now, only the API server is running without eventlet.




References
----------

.. [1] https://uwsgi-docs.readthedocs.io/en/latest/Configuration.html#magic-variables

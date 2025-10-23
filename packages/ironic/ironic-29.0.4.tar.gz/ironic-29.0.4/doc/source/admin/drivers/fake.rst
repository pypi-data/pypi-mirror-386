===========
Fake driver
===========

Overview
========

The ``fake-hardware`` hardware type is what it claims to be: fake. Use of this
type or the ``fake`` interfaces should be temporary or limited to
non-production environments, as the ``fake`` interfaces do not perform any of
the actions typically expected.

The ``fake`` interfaces can be configured to be combined with any of the
"real" hardware interfaces, allowing you to effectively disable one or more
hardware interfaces for testing by simply setting that interface to
``fake``.

Use cases
=========

Development
-----------
Developers can use ``fake-hardware`` hardware-type to mock out nodes for
testing without those nodes needing to exist with physical or virtual hardware.

Scale testing
-------------
The ``fake`` drivers have a configurable delay in seconds which will result in
those operations taking that long to complete. Two comma-delimited values will
result in a delay with a triangular random distribution, weighted on the first
value. These delays are applied to operations which typically block in other
drivers. This allows more realistic scenarios to be arranged for performance and
functional testing of an Ironic service without requiring real bare metal or
faking at the BMC protocol level.

.. code-block:: ini

    [fake]
    power_delay = 5
    boot_delay = 10
    deploy_delay = 60,360
    vendor_delay = 1
    management_delay = 5
    inspect_delay = 360,480
    raid_delay = 10
    bios_delay = 5
    storage_delay = 10
    rescue_delay = 120

Adoption
--------
Some OpenStack deployers have used ``fake`` interfaces in Ironic to allow an
adoption-style workflow with Nova. By setting a node's hardware interfaces to
``fake``, it's possible to deploy to that node with Nova without causing any
actual changes to the hardware or an OS already deployed on it.

This is generally an unsupported use case, but it is possible. For more
information, see the relevant `post from CERN TechBlog`_.

.. _`post from CERN TechBlog`: https://techblog.web.cern.ch/techblog/post/ironic-nova-adoption/

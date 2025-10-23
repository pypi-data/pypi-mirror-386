.. _image-requirements:

Add images to the Image service
===============================

Supported Image Formats
~~~~~~~~~~~~~~~~~~~~~~~

Ironic officially supports and tests use of ``qcow2`` formatted images as well
as ``raw`` format images. Other types of disk images, like ``vdi``, and single
file ``vmdk`` files have been reported by users as working in their specific
cases, but are not tested upstream. We advise operators to convert the image
and properly upload the image to Glance.

Ironic enforces the list of supported and permitted image formats utilizing
the ``[conductor]permitted_image_formats`` option in ironic.conf. This setting
defaults to "raw" and "qcow2".

A detected format mismatch between Glance and what the actual contents of
the disk image file are detected as will result in a failed deployment.
To correct such a situation, the image must be re-uploaded with the
declared ``--disk-format`` or actual image file format corrected.

Instance (end-user) images
~~~~~~~~~~~~~~~~~~~~~~~~~~

Build or download the user images as described in :doc:`/user/creating-images`.

Load all the created images into the Image service, and note the image UUIDs in
the Image service for each one as it is generated.

.. note::
   Images from Glance used by Ironic must be flagged as ``public``, which
   requires administrative privileges with the Glance image service to set.

- For *whole disk images* just upload the image:

  .. code-block:: console

     $ openstack image create my-whole-disk-image --public \
       --disk-format qcow2 --container-format bare \
       --file my-whole-disk-image.qcow2

  .. warning::
      The kernel/ramdisk pair must not be set for whole disk images,
      otherwise they'll be mistaken for partition images.

- For *partition images* to be used only with *local boot* (the default)
  the ``img_type`` property must be set:

  .. code-block:: console

     $ openstack image create my-image --public \
       --disk-format qcow2 --container-format bare \
       --property img_type=partition --file my-image.qcow2

- For *partition images* to be used with both *local* and *network* boot:

  Add the kernel and ramdisk images to the Image service:

  .. code-block:: console

     $ openstack image create my-kernel --public \
       --disk-format raw --container-format bare --file my-image.vmlinuz

  Store the image uuid obtained from the above step as ``MY_VMLINUZ_UUID``.

  .. code-block:: console

     $ openstack image create my-image.initrd --public \
       --disk-format raw --container-format bare --file my-image.initrd

  Store the image UUID obtained from the above step as ``MY_INITRD_UUID``.

  Add the *my-image* to the Image service which is going to be the OS
  that the user is going to run. Also associate the above created
  images with this OS image. These two operations can be done by
  executing the following command:

  .. code-block:: console

     $ openstack image create my-image --public \
       --disk-format qcow2 --container-format bare --property \
       kernel_id=$MY_VMLINUZ_UUID --property \
       ramdisk_id=$MY_INITRD_UUID --file my-image.qcow2

Deploy ramdisk images
~~~~~~~~~~~~~~~~~~~~~

#. Build or download the deploy images

   The deploy images are used initially for preparing the server (creating disk
   partitions) before the actual OS can be deployed.

   There are several methods to build or download deploy images, please read
   the :ref:`deploy-ramdisk` section.

#. Add the deploy images to the Image service

   Add the deployment kernel and ramdisk images to the Image service:

   .. code-block:: console

      $ openstack image create deploy-vmlinuz --public \
        --disk-format raw --container-format bare \
        --file ironic-python-agent.vmlinuz

   Store the image UUID obtained from the above step as ``DEPLOY_VMLINUZ_UUID``
   (or a different name when using the parameter specified by node architecture).

   .. code-block:: console

      $ openstack image create deploy-initrd --public \
        --disk-format raw --container-format bare \
        --file ironic-python-agent.initramfs

   Store the image UUID obtained from the above step as ``DEPLOY_INITRD_UUID``
   (or a different name when using the parameter specified by node architecture).

#. Configure the Bare Metal service to use the produced images. It can be done
   per node as described in :doc:`enrollment` or in the configuration
   file either using a dictionary to specify them by architecture (matching
   the node's ``cpu_arch`` property) as follows:

   .. code-block:: ini

    [conductor]
    deploy_kernel_by_arch = x86_64:<DEPLOY_VMLINUZ_X86_64_UUID>,aarch64:<DEPLOY_VMLINUZ_AARCH64_UUID>
    deploy_ramdisk_by_arch = x86_64:<DEPLOY_INITRD_X86_64_UUID>,aarch64:<DEPLOY_INITRD_AARCH64_UUID>

   or globally using the general configuration parameters:

   .. code-block:: ini

    [conductor]
    deploy_kernel = <insert DEPLOY_VMLINUZ_UUID>
    deploy_ramdisk = <insert DEPLOY_INITRD_UUID>

   In the case when both general parameters and parameters specified by
   architecture are defined, the parameters specified by architecture take
   priority.

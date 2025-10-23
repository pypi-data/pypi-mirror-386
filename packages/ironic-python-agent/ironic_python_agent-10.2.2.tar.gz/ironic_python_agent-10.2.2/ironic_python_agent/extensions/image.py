# Copyright 2015 Red Hat, Inc.
# All Rights Reserved.
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

import os
import re
import shutil
import tempfile

from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import log

from ironic_python_agent import efi_utils
from ironic_python_agent import errors
from ironic_python_agent.extensions import base
from ironic_python_agent import hardware
from ironic_python_agent import partition_utils
from ironic_python_agent import raid_utils
from ironic_python_agent import utils

LOG = log.getLogger(__name__)

CONF = cfg.CONF

BIND_MOUNTS = ('/dev', '/proc', '/run')


def _has_dracut(root):
    try:
        utils.execute('chroot %(path)s /bin/sh -c '
                      '"which dracut"' %
                      {'path': root}, shell=True)
    except processutils.ProcessExecutionError:
        return False
    return True


def _has_boot_sector(device):
    """Checks the device for a boot sector indicator."""
    stdout, stderr = utils.execute('file', '-s', device)
    if 'boot sector' not in stdout:
        return False
    # Now lets check the signature
    ddout, dderr = utils.execute(
        'dd', 'if=%s' % device, 'bs=218', 'count=1', binary=True)
    stdout, stderr = utils.execute('file', '-', process_input=ddout)
    # The bytes recovered by dd show as a "dos executable" when
    # examined with file. In other words, the bootloader is present.
    return 'executable' in stdout


def _find_bootable_device(partitions, dev):
    """Checks the base device and partition for bootloader contents."""
    LOG.debug('Looking for a bootable device in %s', dev)
    for line in partitions.splitlines():
        partition = line.split(':')
        try:
            if 'boot' in partition[6]:
                if _has_boot_sector(dev) or _has_boot_sector(partition[0]):
                    return True
        except IndexError:
            continue
    return False


def _is_bootloader_loaded(dev):
    """Checks the device to see if a MBR bootloader is present.

    :param str dev: Block device upon which to check if it appears
                       to be bootable via MBR.
    :returns: True if a device appears to be bootable with a boot
              loader, otherwise False.
    """

    boot = hardware.dispatch_to_managers('get_boot_info')

    if boot.current_boot_mode != 'bios':
        # We're in UEFI mode, this logic is invalid
        LOG.debug('Skipping boot sector check as the system is in UEFI '
                  'boot mode.')
        return False
    LOG.debug('Starting check for pre-intalled BIOS boot-loader.')
    try:
        # Looking for things marked "bootable" in the partition table
        stdout, stderr = utils.execute('parted', dev, '-s', '-m',
                                       '--', 'print')
    except processutils.ProcessExecutionError:
        return False

    return _find_bootable_device(stdout, dev)


def _umount_all_partitions(path, path_variable, umount_warn_msg):
    """Umount all partitions we may have mounted"""
    umount_binds_success = True
    LOG.debug("Unmounting all vfat partitions inside the image ...")
    try:
        utils.execute('chroot %(path)s /bin/sh -c "umount -a -t vfat"' %
                      {'path': path}, shell=True,
                      env_variables={'PATH': path_variable})
    except processutils.ProcessExecutionError as e:
        LOG.warning("Unable to umount vfat partitions. Error: %(error)s",
                    {'error': e})

    for fs in BIND_MOUNTS + ('/sys',):
        try:
            utils.execute('umount', path + fs, attempts=3,
                          delay_on_retry=True)
        except processutils.ProcessExecutionError as e:
            umount_binds_success = False
            LOG.warning(umount_warn_msg, {'path': path + fs, 'error': e})

    return umount_binds_success


def _mount_partition(partition, path):
    if not os.path.ismount(path):
        LOG.debug('Attempting to mount %(device)s to %(path)s to '
                  'partition.',
                  {'device': partition,
                   'path': path})
        try:
            utils.execute('mount', partition, path)
        except processutils.ProcessExecutionError as e:
            # NOTE(TheJulia): It seems in some cases,
            # the python os.path.ismount can return False
            # even *if* it is actually mounted. This appears
            # to be because it tries to rely on inode on device
            # logic, yet the rules are sometimes different inside
            # ramdisks. So lets check the error first.
            if 'already mounted' not in e:
                # Raise the error, since this is not a known
                # failure case
                raise
            else:
                LOG.debug('Partition already mounted, proceeding.')


def _install_grub2(device, root_uuid, efi_system_part_uuid=None,
                   prep_boot_part_uuid=None, target_boot_mode='bios'):
    """Install GRUB2 bootloader on a given device."""
    LOG.debug("Installing GRUB2 bootloader on device %s", device)

    efi_partition = None
    efi_part = None
    efi_partition_mount_point = None
    efi_mounted = False
    efi_preserved = False
    holders = None
    path_variable = _get_path_variable()

    # NOTE(TheJulia): Seems we need to get this before ever possibly
    # restart the device in the case of multi-device RAID as pyudev
    # doesn't exactly like the partition disappearing.
    root_partition = partition_utils.get_partition(device, uuid=root_uuid)

    # If the root device is an md device (or partition), restart the device
    # (to help grub finding it) and identify the underlying holder disks
    # to install grub.
    if hardware.is_md_device(device):
        # If the root device is an md device (or partition),
        # restart the device to help grub find it later on.
        hardware.md_restart(device)
        # If an md device, we need to rescan the devices anyway to pickup
        # the md device partition.
        utils.rescan_device(device)
    elif (_is_bootloader_loaded(device)
          and not (efi_system_part_uuid
                   or prep_boot_part_uuid)):
        # We always need to put the bootloader in place with software raid
        # so it is okay to elif into the skip doing a bootloader step.
        LOG.info("Skipping installation of bootloader on device %s "
                 "as it is already marked bootable.", device)
        return

    try:
        # Mount the partition and binds
        path = tempfile.mkdtemp()
        if efi_system_part_uuid:
            efi_part = partition_utils.get_partition(
                device, uuid=efi_system_part_uuid)
            efi_partition = efi_part
        if hardware.is_md_device(device):
            holders = hardware.get_holder_disks(device)
            efi_partition = raid_utils.prepare_boot_partitions_for_softraid(
                device, holders, efi_part, target_boot_mode
            )

        if efi_partition:
            efi_partition_mount_point = os.path.join(path, "boot/efi")

        # For power we want to install grub directly onto the PreP partition
        if prep_boot_part_uuid:
            device = partition_utils.get_partition(
                device, uuid=prep_boot_part_uuid)

        # If the root device is an md device (or partition),
        # identify the underlying holder disks to install grub.
        if hardware.is_md_device(device):
            disks = holders
        else:
            disks = [device]

        utils.execute('mount', root_partition, path)

        _mount_for_chroot(path)

        # UEFI asset management for RAID is handled elsewhere
        if not hardware.is_md_device(device) and efi_partition_mount_point:
            # NOTE(TheJulia): It may make sense to retool all efi
            # asset preservation logic at some point since the paths
            # can be a little different, but largely this is JUST for
            # partition images as there _should not_ be a mount
            # point if we have no efi partitions at all.
            efi_preserved = _try_preserve_efi_assets(
                device, path, efi_system_part_uuid,
                efi_partition, efi_partition_mount_point)
            if efi_preserved:
                _append_uefi_to_fstab(path, efi_system_part_uuid)
                # Success preserving efi assets
                return
            else:
                # Failure, either via exception or not found
                # which in this case the partition needs to be
                # remounted.
                LOG.debug('No EFI assets were preserved for setup or the '
                          'ramdisk was unable to complete the setup. '
                          'falling back to bootloader installation from '
                          'deployed image.')
                _mount_partition(root_partition, path)

        binary_name = "grub"
        if os.path.exists(os.path.join(path, 'usr/sbin/grub2-install')):
            binary_name = "grub2"

        # Mount all vfat partitions listed in the fstab of the root partition.
        # This is to make sure grub2 finds all files it needs, as some of them
        # may not be inside the root partition but in the ESP (like grub2env).
        LOG.debug("Mounting all partitions inside the image ...")
        utils.execute('chroot %(path)s /bin/sh -c "mount -a -t vfat"' %
                      {'path': path}, shell=True,
                      env_variables={'PATH': path_variable})

        if efi_partition:
            if not os.path.exists(efi_partition_mount_point):
                os.makedirs(efi_partition_mount_point)
            LOG.warning("GRUB2 will be installed for UEFI on efi partition "
                        "%s using the install command which does not place "
                        "Secure Boot signed binaries.", efi_partition)

            _mount_partition(efi_partition, efi_partition_mount_point)
            efi_mounted = True
            try:
                utils.execute('chroot %(path)s /bin/sh -c '
                              '"%(bin)s-install"' %
                              {'path': path, 'bin': binary_name},
                              shell=True,
                              env_variables={
                                  'PATH': path_variable
                              })
            except processutils.ProcessExecutionError as e:
                LOG.warning('Ignoring GRUB2 boot loader installation failure: '
                            '%s.', e)
            try:
                # Also run grub-install with --removable, this installs grub to
                # the EFI fallback path. Useful if the NVRAM wasn't written
                # correctly, was reset or if testing with virt as libvirt
                # resets the NVRAM on instance start.
                # This operation is essentially a copy operation. Use of the
                # --removable flag, per the grub-install source code changes
                # the default file to be copied, destination file name, and
                # prevents NVRAM from being updated.
                # We only run grub2_install for uefi if we can't verify the
                # uefi bits
                utils.execute('chroot %(path)s /bin/sh -c '
                              '"%(bin)s-install --removable"' %
                              {'path': path, 'bin': binary_name},
                              shell=True,
                              env_variables={
                                  'PATH': path_variable
                              })
            except processutils.ProcessExecutionError as e:
                LOG.warning('Ignoring GRUB2 boot loader installation failure: '
                            '%s.', e)
            utils.execute('umount', efi_partition_mount_point, attempts=3,
                          delay_on_retry=True)
            efi_mounted = False
            # NOTE: probably never needed for grub-mkconfig, does not hurt in
            # case of doubt, cleaned in the finally clause anyway
            utils.execute('mount', efi_partition,
                          efi_partition_mount_point)
            efi_mounted = True
        else:
            # FIXME(rg): does not work if ramdisk boot mode is not the same
            # as the target (--target=i386-pc, arch dependent).
            # See previous FIXME

            # Install grub. Normally, grub goes to one disk only. In case of
            # md devices, grub goes to all underlying holder (RAID-1) disks.
            LOG.info("GRUB2 will be installed on disks %s", disks)
            for grub_disk in disks:
                LOG.debug("Installing GRUB2 on disk %s", grub_disk)
                utils.execute(
                    'chroot %(path)s /bin/sh -c "%(bin)s-install %(dev)s"' %
                    {
                        'path': path,
                        'bin': binary_name,
                        'dev': grub_disk
                    },
                    shell=True,
                    env_variables={
                        'PATH': path_variable
                    }
                )
                LOG.debug("GRUB2 successfully installed on device %s",
                          grub_disk)

        # NOTE(TheJulia): Setup grub configuration again since IF we reach
        # this point, then we've manually installed grub which is not the
        # recommended path.
        _configure_grub(device, path)

        if efi_system_part_uuid and efi_mounted:
            _append_uefi_to_fstab(path, efi_system_part_uuid)

        LOG.info("GRUB2 successfully installed on %s", device)

    except processutils.ProcessExecutionError as e:
        error_msg = ('Installing GRUB2 boot loader to device %(dev)s '
                     'failed with %(err)s.' % {'dev': device, 'err': e})
        LOG.error(error_msg)
        raise errors.CommandExecutionError(error_msg)

    finally:
        LOG.debug('Executing _install_grub2 clean-up.')
        # Umount binds and partition
        umount_warn_msg = "Unable to umount %(path)s. Error: %(error)s"

        # If umount fails for efi partition, then we cannot be sure that all
        # the changes were written back to the filesystem.
        try:
            if efi_mounted:
                utils.execute('umount', efi_partition_mount_point, attempts=3,
                              delay_on_retry=True)
        except processutils.ProcessExecutionError as e:
            error_msg = ('Umounting efi system partition failed. '
                         'Attempted 3 times. Error: %s' % e)
            LOG.error(error_msg)
            raise errors.CommandExecutionError(error_msg)

        # If umounting the binds succeed then we can try to delete it
        if _umount_all_partitions(path,
                                  path_variable,
                                  umount_warn_msg):
            try:
                utils.execute('umount', path, attempts=3, delay_on_retry=True)
            except processutils.ProcessExecutionError as e:
                LOG.warning(umount_warn_msg, {'path': path, 'error': e})
            else:
                # After everything is umounted we can then remove the
                # temporary directory
                shutil.rmtree(path)


def _get_path_variable():
    # Add /bin to PATH variable as grub requires it to find efibootmgr
    # when running in uefi boot mode.
    # Add /usr/sbin to PATH variable to ensure it is there as we do
    # not use full path to grub binary anymore.
    path_variable = os.environ.get('PATH', '')
    return '%s:/bin:/usr/sbin:/sbin' % path_variable


def _configure_grub(device, path):
    """Make consolidated grub configuration as it is device aware.

    :param device: The device for the filesystem.
    :param path: The path in which the filesystem is mounted.
    """
    LOG.debug('Attempting to generate grub Configuration')
    path_variable = _get_path_variable()
    binary_name = "grub"
    if os.path.exists(os.path.join(path, 'usr/sbin/grub2-install')):
        binary_name = "grub2"
    # If the image has dracut installed, set the rd.md.uuid kernel
    # parameter for discovered md devices.
    if hardware.is_md_device(device) and _has_dracut(path):
        rd_md_uuids = ["rd.md.uuid=%s" % x['UUID']
                       for x in hardware.md_get_raid_devices().values()]
        LOG.debug("Setting rd.md.uuid kernel parameters: %s", rd_md_uuids)
        with open('%s/etc/default/grub' % path, 'r') as g:
            contents = g.read()
        with open('%s/etc/default/grub' % path, 'w') as g:
            g.write(
                re.sub(r'GRUB_CMDLINE_LINUX="(.*)"',
                       r'GRUB_CMDLINE_LINUX="\1 %s"'
                       % " ".join(rd_md_uuids),
                       contents))

    utils.execute('chroot %(path)s /bin/sh -c '
                  '"%(bin)s-mkconfig -o '
                  '/boot/%(bin)s/grub.cfg"' %
                  {'path': path, 'bin': binary_name}, shell=True,
                  env_variables={'PATH': path_variable,
                                 'GRUB_DISABLE_OS_PROBER': 'true',
                                 'GRUB_SAVEDEFAULT': 'true'},
                  use_standard_locale=True)
    LOG.debug('Completed basic grub configuration.')


def _mount_for_chroot(path):
    """Mount items for grub-mkconfig to succeed."""
    LOG.debug('Mounting Linux standard partitions for bootloader '
              'configuration generation')
    for fs in BIND_MOUNTS:
        utils.execute('mkdir', '-p', path + fs)
        utils.execute('mount', '-o', 'bind', fs, path + fs)
    utils.execute('mount', '-t', 'sysfs', 'none', path + '/sys')


def _try_preserve_efi_assets(device, path,
                             efi_system_part_uuid,
                             efi_partition,
                             efi_partition_mount_point):
    """Attempt to preserve UEFI boot assets.

    :param device: The device upon which to try to preserve assets.
    :param path: The path in which the filesystem is already mounted
                 which we should examine to preserve assets from.
    :param efi_system_part_uuid: The partition ID representing the
                                 created EFI system partition.
    :param efi_partition: The partitions upon which to write the preserved
                          assets to.
    :param efi_partition_mount_point: The folder at which to mount
                                      the assets for the process of
                                      preservation.

    :returns: True if assets have been preserved, otherwise False.
              None is the result of this method if a failure has
              occurred.
    """
    efi_assets_folder = efi_partition_mount_point + '/EFI'
    if os.path.exists(efi_assets_folder):
        # We appear to have EFI Assets, that need to be preserved
        # and as such if we succeed preserving them, we will be returned
        # True from _preserve_efi_assets to correspond with success or
        # failure in this action.
        # NOTE(TheJulia): Still makes sense to invoke grub-install as
        # fragmentation of grub has occurred.
        if (os.path.exists(os.path.join(path, 'usr/sbin/grub2-install'))
            or os.path.exists(os.path.join(path, 'usr/sbin/grub-install'))):
            _configure_grub(device, path)
        # But first, if we have grub, we should try to build a grub config!
        LOG.debug('EFI asset folder detected, attempting to preserve assets.')
        if _preserve_efi_assets(path, efi_assets_folder,
                                efi_partition,
                                efi_partition_mount_point):
            try:
                # Since we have preserved the assets, we should be able
                # to call the _efi_boot_setup method to scan the device
                # and add loader entries
                efi_preserved = _efi_boot_setup(device, efi_system_part_uuid)
                # Executed before the return so we don't return and then begin
                # execution.
                return efi_preserved
            except Exception as e:
                # Remount the partition and proceed as we were.
                LOG.debug('Exception encountered while attempting to '
                          'setup the EFI loader from a root '
                          'filesystem. Error: %s', e)


def _append_uefi_to_fstab(fs_path, efi_system_part_uuid):
    """Append the efi partition id to the filesystem table.

    :param fs_path: The path to the filesystem.
    :param efi_system_part_uuid: uuid to use to try and find the
                                 partition. Warning: this may be
                                 a partition uuid or a actual uuid.
    """
    fstab_file = os.path.join(fs_path, 'etc/fstab')
    if not os.path.exists(fstab_file):
        return
    try:
        # Collect all of the block devices so we appropriately match UUID
        # or PARTUUID into an fstab entry.
        block_devs = hardware.list_all_block_devices(block_type='part')

        # Default to uuid, but if we find a partuuid instead, that is okay,
        # we just need to know later on.
        fstab_label = None
        for bdev in block_devs:
            # Check UUID first
            if bdev.uuid and efi_system_part_uuid in bdev.uuid:
                LOG.debug('Identified block device %(dev)s UUID %(uuid)s '
                          'for UEFI boot. Proceeding with fstab update using '
                          'a UUID.',
                          {'dev': bdev.name,
                           'uuid': efi_system_part_uuid})
                # What we have works, and is correct, we can break the loop
                fstab_label = 'UUID'
                break
            # Fallback to PARTUUID, since we don't know if the provided
            # UUID matches a PARTUUID, or UUID field, and the fstab entry
            # needs to match it.
            if bdev.partuuid and efi_system_part_uuid in bdev.partuuid:
                LOG.debug('Identified block device %(dev)s partition UUID '
                          '%(uuid)s for UEFI boot. Proceeding with fstab '
                          'update using a PARTUUID.',
                          {'dev': bdev.name,
                           'uuid': efi_system_part_uuid})
                fstab_label = 'PARTUUID'
                break

        if not fstab_label:
            # Fallback to prior behavior, which should generally be correct.
            LOG.warning('Falling back to fstab entry addition label of UUID. '
                        'We could not identify which UUID or PARTUUID '
                        'identifier label should be used, thus UUID will be '
                        'used.')
            fstab_label = 'UUID'

        fstab_string = ("%s=%s\t/boot/efi\tvfat\tumask=0077\t"
                        "0\t1\n") % (fstab_label, efi_system_part_uuid)
        with open(fstab_file, "r+") as fstab:
            already_present_string = fstab_label + '=' + efi_system_part_uuid
            if already_present_string not in fstab.read():
                fstab.writelines(fstab_string)
    except (OSError, EnvironmentError, IOError) as exc:
        LOG.debug('Failed to add entry to /etc/fstab. Error %s', exc)
    LOG.debug('Added entry to /etc/fstab for EFI partition auto-mount '
              'with uuid %s', efi_system_part_uuid)


def _efi_boot_setup(device, efi_system_part_uuid=None, target_boot_mode=None):
    """Identify and setup an EFI bootloader from supplied partition/disk.

    :param device: The device upon which to attempt the EFI bootloader setup.
    :param efi_system_part_uuid: The partition UUID to utilize in searching
                                 for an EFI bootloader.
    :param target_boot_mode: The requested boot mode target for the
                             machine. This is optional and is mainly used
                             for the purposes of identifying a mismatch and
                             reporting a warning accordingly.
    :returns: True if we succeeded in setting up an EFI bootloader in the
              EFI nvram table.
              False if we were unable to set the machine to EFI boot,
              due to inability to locate assets required OR the efibootmgr
              tool not being present.
              None is returned if the node is NOT in UEFI boot mode or
              the system is deploying upon a software RAID device.
    """
    boot = hardware.dispatch_to_managers('get_boot_info')
    # Explicitly only run if a target_boot_mode is set which prevents
    # callers following-up from re-logging the same message
    if target_boot_mode and boot.current_boot_mode != target_boot_mode:
        LOG.warning('Boot mode mismatch: target boot mode is %(target)s, '
                    'current boot mode is %(current)s. Installing boot '
                    'loader may fail or work incorrectly.',
                    {'target': target_boot_mode,
                     'current': boot.current_boot_mode})

    if boot.current_boot_mode == 'uefi':
        try:
            utils.execute('efibootmgr', '--version')
        except FileNotFoundError:
            LOG.warning("efibootmgr is not available in the ramdisk")
        else:
            return efi_utils.manage_uefi(
                device, efi_system_part_uuid=efi_system_part_uuid)
        return False


def _preserve_efi_assets(path, efi_assets_folder, efi_partition,
                         efi_partition_mount_point):
    """Preserve the EFI assets in a partition image.

    :param path: The path used for the mounted image filesystem.
    :param efi_assets_folder: The folder where we can find the
                              UEFI assets required for booting.
    :param efi_partition: The partition upon which to write the
                          preserved assets to.
    :param efi_partition_mount_point: The folder at which to mount
                                      the assets for the process of
                                      preservation.
    :returns: True if EFI assets were able to be located and preserved
              to their appropriate locations based upon the supplied
              efi_partition.
              False if any error is encountered in this process.
    """
    try:
        save_efi = os.path.join(tempfile.mkdtemp(), 'efi_loader')
        LOG.debug('Copying EFI assets to %s.', save_efi)
        shutil.copytree(efi_assets_folder, save_efi)

        # Identify grub2 config file for EFI booting as grub may require it
        # in the folder.

        destlist = os.listdir(efi_assets_folder)
        grub2_file = os.path.join(path, 'boot/grub2/grub.cfg')
        if os.path.isfile(grub2_file):
            LOG.debug('Local Grub2 configuration detected.')
            # A grub2 config seems to be present, we should preserve it!
            for dest in destlist:
                grub_dest = os.path.join(save_efi, dest, 'grub.cfg')
                if not os.path.isfile(grub_dest):
                    LOG.debug('A grub.cfg file was not found in %s. %s'
                              'will be copied to that location.',
                              grub_dest, grub2_file)
                    try:
                        shutil.copy2(grub2_file, grub_dest)
                    except (IOError, OSError, shutil.SameFileError) as e:
                        LOG.warning('Failed to copy grub.cfg file for '
                                    'EFI boot operation. Error %s', e)
        grub2_env_file = os.path.join(path, 'boot/grub2/grubenv')
        # NOTE(TheJulia): By saving the default, this file should be created.
        # this appears to what diskimage-builder does.
        # if the file is just a file, then we'll need to copy it. If it is
        # anything else like a link, we're good. This behavior is inconsistent
        # depending on packager install scripts for grub.
        if os.path.isfile(grub2_env_file):
            LOG.debug('Detected grub environment file %s, will attempt '
                      'to copy this file to align with apparent bootloaders',
                      grub2_env_file)
            for dest in destlist:
                grub2env_dest = os.path.join(save_efi, dest, 'grubenv')
                if not os.path.isfile(grub2env_dest):
                    LOG.debug('A grubenv file was not found. Copying '
                              'to %s along with the grub.cfg file as '
                              'grub generally expects it is present.',
                              grub2env_dest)
                    try:
                        shutil.copy2(grub2_env_file, grub2env_dest)
                    except (IOError, OSError, shutil.SameFileError) as e:
                        LOG.warning('Failed to copy grubenv file. '
                                    'Error: %s', e)
        utils.execute('mount', '-t', 'vfat', efi_partition,
                      efi_partition_mount_point)
        shutil.copytree(save_efi, efi_assets_folder)
        LOG.debug('Files preserved to %(disk)s for %(part)s. '
                  'Files: %(filelist)s From: %(from)s',
                  {'disk': efi_partition,
                   'part': efi_partition_mount_point,
                   'filelist': os.listdir(efi_assets_folder),
                   'from': save_efi})
        utils.execute('umount', efi_partition_mount_point)
        return True
    except Exception as e:
        LOG.debug('Failed to preserve EFI assets. Error %s', e)
        try:
            utils.execute('umount', efi_partition_mount_point)
        except Exception as e:
            LOG.debug('Exception encountered while attempting unmount '
                      'the EFI partition mount point. Error: %s', e)
        return False


class ImageExtension(base.BaseAgentExtension):

    @base.async_command('install_bootloader')
    def install_bootloader(self, root_uuid, efi_system_part_uuid=None,
                           prep_boot_part_uuid=None,
                           target_boot_mode='bios',
                           ignore_bootloader_failure=None):
        """Install the GRUB2 bootloader on the image.

        :param root_uuid: The UUID of the root partition.
        :param efi_system_part_uuid: The UUID of the efi system partition.
            To be used only for uefi boot mode.  For uefi boot mode, the
            boot loader will be installed here.
        :param prep_boot_part_uuid: The UUID of the PReP Boot partition.
            Used only for booting ppc64* partition images locally. In this
            scenario the bootloader will be installed here.
        :param target_boot_mode: bios, uefi. Only taken into account
            for softraid, when no efi partition is explicitly provided
            (happens for whole disk images)
        :raises: CommandExecutionError if the installation of the
                 bootloader fails.
        :raises: DeviceNotFound if the root partition is not found.

        """
        device = hardware.dispatch_to_managers('get_os_install_device')

        # Always allow the API client to be the final word on if this is
        # overridden or not.
        if ignore_bootloader_failure is None:
            ignore_failure = CONF.ignore_bootloader_failure
        else:
            ignore_failure = ignore_bootloader_failure

        try:
            if _efi_boot_setup(device, efi_system_part_uuid, target_boot_mode):
                return
        except Exception as e:
            LOG.error('Error setting up bootloader. Error %s', e)
            if not ignore_failure:
                raise

        # We don't have a working root UUID detection for whole disk images.
        # Until we can do it, avoid a confusing traceback.
        if root_uuid == '0x00000000' or root_uuid is None:
            LOG.info('Not using grub2-install since root UUID is not provided.'
                     ' Assuming a whole disk image')
            return

        # In case we can't use efibootmgr for uefi we will continue using grub2
        LOG.debug('Using grub2-install to set up boot files')
        try:
            _install_grub2(device,
                           root_uuid=root_uuid,
                           efi_system_part_uuid=efi_system_part_uuid,
                           prep_boot_part_uuid=prep_boot_part_uuid,
                           target_boot_mode=target_boot_mode)
        except Exception as e:
            LOG.error('Error setting up bootloader. Error %s', e)
            if not ignore_failure:
                raise

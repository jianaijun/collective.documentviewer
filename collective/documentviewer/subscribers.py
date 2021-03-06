from collective.documentviewer import storage
from collective.documentviewer.async import queueJob
from collective.documentviewer.convert import Converter
from collective.documentviewer.settings import GlobalSettings
from collective.documentviewer.settings import Settings
from collective.documentviewer.storage import getResourceDirectory
from collective.documentviewer.utils import allowedDocumentType
from collective.documentviewer.utils import getPortal
from logging import getLogger
from Products.CMFCore.utils import getToolByName

import os
import shutil


logger = getLogger('collective.documentviewer')


def handle_file_creation(obj, event):
    if obj.portal_type == 'Image':
        return
    qi = getToolByName(obj, 'portal_quickinstaller', None)
    if not qi:
        return
    if not qi:
        return
    if not qi.isProductInstalled('collective.documentviewer'):
        return

    site = getPortal(obj)
    gsettings = GlobalSettings(site)

    if not allowedDocumentType(obj, gsettings.auto_layout_file_types):
        return

    auto_layout = gsettings.auto_select_layout
    if auto_layout and obj.getLayout() != 'documentviewer':
        obj.setLayout('documentviewer')

    if obj.getLayout() == 'documentviewer' and gsettings.auto_convert:
        queueJob(obj)


def handle_workflow_change(obj, event):
    if obj.portal_type == 'Image':
        return
    settings = Settings(obj)
    site = getPortal(obj)
    gsettings = GlobalSettings(site)
    if not gsettings.storage_obfuscate or \
            settings.storage_type != 'File':
        return

    for perm in obj.rolesOfPermission("View"):
        if perm['name'] == 'Anonymous' and perm["selected"] != "":
            # anon can now view, move it to normal
            storage_dir = storage_dir = storage.getResourceDirectory(
                gsettings=gsettings, settings=settings)
            secret_dir = os.path.join(storage_dir,
                                      settings.obfuscate_secret)
            if not os.path.exists(secret_dir):
                # already public, oops
                return

            for folder in os.listdir(secret_dir):
                path = os.path.join(secret_dir, folder)
                newpath = os.path.join(storage_dir, folder)
                shutil.move(path, newpath)

            shutil.rmtree(secret_dir)
            settings.obfuscated_filepath = False
            return

    # if we made it here, the item might have been switched back
    # to being unpublished. Let's just get the converter object
    # and re-move it
    converter = Converter(object)
    converter.handleFileObfuscation()


def handle_file_delete(obj, event):
    if obj.portal_type == 'Image':
        return

    # need to remove files if stored in file system
    settings = Settings(obj)
    if settings.storage_type == 'File':
        storage_directory = getResourceDirectory(obj=obj)
        if os.path.exists(storage_directory):
            shutil.rmtree(storage_directory)

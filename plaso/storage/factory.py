# -*- coding: utf-8 -*-
"""This file contains the storage factory class."""

from plaso.lib import definitions
from plaso.storage.redis import reader as redis_reader
from plaso.storage.redis import writer as redis_writer
from plaso.storage.sqlite import reader as sqlite_reader
from plaso.storage.sqlite import sqlite_file
from plaso.storage.sqlite import writer as sqlite_writer


class StorageFactory(object):
  """Storage factory."""

  @classmethod
  def CheckStorageFileHasSupportedFormat(cls, path, check_readable_only=False):
    """Checks if the storage file format is supported.

    Args:
      path (str): path to the storage file.
      check_readable_only (Optional[bool]): whether the store should only be
          checked to see if it can be read. If False, the store will be checked
          to see if it can be read and written to.

    Returns:
      bool: True if the format is supported.
    """
    return sqlite_file.SQLiteStorageFile.CheckSupportedFormat(
        path, check_readable_only=check_readable_only)

  @classmethod
  def CreateStorageFile(cls, storage_format):
    """Creates a storage file.

    Args:
      storage_format (str): storage format.

    Returns:
      StorageFile: a storage file or None if the storage file cannot be
          opened or the storage format is not supported.
    """
    if storage_format == definitions.STORAGE_FORMAT_SQLITE:
      return sqlite_file.SQLiteStorageFile()

    return None

  @classmethod
  def CreateStorageReaderForFile(cls, path):
    """Creates a storage reader based on the file.

    Args:
      path (str): path to the storage file.

    Returns:
      StorageReader: a storage reader or None if the storage file cannot be
          opened or the storage format is not supported.
    """
    if sqlite_file.SQLiteStorageFile.CheckSupportedFormat(
        path, check_readable_only=True):
      return sqlite_reader.SQLiteStorageFileReader(path)

    return None

  @classmethod
  def CreateStorageWriter(cls, storage_format, session, path):
    """Creates a storage writer.

    Args:
      storage_format (str): storage format.
      session (Session): session the storage changes are part of.
      path (str): path to the storage file.

    Returns:
      StorageWriter: a storage writer or None if the storage file cannot be
          opened or the storage format is not supported.
    """
    if storage_format == definitions.STORAGE_FORMAT_SQLITE:
      return sqlite_writer.SQLiteStorageFileWriter(session, path)

    if storage_format == definitions.STORAGE_FORMAT_REDIS:
      return redis_writer.RedisStorageWriter(session)

    return None

  @classmethod
  def CreateStorageWriterForFile(cls, session, path):
    """Creates a storage writer based on the file.

    Args:
      session (Session): session the storage changes are part of.
      path (str): path to the storage file.

    Returns:
      StorageWriter: a storage writer or None if the storage file cannot be
          opened or the storage format is not supported.
    """
    if sqlite_file.SQLiteStorageFile.CheckSupportedFormat(path):
      return sqlite_writer.SQLiteStorageFileWriter(session, path)

    return None

  @classmethod
  def CreateTaskStorageReader(cls, storage_format, task, path):
    """Creates a task storage reader.

    Args:
      storage_format (str): storage format.
      task (Task): task the storage changes are part of.
      path (str): path to the storage file.

    Returns:
      StorageReader: a storage reader or None if the storage file cannot be
          opened or the storage format is not supported.
    """
    if storage_format == definitions.STORAGE_FORMAT_SQLITE:
      return sqlite_reader.SQLiteStorageFileReader(path)

    if storage_format == definitions.STORAGE_FORMAT_REDIS:
      return redis_reader.RedisStorageReader(task)

    return None

  @classmethod
  def CreateTaskStorageWriter(cls, storage_format, session, task, path):
    """Creates a task storage writer.

    Args:
      storage_format (str): storage format.
      session (Session): session the storage changes are part of.
      task (Task): task the storage changes are part of.
      path (str): path to the storage file.

    Returns:
      StorageWriter: a storage writer or None if the storage file cannot be
          opened or the storage format is not supported.
    """
    if storage_format == definitions.STORAGE_FORMAT_SQLITE:
      return sqlite_writer.SQLiteStorageFileWriter(
          session, path, storage_type=definitions.STORAGE_TYPE_TASK, task=task)

    if storage_format == definitions.STORAGE_FORMAT_REDIS:
      return redis_writer.RedisStorageWriter(
          session, storage_type=definitions.STORAGE_TYPE_TASK, task=task)

    return None

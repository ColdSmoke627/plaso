# -*- coding: utf-8 -*-
"""The merge reader."""

from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import reports
from plaso.containers import tasks
from plaso.containers import warnings
from plaso.storage import logger


class StorageMergeReader(object):
  """Storage reader for merging.

  Attributes:
    number_of_containers (int): number of containers merged in last call to
        MergeAttributeContainers.
  """

  _CONTAINER_TYPE_ANALYSIS_REPORT = reports.AnalysisReport.CONTAINER_TYPE
  _CONTAINER_TYPE_ANALYSIS_WARNING = warnings.AnalysisWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA_STREAM = events.EventDataStream.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_SOURCE = event_sources.EventSource.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE
  _CONTAINER_TYPE_EXTRACTION_WARNING = warnings.ExtractionWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_PREPROCESSING_WARNING = (
      warnings.PreprocessingWarning.CONTAINER_TYPE)
  _CONTAINER_TYPE_RECOVERY_WARNING = warnings.RecoveryWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_TASK_COMPLETION = tasks.TaskCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_TASK_START = tasks.TaskStart.CONTAINER_TYPE

  # Some container types reference other container types, such as event
  # referencing event_data. Container types in this tuple must be ordered after
  # all the container types they reference.
  _CONTAINER_TYPES = (
      _CONTAINER_TYPE_EVENT_SOURCE,
      _CONTAINER_TYPE_EVENT_DATA_STREAM,
      _CONTAINER_TYPE_EVENT_DATA,
      _CONTAINER_TYPE_EVENT,
      _CONTAINER_TYPE_EVENT_TAG,
      _CONTAINER_TYPE_EXTRACTION_WARNING,
      _CONTAINER_TYPE_RECOVERY_WARNING,
      _CONTAINER_TYPE_ANALYSIS_REPORT,
      _CONTAINER_TYPE_ANALYSIS_WARNING)

  def __init__(self, storage_writer, task_storage_reader):
    """Initializes a storage merge reader.

    Args:
      storage_writer (StorageWriter): storage writer.
      task_storage_reader (StorageReader): task storage reader.
    """
    super(StorageMergeReader, self).__init__()
    self._active_container_type = None
    self._active_generator = None
    self._container_types = []
    self._event_data_identifier_mappings = {}
    self._event_data_stream_identifier_mappings = {}
    self._storage_writer = storage_writer
    self._task_storage_reader = task_storage_reader

    self.number_of_containers = 0

  def Close(self):
    """Closes the merge reader."""
    self._task_storage_reader.Close()
    self._task_storage_reader = None

  def AddAttributeContainer(self, container):
    """Adds an attribute container.

    Args:
      container (AttributeContainer): attribute container.
    """
    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      event_data_identifier = container.GetEventDataIdentifier()
      lookup_key = event_data_identifier.CopyToString()

      event_data_identifier = self._event_data_identifier_mappings.get(
          lookup_key, None)

      if event_data_identifier:
        container.SetEventDataIdentifier(event_data_identifier)
      else:
        identifier = container.GetIdentifier()
        identifier = identifier.CopyToString()

        # TODO: store this as an extraction warning so this is preserved
        # in the storage file.
        logger.error((
            'Unable to merge event attribute container: {0:s} since '
            'corresponding event data: {1:s} could not be found.').format(
                identifier, lookup_key))
        return

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      event_data_stream_identifier = container.GetEventDataStreamIdentifier()
      lookup_key = None
      if event_data_stream_identifier:
        lookup_key = event_data_stream_identifier.CopyToString()

        event_data_stream_identifier = (
            self._event_data_stream_identifier_mappings.get(lookup_key, None))

      if event_data_stream_identifier:
        container.SetEventDataStreamIdentifier(event_data_stream_identifier)
      elif lookup_key:
        identifier = container.GetIdentifier()
        identifier = identifier.CopyToString()

        # TODO: store this as an extraction warning so this is preserved
        # in the storage file.
        logger.error((
            'Unable to merge event data attribute container: {0:s} since '
            'corresponding event data stream: {1:s} could not be '
            'found.').format(identifier, lookup_key))
        return

    if container.CONTAINER_TYPE in (
        self._CONTAINER_TYPE_EVENT_DATA,
        self._CONTAINER_TYPE_EVENT_DATA_STREAM):
      identifier = container.GetIdentifier()
      lookup_key = identifier.CopyToString()

    self._storage_writer.AddAttributeContainer(container)

    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      identifier = container.GetIdentifier()
      self._event_data_identifier_mappings[lookup_key] = identifier

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA_STREAM:
      identifier = container.GetIdentifier()
      self._event_data_stream_identifier_mappings[lookup_key] = identifier

  def MergeAttributeContainers(self, maximum_number_of_containers=0):
    """Reads attribute containers from a task store into the writer.

    Args:
      maximum_number_of_containers (Optional[int]): maximum number of
          containers to merge, where 0 represent no limit.

    Returns:
      bool: True if the entire task storage file has been merged.
    """
    if not self._container_types:
      self._container_types = list(self._CONTAINER_TYPES)

    if not self._active_container_type:
      logger.debug('Starting merge')
    else:
      logger.debug('Continuing merge of: {0:s}'.format(
          self._active_container_type))

    self.number_of_containers = 0

    while self._active_generator or self._container_types:
      if not self._active_generator:
        self._active_container_type = self._container_types.pop(0)
        self._active_generator = (
            self._task_storage_reader.GetAttributeContainers(
                self._active_container_type))

      try:
        container = next(self._active_generator)
        self.number_of_containers += 1
      except StopIteration:
        container = None
        self._active_generator = None

      if container:
        self.AddAttributeContainer(container)

      if 0 < maximum_number_of_containers <= self.number_of_containers:
        break

    merge_completed = not self._active_generator and not self._container_types

    logger.debug('Merged {0:d} containers'.format(self.number_of_containers))

    return merge_completed

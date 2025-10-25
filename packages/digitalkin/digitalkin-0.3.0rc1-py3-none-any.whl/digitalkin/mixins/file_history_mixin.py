"""Context mixins providing ergonomic access to service strategies.

This module provides mixins that wrap service strategy calls with cleaner APIs,
following Django/FastAPI patterns where context is passed explicitly to each method.
"""

from digitalkin.mixins.logger_mixin import LoggerMixin
from digitalkin.mixins.storage_mixin import StorageMixin
from digitalkin.models.module.module_context import ModuleContext
from digitalkin.models.services.storage import FileHistory, FileModel


class FileHistoryMixin(StorageMixin, LoggerMixin):
    """Mixin providing File history operations through storage strategy.

    This mixin provides a higher-level API for managing File history,
    using the storage strategy as the underlying persistence mechanism.
    """

    file_history_front: FileHistory = FileHistory(files=[])
    FILE_HISTORY_COLLECTION = "file_history"
    FILE_HISTORY_RECORD_ID = "full_file_history"

    def _get_history_key(self, context: ModuleContext) -> str:
        """Get session-specific history key.

        Args:
            context: Module context containing session information

        Returns:
            Unique history key for the current session
        """
        # TODO: define mission-specific chat history key not dependant on mission_id
        # or need customization by user
        mission_id = getattr(context.session, "mission_id", None) or "default"
        return f"{self.FILE_HISTORY_RECORD_ID}_{mission_id}"

    def load_file_history(self, context: ModuleContext) -> FileHistory:
        """Load File history for the current session.

        Args:
            context: Module context containing storage strategy

        Returns:
            File history object, empty if none exists or loading fails
        """
        history_key = self._get_history_key(context)

        if self.file_history_front is None:
            try:
                record = self.read_storage(
                    context,
                    self.FILE_HISTORY_COLLECTION,
                    history_key,
                )
                if record and record.data:
                    return FileHistory.model_validate(record.data)
            except Exception as e:
                self.log_warning(context, f"Failed to load File history: {e}")
        return self.file_history_front

    def append_files_history(self, context: ModuleContext, files: list[FileModel]) -> None:
        """Append a message to File history.

        Args:
            context: Module context containing storage strategy
            files: list of files model

        Raises:
            StorageServiceError: If history update fails
        """
        history_key = self._get_history_key(context)
        file_history = self.load_file_history(context)

        file_history.files.extend(files)
        if len(file_history.files) == len(files):
            # Create new record
            self.log_debug(context, f"Creating new file history for session: {history_key}")
            self.store_storage(
                context,
                self.FILE_HISTORY_COLLECTION,
                history_key,
                file_history.model_dump(),
                data_type="OUTPUT",
            )
        else:
            self.log_debug(context, f"Updating file history for session: {history_key}")
            self.update_storage(
                context,
                self.FILE_HISTORY_COLLECTION,
                history_key,
                file_history.model_dump(),
            )

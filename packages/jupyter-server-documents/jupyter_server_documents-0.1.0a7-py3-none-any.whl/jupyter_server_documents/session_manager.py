import os
from typing import Optional, Any
from jupyter_server.services.sessions.sessionmanager import SessionManager, KernelName, ModelName
from jupyter_server.serverapp import ServerApp
from jupyter_server_fileid.manager import BaseFileIdManager
from jupyter_server_documents.rooms.yroom_manager import YRoomManager
from jupyter_server_documents.rooms.yroom import YRoom
from jupyter_server_documents.kernels.kernel_client import DocumentAwareKernelClient


class YDocSessionManager(SessionManager): 
    """A Jupyter Server Session Manager that connects YDocuments
    to Kernel Clients.
    """
    
    @property
    def serverapp(self) -> ServerApp:
        """When running in Jupyter Server, the parent 
        of this class is an instance of the ServerApp.
        """
        return self.parent
    
    @property
    def file_id_manager(self) -> BaseFileIdManager:
        """The Jupyter Server's File ID Manager."""
        return self.serverapp.web_app.settings["file_id_manager"]
    
    @property
    def yroom_manager(self) -> YRoomManager:
        """The Jupyter Server's YRoom Manager."""
        return self.serverapp.web_app.settings["yroom_manager"]

    _room_ids: dict[str, str]
    """
    Dictionary of room IDs, keyed by session ID.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._room_ids = {}

    def get_kernel_client(self, kernel_id: str) -> DocumentAwareKernelClient:
        """Get the kernel client for a running kernel."""
        kernel_manager = self.kernel_manager.get_kernel(kernel_id)
        kernel_client = kernel_manager.main_client
        return kernel_client

    def get_yroom(self, session_id: str) -> YRoom:
        """
        Get the `YRoom` for a session given its ID. The session must have
        been created first via a call to `create_session()`.
        """
        room_id = self._room_ids.get(session_id, None)
        yroom = self.yroom_manager.get_room(room_id) if room_id else None
        if not yroom:
            raise LookupError(f"No room found for session '{session_id}'.")
        return yroom
    

    def _init_session_yroom(self, session_id: str, path: str) -> YRoom:
        """
        Returns a `YRoom` for a session identified by the given `session_id` and
        `path`. This should be called only in `create_session()`.

        This method stores the new room ID & session ID in `self._room_ids`. The
        `YRoom` for a session can be retrieved via `self.get_yroom()` after this
        method is called.
        """
        file_id = self.file_id_manager.index(path)
        room_id = f"json:notebook:{file_id}"
        yroom = self.yroom_manager.get_room(room_id)
        self._room_ids[session_id] = room_id

        return yroom

    async def create_session(
        self,
        path: Optional[str] = None,
        name: Optional[ModelName] = None,
        type: Optional[str] = None,
        kernel_name: Optional[KernelName] = None,
        kernel_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        After creating a session, connects the yroom to the kernel client.
        """
        session_model = await super().create_session(
            path,
            name,
            type,
            kernel_name,
            kernel_id
        )
        session_id = session_model["id"]
        if kernel_id is None:
            kernel_id = session_model["kernel"]["id"]

        # If the type is not 'notebook', return the session model immediately
        if type != "notebook":
            self.log.warning(
                f"Document type '{type}' is not recognized by YDocSessionManager."
            )
            return session_model

        # If name or path is None, we cannot map to a yroom,
        # so just move on.
        if name is None or path is None:
            self.log.warning(f"`name` or `path` was not given for new session at '{path}'.")
            return session_model

        # Otherwise, get a `YRoom` and add it to this session's kernel client.

        # When JupyterLab creates a session, it uses a fake path
        # which is the relative path + UUID, i.e. the notebook
        # name is incorrect temporarily. It later makes multiple
        # updates to the session to correct the path.
        # 
        # Here, we create the true path to store in the fileID service
        # by dropping the UUID and appending the file name.
        real_path = os.path.join(os.path.split(path)[0], name)

        # Get YRoom for this session and store its ID in `self._room_ids`
        yroom = self._init_session_yroom(session_id, real_path)

        # Add YRoom to this session's kernel client
        # TODO: we likely have a race condition here... need to 
        # think about it more. Currently, the kernel client gets
        # created after the kernel starts fully. We need the 
        # kernel client instantiated _before_ trying to connect
        # the yroom.
        kernel_client = self.get_kernel_client(kernel_id)
        await kernel_client.add_yroom(yroom)
        self.log.info(f"Connected yroom {yroom.room_id} to kernel {kernel_id}. yroom: {yroom}")
        return session_model
    

    async def update_session(self, session_id: str, **update) -> None:
        """
        Updates the session identified by `session_id` using the keyword
        arguments passed to this method. Each keyword argument should correspond
        to a column in the sessions table.

        This class calls the `update_session()` parent method, then updates the
        kernel client if `update` contains `kernel_id`.
        """
        # Apply update and return early if `kernel_id` was not updated
        if "kernel_id" not in update:
            return await super().update_session(session_id, **update)
        
        # Otherwise, first remove the YRoom from the old kernel client and add
        # the YRoom to the new kernel client, before applying the update.
        old_session_info = (await self.get_session(session_id=session_id) or {})
        old_kernel_id = old_session_info.get("kernel_id", None)
        new_kernel_id = update.get("kernel_id", None)
        self.log.info(
            f"Updating session '{session_id}' from kernel '{old_kernel_id}' "
            f"to kernel '{new_kernel_id}'."
        )
        yroom = self.get_yroom(session_id)
        if old_kernel_id:
            old_kernel_client = self.get_kernel_client(old_kernel_id)
            await old_kernel_client.remove_yroom(yroom=yroom)
        if new_kernel_id:
            new_kernel_client = self.get_kernel_client(new_kernel_id)
            await new_kernel_client.add_yroom(yroom=yroom)

        # Apply update and return
        return await super().update_session(session_id, **update)
    
    
    async def delete_session(self, session_id):
        """
        Deletes the session and disconnects the yroom from the kernel client.
        """
        session = await self.get_session(session_id=session_id)
        kernel_id = session["kernel"]["id"]

        # Remove YRoom from session's kernel client
        yroom = self.get_yroom(session_id)
        kernel_client = self.get_kernel_client(kernel_id)
        await kernel_client.remove_yroom(yroom)

        # Remove room ID stored for the session
        self._room_ids.pop(session_id, None)

        # Delete the session via the parent method
        await super().delete_session(session_id)
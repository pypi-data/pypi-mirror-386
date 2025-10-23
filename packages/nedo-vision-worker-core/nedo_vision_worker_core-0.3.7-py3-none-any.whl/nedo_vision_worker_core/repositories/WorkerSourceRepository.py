from .BaseRepository import BaseRepository
from ..models.worker_source import WorkerSourceEntity


class WorkerSourceRepository(BaseRepository):
    def __init__(self):
        super().__init__(db_name="config")

    def get_worker_sources(self):
        """
        Fetch all worker sources from the local database in a single query.

        Returns:
            list: A list of WorkerSourceEntity records.
        """
        with self._get_session() as session:
            session.expire_all()
            sources = session.query(WorkerSourceEntity).all()
            for source in sources:
                session.expunge(source)
            return sources

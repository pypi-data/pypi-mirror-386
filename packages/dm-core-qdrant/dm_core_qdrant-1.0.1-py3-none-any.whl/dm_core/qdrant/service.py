from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.models import Filter
from dm_core.redis.utils import singleton
from django.conf import settings


@singleton
class QdrantService:

    def __init__(self):
        self.collection_name = settings.QDRANT['COLLECTION']['JOBS']
        self.client = QdrantClient(
            host=settings.QDRANT['SERVICE'],
            port=int(settings.QDRANT['PORT']),
            api_key=settings.QDRANT['API_KEY'],
            https=False
        )
        self._create_collection_if_not_exists()

    def _create_collection_if_not_exists(self, vector_size: int = 384, distance: Distance = Distance.COSINE):
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance)
            )

    def recreate_collection(self, vector_size: int = 384, distance: Distance = Distance.COSINE):
        """
        recreate_collection: Call this method only from unit tests
        """
        self.client.delete_collection(self.collection_name)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance)
        )
        return self

    def upsert_point(self, key: str, payload: dict, vector):
        point = PointStruct(id=key, vector=vector, payload=payload)
        return self.client.upsert(collection_name=self.collection_name, points=[point])

    def upsert_points(self, points: list[PointStruct]):
        return self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, query, top_k: int = 5, offset: int = 0, filter: Filter = None, with_payload: bool = True):
        kwargs = {
            "collection_name": self.collection_name,
            "query": query,
            "limit": top_k,
            "offset": offset,
            "with_payload": with_payload
        }
        if filter is not None:
            kwargs["filter"] = filter
        return self.client.query_points(**kwargs)

    def delete_point(self, key: str):
        return self.client.delete(
            collection_name=self.collection_name,
            points_selector=[key]
        )

    def list_collections(self):
        return self.client.get_collections()

    def delete_collection(self):
        return self.client.delete_collection(self.collection_name)

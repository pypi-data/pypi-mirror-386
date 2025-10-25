"""Qdrant vector store, built on top of an existing Qdrant collection."""

__all__ = [
    'HybridFuse',
    'QdrantVectorStore',
]

import asyncio
import logging
from collections.abc import Awaitable, Callable, Iterable, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    NamedTuple,
    Protocol,
    cast,
    runtime_checkable,
)

from glow import astreaming
from grpc import RpcError
from llama_index.core.schema import MetadataMode
from llama_index.core.vector_stores import MetadataFilters
from pydantic import BaseModel, PrivateAttr
from qdrant_client import AsyncQdrantClient
from qdrant_client.conversions.common_types import QuantizationConfig
from qdrant_client.fastembed_common import IDF_EMBEDDING_MODELS
from qdrant_client.http import models as rest
from qdrant_client.http.exceptions import UnexpectedResponse

from ._nodes import metadata_dict_to_node, node_to_metadata_dict
from ._types import SparseEncode
from .fastembed import get_sparse_encoder
from .util import aretry

if TYPE_CHECKING:
    from llama_index.core.schema import BaseNode
    from llama_index.core.vector_stores import MetadataFilter, VectorStoreQuery

type _QueryResponse = Sequence[tuple['BaseNode', float]]

_DENSE_NAME = 'text-dense'
_SPARSE_NAME = 'text-sparse'
_SPARSE_MODIFIERS = dict.fromkeys(IDF_EMBEDDING_MODELS, rest.Modifier.IDF)
_LOCK = asyncio.Lock()
logger = logging.getLogger(__name__)


class _QueryData(NamedTuple):
    vector: list[float] | rest.SparseVector
    limit: int
    threshold: float | None = None


@runtime_checkable
class HybridFuse(Protocol):
    def __call__(
        self,
        dense: Sequence[rest.ScoredPoint],
        sparse: Sequence[rest.ScoredPoint],
        /,
        *,
        alpha: float = ...,
        top_k: int = ...,
    ) -> Sequence[rest.ScoredPoint]: ...


def _relative_score_fusion(
    dense: Sequence[rest.ScoredPoint],
    sparse: Sequence[rest.ScoredPoint],
    # NOTE: only for hybrid search (0 for sparse search, 1 for dense search)
    alpha: float = 0.5,
    top_k: int = 2,
) -> Sequence[rest.ScoredPoint]:
    """Fuse dense and sparse results using relative score fusion."""
    if not dense and not sparse:
        return []
    if alpha >= 1:
        return dense
    if alpha <= 0:
        return sparse

    # Normalize scores
    if dense:
        dense = [
            p.model_copy(update={'score': x})
            for p, x in zip(dense, _min_max([p.score for p in dense]))
        ]
    if sparse:
        sparse = [
            p.model_copy(update={'score': x})
            for p, x in zip(sparse, _min_max([p.score for p in sparse]))
        ]

    dense_scores = {p.id: p.score for p in dense}
    sparse_scores = {p.id: p.score for p in sparse}

    # Update scores
    scored = (
        (p, dense_scores.get(id_, 0), sparse_scores.get(id_, 0))
        for id_, p in {p.id: p for p in [*dense, *sparse]}.items()
    )
    points = [
        p.model_copy(update={'score': (1 - alpha) * ss + alpha * ds})
        for p, ds, ss in scored
    ]

    points = sorted(points, key=lambda p: p.score, reverse=True)
    return points[:top_k] if top_k > 0 else points


class QdrantVectorStore(BaseModel):
    """Fork of LlamaIndex's Qdrant Vector Store.

    Differences:
    - async only
    - no legacy formats
    - no legacy sparse embeddings
    - Qdrant Query API

    In this vector store, embeddings and docs are stored within a
    Qdrant collection.

    During query time, the index uses Qdrant to query for the top
    k most similar nodes.
    """

    model_config = {'arbitrary_types_allowed': True}

    collection_name: str
    aclient: AsyncQdrantClient
    upsert_timeout: float | None = None  # enable to batch upserts
    upsert_batch_size: int | None = 64
    query_timeout: float | None = None  # enable to batch upserts
    query_batch_size: int | None = 64
    max_retries: int = 3

    # Collection construction parameters
    dense_config: rest.VectorParams | None = None
    sparse_config: rest.SparseVectorParams | None = None
    shard_number: int | None = None
    hnsw_config: rest.HnswConfigDiff | None = None
    optimizers_config: rest.OptimizersConfigDiff | None = None
    quantization_config: QuantizationConfig | None = None
    tenant_fields: list[str] = []  # For multitenancy

    # Sparse search parameters
    sparse_doc_fn: SparseEncode | None = None
    sparse_query_fn: SparseEncode | None = None
    sparse_model: str | None = None
    sparse_model_kwargs: dict[str, Any] = {}

    # Hybrid search fusion
    hybrid_fusion_fn: HybridFuse = _relative_score_fusion

    _update: Callable[
        [Sequence['BaseNode | str']],
        Awaitable[Sequence[str]],
    ] = PrivateAttr()
    _query: Callable[
        [Sequence[rest.QueryRequest]],
        Awaitable[Sequence[Sequence[rest.ScoredPoint]]],
    ] = PrivateAttr()

    _is_initialized: bool = PrivateAttr()
    _is_legacy: bool = PrivateAttr()

    def model_post_init(self, context) -> None:
        retry_ = aretry(
            RpcError,
            UnexpectedResponse,
            max_attempts=self.max_retries,
        )
        update = self._ll_update
        if self.upsert_timeout is not None:
            update = astreaming(
                update,
                batch_size=self.upsert_batch_size,
                timeout=self.upsert_timeout,
            )
        self._update = retry_(update)

        query = self._ll_query
        if self.query_timeout is not None:
            query = astreaming(
                query,
                batch_size=self.query_batch_size,
                timeout=self.query_timeout,
            )
        self._query = retry_(query)

        self._is_initialized = False
        self._is_legacy = False

    async def initialize(self, vector_size: int) -> None:
        if self._is_initialized:
            return
        async with _LOCK:
            await self._initialize_unsafe(vector_size)

    async def is_initialized(self) -> bool:
        if self._is_initialized:
            return True
        async with _LOCK:
            return await self._is_initialized_unsafe()

    async def _initialize_unsafe(self, vector_size: int) -> None:
        dense_config = self.dense_config or rest.VectorParams(
            size=vector_size,
            distance=rest.Distance.COSINE,
        )
        vectors_config = {_DENSE_NAME: dense_config}

        await self._load_models()
        if self.sparse_query_fn and self.sparse_doc_fn:
            sparse_config = self.sparse_config or rest.SparseVectorParams(
                modifier=_SPARSE_MODIFIERS.get(self.sparse_model or '')
            )
            sparse_vectors_config = {_SPARSE_NAME: sparse_config}
        else:
            sparse_vectors_config = None

        try:
            await self.aclient.create_collection(
                self.collection_name,
                vectors_config=vectors_config,
                sparse_vectors_config=sparse_vectors_config,
                shard_number=self.shard_number,
                hnsw_config=self.hnsw_config,
                optimizers_config=self.optimizers_config,
                quantization_config=self.quantization_config,
            )

            self._is_initialized = True
        except (RpcError, ValueError, UnexpectedResponse) as exc:
            if 'already exists' not in str(exc):
                raise exc  # noqa: TRY201
            logger.warning(
                'Collection %s already exists, skipping collection creation.',
                self.collection_name,
            )
            assert await self._is_initialized_unsafe()

        await self._setup_indices()

    async def _setup_indices(self):
        tenant_schema = rest.KeywordIndexParams(
            type=rest.KeywordIndexType.KEYWORD, is_tenant=True
        )
        name_n_schema = [('doc_id', rest.PayloadSchemaType.KEYWORD)] + [
            (field, tenant_schema) for field in self.tenant_fields
        ]

        # To improve search performance set up a payload index
        # for fields used in filters.
        # https://qdrant.tech/documentation/concepts/indexing
        aws = (
            self.aclient.create_payload_index(
                self.collection_name, field_name=name, field_schema=schema
            )
            for name, schema in name_n_schema
        )
        await asyncio.gather(*aws)

    async def _is_initialized_unsafe(self) -> bool:
        if not await self.aclient.collection_exists(self.collection_name):
            return False
        await self._load_models()
        info = await self.aclient.get_collection(self.collection_name)

        dense = info.config.params.vectors
        if isinstance(dense, rest.VectorParams):
            logger.warning(
                'Collection %s is using legacy anonymous vectors. '
                'Recreate it to allow sparse/hybrid search',
                self.collection_name,
            )
            self._is_legacy = True
        elif isinstance(dense, dict) and _DENSE_NAME in dense:
            self._is_legacy = False
        else:
            msg = f'Bad vector config {dense}'
            raise TypeError(msg)

        sparse = info.config.params.sparse_vectors
        if isinstance(sparse, dict) and _SPARSE_NAME in sparse:
            if not self.sparse_query_fn:
                logger.warning(
                    'Collection %s support '
                    'sparse search, but neither '
                    'sparse_query_fn nor sparse_model was provided',
                    self.collection_name,
                )
            if not self.sparse_doc_fn:
                logger.warning(
                    'Collection %s support '
                    'sparse search, but neither '
                    'sparse_doc_fn nor sparse_model was provided',
                    self.collection_name,
                )
        else:
            self.sparse_query_fn = self.sparse_doc_fn = None

        self._is_initialized = True
        return True

    async def _load_models(self) -> None:
        if self.sparse_model is None or (
            self.sparse_doc_fn is not None and self.sparse_query_fn is not None
        ):
            return

        encoder = await asyncio.to_thread(
            get_sparse_encoder, self.sparse_model, **self.sparse_model_kwargs
        )
        self.sparse_doc_fn = self.sparse_doc_fn or encoder
        self.sparse_query_fn = self.sparse_query_fn or encoder

    # CRUD: create or update
    async def async_add(self, nodes: Sequence['BaseNode'], /) -> Sequence[str]:
        """Add nodes with embeddings to Qdrant index.

        Returns node IDs that were added to the index.
        """
        return await self._update(nodes)

    async def _build_points(
        self, nodes: Sequence['BaseNode'], /
    ) -> list[rest.PointStruct]:
        if not nodes:
            return []
        sparse_embeddings: Sequence[rest.SparseVector | None]
        if self.sparse_doc_fn:
            sparse_embeddings = await _aembed_sparse(
                *(n.get_content(MetadataMode.EMBED) for n in nodes),
                fn=self.sparse_doc_fn,
            )
        else:
            sparse_embeddings = [None for _ in nodes]

        points: list[rest.PointStruct] = []
        for node, semb in zip(nodes, sparse_embeddings, strict=True):
            demb = node.embedding

            vector: rest.VectorStruct | None
            if self._is_legacy:
                vector = demb
            else:
                vecs = {_DENSE_NAME: demb, _SPARSE_NAME: semb}
                vector = {k: v for k, v in vecs.items() if v is not None}
            if not vector:
                raise ValueError('Embedding is not set')

            payload = node_to_metadata_dict(node)

            pt = rest.PointStruct(id=node.id_, vector=vector, payload=payload)
            points.append(pt)
        return points

    # CRUD: read
    async def aquery(
        self,
        query: 'VectorStoreQuery',
        /,
        *,
        qdrant_filters: rest.Filter | None = None,
        with_payload: Sequence[str] | bool = True,
        dense_threshold: float | None = None,
    ) -> '_QueryResponse':
        """Query index for top k most similar nodes."""
        #  NOTE: users can pass in qdrant_filters
        # (nested/complicated filters) to override the default MetadataFilters
        if qdrant_filters is None:
            qdrant_filters = _build_filter(
                query.doc_ids, query.node_ids, query.filters
            )

        if query.query_embedding is None and query.query_str is None:
            assert query.node_ids
            assert query.doc_ids is None
            assert query.filters is None
            records = await self.qretrieve(
                query.node_ids, with_payload=with_payload
            )
            return _parse_query_results(records)

        dq, sq, hybrid_k, alpha = await self._parse_query(
            query, similarity=dense_threshold
        )
        points = await self.qquery(
            alpha=alpha,
            hybrid_k=hybrid_k,
            dq=dq,
            sq=sq,
            filters=qdrant_filters,
            with_payload=with_payload,
        )
        return _parse_query_results(points)

    async def qretrieve(
        self,
        ids: Sequence[str | int],
        with_payload: Sequence[str] | bool = True,
    ) -> list[rest.Record]:
        if not await self.is_initialized():
            return []
        return await self.aclient.retrieve(
            self.collection_name, ids, with_payload=with_payload
        )

    async def qquery(
        self,
        alpha: float,
        hybrid_k: int = 0,
        dq: _QueryData | None = None,
        sq: _QueryData | None = None,
        filters: rest.Filter | None = None,
        with_payload: Sequence[str] | bool = True,
    ) -> Sequence[rest.Record | rest.ScoredPoint]:
        if not await self.is_initialized():
            return []

        # TODO: possible optimization.
        # Use prefetch={filter=filter_, lookup_from=<other collection>}
        #   and no filter in QueryRequest itself,
        # or call scroll first.
        # But for this we need to ensure that limit is infinite,
        #  otherwise we should use another storage for filters.

        # TODO: handle MMR in qdrant

        if isinstance(with_payload, Sequence):
            with_payload = list(with_payload)

        reqs: list[rest.QueryRequest] = []
        if dq:
            # Dense scores are absolute, i.e. depend only on (query, node),
            # thus we can apply some globally fixed score threshold.
            reqs.append(
                rest.QueryRequest(
                    query=dq.vector,
                    using=None if self._is_legacy else _DENSE_NAME,
                    filter=filters,
                    score_threshold=dq.threshold,
                    limit=dq.limit,
                    with_payload=with_payload,
                )
            )

        if sq:
            # Sparse scores are computed relative to the whole candidate list,
            # so we cannot threshold them,
            # and only able to directly limit their count.
            reqs.append(
                rest.QueryRequest(
                    query=sq.vector,
                    using=_SPARSE_NAME,
                    filter=filters,
                    limit=sq.limit,
                    with_payload=with_payload,
                )
            )

        if not reqs:
            return []

        results = await self._query(reqs)
        if len(results) != 2:  # (dense) or (sparse)
            return results[0]

        # (dense, sparse)
        assert hybrid_k > 0
        assert self.hybrid_fusion_fn is not None
        return self.hybrid_fusion_fn(*results, alpha=alpha, top_k=hybrid_k)

    async def _parse_query(
        self, q: 'VectorStoreQuery', similarity: float | None = None
    ) -> tuple[_QueryData | None, _QueryData | None, int, float]:
        match q.mode.value:
            case 'default':
                alpha = 1.0
            case 'hybrid':
                alpha = 0.5 if q.alpha is None else max(0, min(q.alpha, 1))
            case 'sparse':
                alpha = 0.0
            case _ as unsupported:
                msg = f'Unsupported query mode: {unsupported}'
                raise NotImplementedError(msg)

        if not await self.is_initialized():
            return None, None, 0, alpha

        dense_k = q.similarity_top_k
        sparse_k = dense_k if q.sparse_top_k is None else q.sparse_top_k
        hybrid_k = dense_k if q.hybrid_top_k is None else q.hybrid_top_k

        # With hybrid search we get:
        # - some nodes from dense search;
        # - some nodes from sparse search;
        # - and some nodes coming from both with merged scores.
        # The larger `dense_k`/`sparse_k` the higher chances to get these.

        # `hybrid_k` is effective only up to `dense_k+sparse_k`
        hybrid_k = min(hybrid_k, dense_k + sparse_k)

        dense = sparse = None

        if alpha < 1 and sparse_k:
            if not self.sparse_query_fn:
                msg = (
                    f'Collection {self.collection_name} does not '
                    'have sparse vectors to do sparse search. '
                    'Please reinitialize it with sparse model '
                    'to allow sparse/hybrid search'
                )
                raise ValueError(msg)

            if not q.query_str:
                msg = '`query_str` is required for sparse queries'
                raise ValueError(msg)

            [sparse_embedding] = await _aembed_sparse(
                q.query_str, fn=self.sparse_query_fn
            )
            sparse = _QueryData(sparse_embedding, sparse_k)

        if alpha > 0 and dense_k:
            if not q.query_embedding:
                msg = '`query_embedding` is required for dense queries'
                raise ValueError(msg)

            dense = _QueryData(q.query_embedding, dense_k, similarity)

        return dense, sparse, hybrid_k, alpha

    # CRUD: delete
    async def adelete(self, ref_doc_id: str) -> None:
        if not await self.is_initialized():
            return
        cond = rest.FieldCondition(
            key='doc_id', match=rest.MatchValue(value=ref_doc_id)
        )
        await self.aclient.delete(
            self.collection_name, rest.Filter(must=[cond])
        )

    # CRUD: delete
    async def adelete_nodes(self, node_ids: Sequence[str], /) -> None:
        await self._update(node_ids)

    async def aclear(self) -> None:
        async with _LOCK:
            await self.aclient.delete_collection(self.collection_name)
            self._is_initialized = False

    # low levels

    async def _ll_update(
        self, nodes: Sequence['BaseNode | str'], /
    ) -> Sequence[str]:
        ids = [n if isinstance(n, str) else n.id_ for n in nodes]

        # Merge and deduplicate updates & deletions
        updates = dict(
            (n, None) if isinstance(n, str) else (n.id_, n) for n in nodes
        )
        add_nodes = [n for n in updates.values() if n is not None]
        rm_ids = [id_ for id_, n in updates.items() if n is None]

        aws: list[Awaitable] = []

        if add_nodes:
            await self.initialize(len(add_nodes[0].get_embedding()))

            points = await self._build_points(add_nodes)
            aws.append(self.aclient.upsert(self.collection_name, points))

        if rm_ids and await self.is_initialized():
            cond = rest.HasIdCondition(has_id=rm_ids)  # type: ignore[arg-type]
            aws.append(
                self.aclient.delete(
                    self.collection_name, rest.Filter(must=[cond])
                )
            )

        if aws:
            await asyncio.gather(*aws)

        return ids

    async def _ll_query(
        self, reqs: Sequence[rest.QueryRequest], /
    ) -> Sequence[Sequence[rest.ScoredPoint]]:
        if not reqs:
            return []
        qrs = await self.aclient.query_batch_points(self.collection_name, reqs)
        return [r.points for r in qrs]


async def _aembed_sparse(
    *queries: str, fn: SparseEncode
) -> list[rest.SparseVector]:
    ichunk, vchunk = await asyncio.to_thread(fn, queries)
    return [
        rest.SparseVector(indices=ids, values=vs)
        for ids, vs in zip(ichunk, vchunk, strict=True)
    ]


def _min_max(xs: Sequence[float], /) -> Sequence[float]:
    lo, hi = min(xs), max(xs)
    if ptp := hi - lo:
        return [(x - lo) / ptp for x in xs]  # scale to 0..1
    return [0.5] * len(xs)


# --------------- from llama index metadata to qdrant filters ----------------


def _build_filter(
    doc_ids: list[str] | None = None,
    node_ids: list[str] | None = None,
    filters: MetadataFilters | None = None,
) -> rest.Filter | None:
    conditions: list[rest.Condition] = []

    if doc_ids:
        conditions.append(
            rest.FieldCondition(key='doc_id', match=rest.MatchAny(any=doc_ids))
        )

    # Point id is a "service" id, it is not stored in payload.
    # There is 'HasId' condition to filter by point id
    # https://qdrant.tech/documentation/concepts/filtering/#has-id
    if node_ids:
        conditions.append(
            rest.HasIdCondition(has_id=node_ids),  # type: ignore
        )

    if c := _build_subfilter(filters):
        conditions.append(c)

    return rest.Filter(must=conditions) if conditions else None


def _build_subfilter(mfs: MetadataFilters | None) -> rest.Filter | None:
    if not mfs or not mfs.filters:
        return None
    nullable_conditions = [
        (
            _build_subfilter(mf)
            if isinstance(mf, MetadataFilters)
            else _meta_to_condition(mf)
        )
        for mf in mfs.filters
    ]
    conditions = [c for c in nullable_conditions if c]
    if mfs.condition is None:
        return rest.Filter()

    match mfs.condition.value:
        case 'and':
            return rest.Filter(must=conditions)
        case 'or':
            return rest.Filter(should=conditions)
        case 'not':
            return rest.Filter(must_not=conditions)
        case _ as unknown:
            raise NotImplementedError(f'Unknown FilterCondition: {unknown}')


def _meta_to_condition(f: 'MetadataFilter') -> rest.Condition | None:
    op = f.operator
    if op.name in {'LT', 'GT', 'LTE', 'GTE'}:
        return rest.FieldCondition(
            key=f.key,
            range=rest.Range(**{op.name.lower(): f.value}),  # type: ignore
        )

    # Missing value, `None` or [].
    # https://qdrant.tech/documentation/concepts/filtering/#is-empty
    if op.value == 'is_empty':
        return rest.IsEmptyCondition(is_empty=rest.PayloadField(key=f.key))

    if f.value is None:
        msg = f'Invalid filter {f}'
        raise ValueError(msg)

    values = cast(
        'list[int] | list[str]',
        f.value if isinstance(f.value, list) else [f.value],
    )

    m: rest.Match | None = None
    match op.value:
        case 'text_match' | 'text_match_insensitive':
            assert isinstance(f.value, str)
            m = rest.MatchText(text=f.value)

        case '==':
            if isinstance(f.value, float):
                return rest.FieldCondition(
                    key=f.key, range=rest.Range(gte=f.value, lte=f.value)
                )
            m = rest.MatchValue(value=f.value)  # type: ignore

        # Any of
        # https://qdrant.tech/documentation/concepts/filtering/#match-any
        case 'in':
            m = rest.MatchAny(any=values)

        # None of
        # https://qdrant.tech/documentation/concepts/filtering/#match-except
        case '!=' | 'nin':
            m = rest.MatchExcept(**{'except': values})

    if m:
        return rest.FieldCondition(key=f.key, match=m)
    return None


# ------------------------ from qdrant to llama index ------------------------


def _parse_query_results(
    points: Iterable[rest.Record | rest.ScoredPoint],
) -> '_QueryResponse':
    scored: list[tuple[BaseNode, float]] = []

    for pt in points:
        assert pt.payload is not None
        node = metadata_dict_to_node(pt.payload, with_id=pt.id)

        if node.embedding is None:
            vecs = pt.vector
            if isinstance(vecs, list):
                node.embedding = vecs  # type: ignore[assignment]
            elif isinstance(vecs, dict) and (
                isinstance(vec := vecs.get(_DENSE_NAME), list)
                or isinstance(vec := vecs.get(''), list)
            ):
                node.embedding = vec  # type: ignore[assignment]

        s = pt.score if isinstance(pt, rest.ScoredPoint) else 1.0
        scored.append((node, s))

    similarities = [s for _, s in scored]
    if any(similarities):
        logger.debug(
            'Retrieved %d nodes with score: %.3g - %.3g',
            len(similarities),
            min(similarities),
            max(similarities),
        )

    return scored

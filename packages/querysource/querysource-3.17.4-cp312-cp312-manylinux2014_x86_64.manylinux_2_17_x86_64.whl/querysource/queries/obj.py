import asyncio
from typing import Union, Optional
from aiohttp import web
from asyncdb.exceptions import (
    NoDataFound,
    StatementError,
    ConnectionTimeout
)
from ..providers import BaseProvider  # renamed to Providers.
from ..exceptions import (
    SlugNotFound,
    QueryException,
    DriverError,
    DataNotFound,
    EmptySentence
)
from .base import BaseQuery


class QueryObject(BaseQuery):
    """
    QueryObject.

    Query multiple data-origins for QuerySource.
    """
    def __init__(
            self,
            name: str,
            query: Optional[Union[list, dict]],
            conditions: dict = None,
            request: web.Request = None,
            queue: asyncio.Queue = None,
            loop: asyncio.AbstractEventLoop = None,
            **kwargs
    ):
        super(QueryObject, self).__init__(
            slug=None,
            conditions=conditions,
            request=request,
            loop=loop,
            **kwargs
        )
        ## Base provider (if slug)
        self._name = name
        self._qs: BaseProvider = None
        self._queue = queue
        self.is_cached: bool = False
        if "slug" in query:
            slug = query.pop('slug')
            self.slug = slug
            self._logger.debug(
                f'Initialize Slug: {slug!s}'
            )
            self._query = slug
            self._type = 'slug'
            # defining conditions
            self._conditions = query or {}
        elif 'query' in query:
            self._logger.debug(
                ':: Initialize Query ::'
            )
            self._query = query
            self._type = 'query'

    async def build_provider(self):
        """
        build_provider.

        create queries based on a query_slug,
        a raw query or an Object Query.
        """
        if self._type == 'slug':  # slug-based provider:
            self._logger.debug(
                f'Starting Slug-based Query: {self._query!s}'
            )
            try:
                objquery = await self.get_slug(
                    self._query,
                    evt=self._loop
                )
            except (SlugNotFound):
                raise
            except Exception:
                raise
            ### getting the connection and the provider from Slug:
            try:
                conn, provider = await self.get_provider(objquery)
            except (QueryException, DriverError) as ex:
                raise QueryException(
                    str(ex)
                ) from ex
            ### Check conditions:
            conditions = {}
            # get all information for query
            self.is_cached = objquery.is_cached
            # timeout in the cache.
            try:
                self.timeout = objquery.cache_timeout
            except (TypeError, AttributeError):
                self.timeout = 3600
            if self._conditions:
                try:
                    conditions = {**objquery.conditions, **self._conditions}
                except (AttributeError, TypeError):
                    conditions = {**self._conditions}
            elif objquery.conditions:
                conditions = {**objquery.conditions}
            # TODO: try to discovering the type of conditions
            self._logger.debug(
                f":: = SLUG {self._query}, provider: {provider!s}"
            )
            try:
                args = {
                    "slug": self._query,
                    "query": self._query,
                    "qstype": self._type,
                    "connection": conn,
                    "definition": objquery,
                    "conditions": conditions,
                    "request": self._request,
                    "loop": self._loop
                }
                self._qs = provider(**args)
                await self._qs.prepare_connection()
                return self
            except Exception as err:
                self._logger.exception(
                    f"Cannot Initialize the provider {provider}, error: {err}"
                )
                raise DriverError(
                    f"Cannot Initialize the provider {provider}, error: {err}"
                ) from err
        elif self._type == 'query':  # query raw
            try:
                self._qs = self.query_model(self._query)
            except TypeError as ex:
                return self.Error(
                    message=f'QS: Invalid query {ex}',
                    exception=ex
                )
            if datasource := self._qs.datasource:
                _, self._qs.connection = await self.datasource(datasource)
            elif driver := self._qs.driver:
                ## using a default driver:
                try:
                    _, self._qs.connection = await self.default_driver(driver)
                except (RuntimeError, QueryException) as ex:
                    return self.Error(
                        message=str(ex),
                        exception=ex
                    )
            else:
                return self.Error(
                    message=f'QS: Invalid Query Type {self._query!s}'
                )
        else:
            raise DriverError(
                f"Invalid type of Query: {self._query}"
            )

    async def query(self):
        ## TODO: adding Mapping to results (changing names)
        self.output_format('pandas')
        if self._type == 'slug':  # slug-based provider:
            if not self._qs:
                await self.build_provider()
            ## refresh = self._qs.refresh() -> TODO: add refresh feature
            self._logger.debug('= Query from PROVIDER =')
            async with self.semaphore:  # pylint: disable=E1701
                try:
                    self._logger.debug(
                        f':: Query: {self._query}'
                    )
                    result, error = await self._qs.query()
                    if error:
                        if isinstance(error, (DataNotFound, NoDataFound)):
                            raise error
                        else:
                            raise DriverError(str(error))
                    result, error = await self._output_format(result, error)  # pylint: disable=W0150
                    await self._queue.put({self._name: result})
                except (NoDataFound, DataNotFound) as err:
                    raise DataNotFound(
                        f'{self._qs.__name__!s}: {err}'
                    ) from err
                except (StatementError, EmptySentence) as err:
                    raise DriverError(
                        f"Query Error: {err}"
                    ) from err
                except Exception as ex:
                    raise self.Error(
                        "QS unhandled Exception",
                        exception=ex,
                        code=500
                    )
                finally:
                    await self._qs.close()
        elif self._type == 'query':
            async with await self._qs.connection.connection() as conn:
                try:
                    self._logger.debug(
                        f'Connected: {conn.is_connected()}'
                    )
                    result, error = await conn.query(self._qs.query)
                    if error:
                        if isinstance(error, (DataNotFound, NoDataFound)):
                            raise error
                        else:
                            raise DriverError(str(error))
                    result, error = await self._output_format(result, error)  # pylint: disable=W0150
                    await self._queue.put({self._name: result})
                except ConnectionTimeout as err:
                    raise DriverError(
                        f"Connection Timeout: {err}"
                    ) from err
                except (RuntimeError, QueryException) as ex:
                    raise QueryException(
                        f"Error on Query: {ex}"
                    )
        else:
            result = {
                "result": self._query
            }

    def __repr__(self) -> str:
        return f'<QueryObject: {self._type}:"{self._query}" >'

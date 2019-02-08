import pickle

import redis

from falcon_idempotency import SentinelException


class _BaseKlass(object):
    """Base Mixin

    A private class which adds basic fields and arguments
    which are then overriden for our two exposed Middleware
    clases.

    Parameters
    ----------
    redis_connection: redis.Redis
    force_idempotency: bool (default: False)
        If enabled, sets

    Raises
    ------
    ValueError
        If neither `redis_url` or `redis_connection` is passed

    """

    def __init__(self, redis_url=None, redis_connection=None, idempotency_ttl=3600):
        self._redis_url = redis_url
        self._redis_connection = redis_connection
        self._ttl = idempotency_ttl
        if redis_connection is None and redis_url is None:  # pragma: no cover
            raise ValueError("Expecting one of, redis_url or redis_connection")

    @property
    def idempotency_keyname(self):
        """Idempotency Keyname

        The keyname which we will look for in a given request header. This
        property can be overriden should you perfer different verbiage.

        Notes
        -----
        - The keyname is case-insensitive. This behaviour cannot be changed
        as it would violate HTTP Specification (original: RFC2616 which was
        unchanged in the superceded specifications)

        See Also
        --------
        https://www.w3.org/Protocols/rfc2616/rfc2616-sec4.html#sec4.2

        """
        return "idempotency-key"

    @property
    def redis_key(self):
        """Redis Key

        String which is used to build the redis keyname.

        Returns
        -------
        str

        """
        return "FALCON_REQUEST_{method}_{idempotency_key}"

    @property
    def redis_conn(self):
        """
        Redis connection property which can be overriden in the case where the
        developer already has a Redis connection/connection pool handy and
        would like to circumvent the method of creating the connection.

        By default, `redis-py` uses a connection pool behind the scenes.
        However, a pool is created for _every_ instantiation of Redis
        class. Should this peroperty be overriden, it may be beneficial
        to use Singleton


        Hence, ideally, the `redis_connection` that is passed upon
        instantition should be an instance of a Singleton which wraps
        said functionality. This allows for a _single_ pool.

        Returns
        -------
        redis.Redis

        See Also
        --------
        https://github.com/andymccurdy/redis-py#connection-pools

        """
        connection = getattr(self, "_redis_connection", None)
        if connection is None and self._redis_url:  # pragma: no cover
            self._redis_connection = redis.Redis.from_url(self._redis_url)
        return self._redis_connection

    def get_response_from_redis(self, idempotency_key, request):
        """Get Response from Redis

        Searches for the result that may already be stored with the given
        idempotency_key

        Parameters
        ----------
        idempotency_key: str
        request: falcon.Request

        Returns
        -------
        None
        falcon.Response
            If a response was already stored in Redis

        """
        idempotency_key = self.redis_key.format(
            idempotency_key=idempotency_key, method=request.method
        )
        data = self.redis_conn.get(idempotency_key)
        if data is not None:
            return pickle.loads(data)
        return None

    def store_response_in_redis(self, idempotency_key, request, response):
        """Store Response in Redis

        Given an indempotency_key and Falcon response object, stores the record
        in redis

        Parameters
        ----------
        idempotency_key: str
        request: falcon.Request
        response: falcon.Response
        ttl: int (default: 3600)
            Idempotency period in seconds. Defaults to 3600 seconds (1 hour)

        """
        new_idempotency_key = self.redis_key.format(
            idempotency_key=idempotency_key, method=request.method
        )
        self.redis_conn.setex(new_idempotency_key, pickle.dumps(response), self._ttl)


class SimpleIdempotencyMiddleware(_BaseKlass):
    """Simple Idempotency Middleware

    A basic implementation which assumes idempotency is applicable for the
    given POST/DELETE request so as long as the idempotency key is passed
    as part of the header.

    """

    def process_request(self, request, response):
        idempotency_key = request.get_header(self.idempotency_keyname)
        if idempotency_key:
            previous_response = self.get_response_from_redis(idempotency_key, request)
            if previous_response is not None:
                request.context[idempotency_key] = previous_response
                raise SentinelException()

    def process_response(self, request, response, resource, request_succeeded):
        idempotency_key = request.get_header(self.idempotency_keyname)
        if idempotency_key:
            self.store_response_in_redis(idempotency_key, request, response)

    def handler(self, exception, request, response, params):
        idempotency_key = request.get_header(self.idempotency_keyname)
        previous_response = request.context.pop(idempotency_key)
        for field in dir(previous_response):
            setattr(response, field, getattr(previous_response, field))


class IdempotencyMiddleware(SimpleIdempotencyMiddleware, _BaseKlass):
    """Idempotency Middleware

    An extension of `SimpleIdempotencyMiddleware` but instead allows the
    resources to dictate via idempotency is applicable using flag mixins.

    """

    def process_request(self, request, response):
        # As we need to determine if idempotency is applicable using the
        # resource, we have to defer the request processing from the parent
        # class and perform it within `process_resource`
        pass

    def process_resource(self, request, response, resource, params):
        if request.method == "POST":
            if getattr(resource, "idempotent_post", None) is True:
                return super().process_request(request, response)

        if request.method == "DELETE":
            if getattr(resource, "idempotent_delete", None) is True:
                return super().process_request(request, response)

    def process_response(self, request, response, resource, request_succeeded):
        super().process_response(request, response, resource, request_succeeded)

    def handler(self, exception, request, response, params):
        super().handler(exception, request, response, params)

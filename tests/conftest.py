import time
import uuid

import falcon
import pytest
from falcon import testing
from mockredis import MockRedis

from falcon_idempotency import SentinelException, mixins
from falcon_idempotency.middlewares import (IdempotencyMiddleware,
                                            SimpleIdempotencyMiddleware)


class MyMockRedis(MockRedis):
    """
    Applies a slight change to _always_ call `MockRedis.do_expire` prior
    to `get` call to ensure that keys are expired

    """

    def get(self, key):
        super().do_expire()
        return super().get(key)


class VanillaResource(object):
    """Mock Resource

    A mock resource which aids in testing by performing "non-idempotent"
    operations. It does so by returning the current timestamp on each request.
    We utilize this behaviour to test if we are able to intercept an incoming
    request and provide idempotency.

    """

    def on_get(self, request, response):
        response.body = "hello"

    def on_post(self, request, response):
        # Simply generate a random uuid and return it
        transaction_id = str(uuid.uuid4())
        response.set_header("trans_id", transaction_id)

    def on_delete(self, request, response):
        # Simply generate a random uuid and return it
        transaction_id = str(uuid.uuid4())
        response.set_header("trans_id", transaction_id)


class DELETEOnly(VanillaResource, mixins.IdempotentDeleteMixin):
    pass


class POSTOnly(VanillaResource, mixins.IdempotentPostMixin):
    pass


@pytest.fixture(scope="module")
def redis():
    return MyMockRedis()


@pytest.fixture()
def client(redis):
    middleware = SimpleIdempotencyMiddleware(
        redis_connection=redis, idempotency_ttl=3600
    )

    api = falcon.API(middleware=[middleware])
    api.add_route("/mock", VanillaResource())
    api.add_error_handler(SentinelException, middleware.handler)

    return testing.TestClient(api)


@pytest.fixture()
def client2(redis):
    middleware = IdempotencyMiddleware(redis_connection=redis, idempotency_ttl=3600)

    api = falcon.API(middleware=[middleware])
    api.add_route("/postonly", POSTOnly())
    api.add_route("/deleteonly", DELETEOnly())
    api.add_error_handler(SentinelException, middleware.handler)

    return testing.TestClient(api)

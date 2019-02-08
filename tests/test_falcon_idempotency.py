import falcon
import pytest
from falcon import testing


def resolve_request_method(client, request_method):
    """
        Simple utility which can be used to ease the burden of
        parametrizing for POST and DELETE metods

        Parameters
        ----------
        client: falcon.testing.TestClietn
        request_method: str
            Expecting one of: 'post', or 'delete'

        Returns
        -------
        func
            Bounded method from client

    """
    if request_method == "post":
        return client.simulate_post
    elif request_method == "delete":
        return client.simulate_delete
    else:
        raise ValueError("Invalid request_method parameter")


class TestSimpleIdempotency(object):
    """
        Test `falcon_idempotency.middlewares.SimpleIdempotencyMiddleware`

    """

    @pytest.mark.parametrize("request_method", ["delete", "post"])
    def test_inapplicable_requests(self, client, request_method):
        """
            Ensure that we do not consider requests which do not
            include valid idempotency keys
        """
        simulate_request = resolve_request_method(client, request_method)
        # Send a request with no headers at all
        first_request = simulate_request("/mock")
        second_request = simulate_request("/mock")
        first_request.headers["trans_id"] != second_request.headers["trans_id"]

        # Send a request with key set to None; these should be ignored
        first_request = simulate_request("/mock", headers={"Idempotency-Key": None})
        second_request = simulate_request("/mock", headers={"Idempotency-Key": None})
        first_request.headers["trans_id"] != second_request.headers["trans_id"]

        # Send a request with key set to ''; these should be ignored
        first_request = simulate_request("/mock", headers={"Idempotency-Key": ""})
        second_request = simulate_request("/mock", headers={"Idempotency-Key": ""})
        first_request.headers["trans_id"] != second_request.headers["trans_id"]

    @pytest.mark.parametrize("request_method", ["delete", "post"])
    def test_unrelated_requests(self, client, request_method):
        """
            Ensure that we do not couple two unique requests' responses
            if their idempotency keys do not match
        """
        simulate_request = resolve_request_method(client, request_method)
        first_request = simulate_request("/mock", headers={"Idempotency-Key": "ABCD"})
        second_request = simulate_request("/mock", headers={"Idempotency-Key": "DEFG"})
        first_request.headers["trans_id"] != second_request.headers["trans_id"]

    @pytest.mark.parametrize("request_method", ["delete", "post"])
    def test_related_requests(self, client, request_method):
        """
            Ensure we send the first response for a second request with the
            same idempotency key
        """
        simulate_request = resolve_request_method(client, request_method)
        first_request = simulate_request("/mock", headers={"Idempotency-Key": "ABCD"})
        second_request = simulate_request("/mock", headers={"Idempotency-Key": "ABCD"})
        first_request.headers["trans_id"] == second_request.headers["trans_id"]


class TestIdempotencyMiddleware(object):
    """
        Tests associated with `falcon_idempotency.middlewares.IdempotencyMiddleware`.

        Notes
        -----
        The tests are similar to that of `TestSimpleIdempotencyMiddleware`. However,
        note that the implementations of `IdempotencyMiddleware` require functionality
        to be explicitly enabled via the use of mixins/class attributes.

    """

    @pytest.mark.parametrize(
        ["endpoint", "request_method"],
        [
            ("/postonly", "post"),
            ("/postonly", "delete"),
            ("/deleteonly", "post"),
            ("/deleteonly", "delete"),
        ],
    )
    def test_inapplicable_requests(self, client2, endpoint, request_method):
        """
            Ensure that we do not consider requests which do not
            include valid idempotency keys
        """
        simulate_request = resolve_request_method(client2, request_method)
        # Send a request with no headers at all
        first_request = simulate_request("/postonly")
        second_request = simulate_request("/postonly")
        first_request.headers["trans_id"] != second_request.headers["trans_id"]

        # Send a request with key set to None; these should be ignored
        first_request = simulate_request("/postonly", headers={"Idempotency-Key": None})
        second_request = simulate_request(
            "/postonly", headers={"Idempotency-Key": None}
        )
        first_request.headers["trans_id"] != second_request.headers["trans_id"]

        # Send a request with key set to ''; these should be ignored
        first_request = simulate_request("/postonly", headers={"Idempotency-Key": ""})
        second_request = simulate_request("/postonly", headers={"Idempotency-Key": ""})
        first_request.headers["trans_id"] != second_request.headers["trans_id"]

    def test_posts_are_idempotency(self, client2):
        """
            Ensure post requests send to /postonly are idempotent
        """
        first_request = client2.simulate_post(
            "/postonly", headers={"Idempotency-Key": "ABCD"}
        )
        second_request = client2.simulate_post(
            "/postonly", headers={"Idempotency-Key": "ABCD"}
        )
        first_request.headers["trans_id"] == second_request.headers["trans_id"]

    def test_deletes_are_not_idempotent(self, client2):
        """
            Ensure that deletes are not idempotent regardless if the keys
            are identical. This is because resource associated with /postonly
            endpoint does not explicitly enable idempotent deletes
        """
        first_request = client2.simulate_delete(
            "/postonly", headers={"Idempotency-Key": "ABCD"}
        )
        second_request = client2.simulate_delete(
            "/postonly", headers={"Idempotency-Key": "ABCD"}
        )
        first_request.headers["trans_id"] != second_request.headers["trans_id"]

    def test_posts_are_not_idempotent(self, client2):
        """
            Ensure that posts are not idempotent regardless if the keys
            are identical. This is because resource associated with /deleteonly
            endpoint does not explicitly enable idempotent posts
        """
        first_request = client2.simulate_post(
            "/deleteonly", headers={"Idempotency-Key": "ABCD"}
        )
        second_request = client2.simulate_post(
            "/deleteonly", headers={"Idempotency-Key": "ABCD"}
        )
        first_request.headers["trans_id"] != second_request.headers["trans_id"]

    def test_deletes_are_idempotent(self, client2):
        """
            Ensure delete requests send to /postonly are idempotent
        """
        first_request = client2.simulate_delete(
            "/deleteonly", headers={"Idempotency-Key": "ABCD"}
        )
        second_request = client2.simulate_delete(
            "/deleteonly", headers={"Idempotency-Key": "ABCD"}
        )
        first_request.headers["trans_id"] == second_request.headers["trans_id"]

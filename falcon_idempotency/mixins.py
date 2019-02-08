class IdempotentPostMixin(object):
    """Idmepotent POST Mixin

    A Mixin class which can be added to a resource to enable
    idempotent POSTs.

    Note
    ----
    Usage of this mixin is completely optional. The implementation
    simply checks for the existence of the resource instance variable rather
    than checking MRO or something that might strictly necessitate the use
    of this mixin.

    """

    @property
    def idempotent_post(self):
        return True


class IdempotentDeleteMixin(object):
    """Idmepotent DELETE Mixin

    A Mixin class which can be added to a resource to enable
    idempotent DELETEs.

    Note
    ----
    Usage of this mixin is completely optional. The implementation
    simply checks for the existence of the resource instance variable rather
    than checking MRO or something that might strictly necessitate the use
    of this mixin.

    """

    @property
    def idempotent_delete(self):
        return True

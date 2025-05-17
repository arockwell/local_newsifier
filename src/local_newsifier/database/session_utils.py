"""Legacy session utilities removed in favor of the standard provider."""

# This module previously exposed ``get_container_session`` and
# ``with_container_session`` helpers.  These have been deleted as part of the
# migration to the ``get_session`` provider defined in
# :mod:`local_newsifier.di.providers`.  Any code that relied on the old helpers
# should import and use ``get_session`` directly.


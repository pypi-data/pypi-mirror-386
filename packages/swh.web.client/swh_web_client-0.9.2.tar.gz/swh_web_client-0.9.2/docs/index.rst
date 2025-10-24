.. _swh-web-client:

.. include:: README.rst

.. _swh-web-client-auth:

Authentication
--------------

If you have a user account registered on `Software Heritage Identity Provider`_,
it is possible to authenticate requests made to the Web APIs through the use of
an OpenID Connect bearer token. Sending authenticated requests can notably
allow to lift API rate limiting depending on your permissions.

To get this token, a dedicated CLI tool is made available when installing
``swh-web-client``:

.. code-block:: text

  $ swh auth
  Usage: swh auth [OPTIONS] COMMAND [ARGS]...

    Software Heritage Authentication tools.

    This CLI eases the retrieval of a bearer token to authenticate a user
    querying Software Heritage Web APIs.

  Options:
    --oidc-server-url TEXT  URL of OpenID Connect server (default to
                            "https://auth.softwareheritage.org/auth/")

    --realm-name TEXT       Name of the OpenID Connect authentication realm
                            (default to "SoftwareHeritage")

    --client-id TEXT        OpenID Connect client identifier in the realm
                            (default to "swh-web")

    -h, --help              Show this message and exit.

  Commands:
    generate-token  Generate a new bearer token for a Web API authentication.
    revoke-token    Revoke a bearer token used for a Web API authentication.

In order to get your tokens, you need to use the ``generate-token`` subcommand of
the CLI tool by passing your username as argument. You will be prompted
for your password and if the authentication succeeds a new OpenID Connect
offline session will be created and token will be dumped to standard output.

.. code-block:: text

  $ swh auth --client-id swh-web generate-token <username>
  Password:
  eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJmNjMzMD...

To authenticate yourself, you need to send that token value in request headers
when querying the Web API.
Considering you have stored that token value in a TOKEN environment
variable, you can perform an authenticated call the following way using ``curl``:

.. code-block:: text

  $ curl -H "Authorization: Bearer ${TOKEN}" https://archive.softwareheritage.org/api/1/<endpoint>

Note that if you intend to use the :class:`swh.web.client.client.WebAPIClient`
class, you can activate authentication by using the following code snippet::

  from swh.web.client.client import WebAPIClient

  TOKEN = '.......'  # Use "swh auth generate-token" command to get it

  client = WebAPIClient(bearer_token=TOKEN)

  # All requests to the Web API will be authenticated
  resp = client.get('swh:1:rev:aafb16d69fd30ff58afdd69036a26047f3aebdc6')

It is also possible to revoke a token, preventing future Web API authentication
when using it. The ``revoke-token`` subcommand of the CLI tool has to be used
to perform that task.

.. code-block:: text

  $ swh auth --client-id swh-web revoke-token $REFRESH_TOKEN
  Token successfully revoked.


.. only:: standalone_package_doc

   Indices and tables
   ------------------

   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`

.. _Software Heritage Identity Provider:
  https://auth.softwareheritage.org/auth/realms/SoftwareHeritage/account/

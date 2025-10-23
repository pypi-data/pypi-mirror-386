import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from tempfile import TemporaryDirectory

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from lsst.daf.butler import Butler, ButlerConfig, Config, LabeledButlerFactory
from lsst.daf.butler.remote_butler import RemoteButler
from lsst.daf.butler.remote_butler._factory import RemoteButlerFactory
from lsst.daf.butler.remote_butler.server import create_app
from lsst.daf.butler.remote_butler.server._config import ButlerServerConfig, RepositoryConfig, mock_config
from lsst.daf.butler.remote_butler.server._dependencies import (
    auth_delegated_token_dependency,
    butler_factory_dependency,
    reset_dependency_caches,
    user_name_dependency,
)
from lsst.resources import ResourcePath
from lsst.resources.s3utils import clean_test_environment_for_s3, getS3Client

from ..direct_butler import DirectButler
from .hybrid_butler import HybridButler
from .postgresql import TemporaryPostgresInstance
from .server_utils import add_auth_header_check_middleware

try:
    # moto v5
    from moto import mock_aws  # type: ignore
except ImportError:
    # moto v4 and earlier
    from moto import mock_s3 as mock_aws  # type: ignore

__all__ = ("TEST_REPOSITORY_NAME", "TestServerInstance", "create_test_server")


TEST_REPOSITORY_NAME = "testrepo"


@dataclass(frozen=True)
class TestServerInstance:
    """Butler instances and other data associated with a temporary server
    instance.
    """

    config_file_path: str
    """Path to the Butler config file used by the server."""
    client: TestClient
    """HTTPX client connected to the temporary server."""
    remote_butler: RemoteButler
    """`RemoteButler` connected to the temporary server."""
    remote_butler_without_error_propagation: RemoteButler
    """`RemoteButler` connected to the temporary server.

    By default, the TestClient instance raises any unhandled exceptions
    from the server as if they had originated in the client to ease debugging.
    However, this can make it appear that error propagation is working
    correctly when in a real deployment the server exception would cause a 500
    Internal Server Error.  This instance of the butler is set up so that any
    unhandled server exceptions do return a 500 status code."""
    direct_butler: Butler
    """`DirectButler` instance connected to the same repository as the
    temporary server.
    """
    hybrid_butler: HybridButler
    """`HybridButler` instance connected to the temporary server."""
    app: FastAPI
    """Butler server FastAPI app."""


@contextmanager
def create_test_server(
    test_directory: str,
    *,
    postgres: TemporaryPostgresInstance | None = None,
    server_config: ButlerServerConfig | None = None,
) -> Iterator[TestServerInstance]:
    """Create a temporary Butler server instance for testing.

    Parameters
    ----------
    test_directory : `str`
        Path to the ``tests/`` directory at the root of the repository,
        containing Butler test configuration files.
    postgres : `TemporaryPostgresInstance` | `None`
        If provided, the Butler server will use this postgres database
        instance.  If no postgres instance is specified, the server will use a
        a SQLite database.
    server_config : `ButlerServerConfig`, optional
        Configuration to use for the Butler server.

    Returns
    -------
    instance : `TestServerInstance`
        Object containing Butler instances connected to the server and
        associated information.
    """
    # Set up a mock S3 environment using Moto.  Moto also monkeypatches the
    # `requests` library so that any HTTP requests to presigned S3 URLs get
    # redirected to the mocked S3.
    # Note that all files are stored in memory.
    with clean_test_environment_for_s3():
        with mock_aws():
            base_config_path = os.path.join(test_directory, "config/basic/server.yaml")
            # Create S3 buckets used for the datastore in server.yaml.
            for bucket in ["mutable-bucket", "immutable-bucket"]:
                getS3Client().create_bucket(Bucket=bucket)

            config = Config(base_config_path)
            if postgres is not None:
                postgres.patch_butler_config(config)

            with TemporaryDirectory() as root, mock_config(server_config) as server_config:
                Butler.makeRepo(root, config=config, forceConfigRoot=False)
                config_file_path = os.path.join(root, "butler.yaml")

                server_config.repositories = {
                    TEST_REPOSITORY_NAME: RepositoryConfig(
                        config_uri=config_file_path, authorized_groups=["*"]
                    )
                }
                reset_dependency_caches()

                app = create_app()
                if server_config.authentication == "rubin_science_platform":
                    add_auth_header_check_middleware(app)
                _add_root_exception_handler(app)
                # Override the server's Butler initialization to point at our
                # test repo
                server_butler_factory = LabeledButlerFactory({TEST_REPOSITORY_NAME: config_file_path})
                # DirectButler has a dimension_record_cache object that
                # maintains a complete set of dimension records for governor
                # dimensions.  These values change infrequently and are needed
                # for almost every DirectButler operation, so the complete set
                # is downloaded the first time a record is needed.
                #
                # On the server it would be expensive to do this for every
                # request's new DirectButler instance, so normally these are
                # loaded once, the first time a repository is accessed.  This
                # is a problem for unit tests because they typically manipulate
                # instrument records etc during setup.  So configure the
                # factory to disable this preloading and re-fetch the records
                # as needed.
                server_butler_factory._preload_unsafe_direct_butler_caches = False
                app.dependency_overrides[butler_factory_dependency] = lambda: server_butler_factory
                # In an actual deployment, these headers would be provided by
                # the Gafaelfawr ingress.
                app.dependency_overrides[user_name_dependency] = lambda: "mock-username"
                app.dependency_overrides[auth_delegated_token_dependency] = lambda: "mock-delegated-token"

                # Using TestClient in a context manager ensures that it uses
                # the same async event loop for all requests -- otherwise it
                # starts a new one on each request.
                with TestClient(app) as client:
                    remote_butler = _make_remote_butler(client)

                    direct_butler = Butler.from_config(config_file_path, writeable=True)
                    assert isinstance(direct_butler, DirectButler)
                    hybrid_butler = HybridButler(remote_butler, direct_butler)

                    client_without_error_propagation = TestClient(app, raise_server_exceptions=False)
                    remote_butler_without_error_propagation = _make_remote_butler(
                        client_without_error_propagation
                    )

                    yield TestServerInstance(
                        config_file_path=config_file_path,
                        client=client,
                        direct_butler=direct_butler,
                        remote_butler=remote_butler,
                        remote_butler_without_error_propagation=remote_butler_without_error_propagation,
                        hybrid_butler=hybrid_butler,
                        app=app,
                    )


def _make_remote_butler(client: TestClient) -> RemoteButler:
    config_endpoint = f"https://test.example/api/butler/repo/{TEST_REPOSITORY_NAME}/butler.yaml"
    config_json = client.get(config_endpoint).read()
    config = Config(json.loads(config_json))
    config.configFile = ResourcePath(config_endpoint)
    butler_config = ButlerConfig(config)
    remote_butler_factory = RemoteButlerFactory.create_factory_from_config(butler_config, client)
    return remote_butler_factory.create_butler_for_access_token("fake-access-token")


class UnhandledServerError(Exception):
    """Raised for unhandled exceptions within the server that would result in a
    500 Internal Server Error in a real deployment.  This allows us to tell the
    difference between exceptions being propagated intentionally, and those
    just bubbling up implicitly from the server to the client.

    The FastAPI TestClient by default passes unhandled exceptions up from the
    server to the client.  This is useful behavior for unit testing because it
    gives you traceability from the test to the problem in the server code.
    However, because RemoteButler is in some ways just a proxy for the
    server-side Butler, we raise similar exceptions on the client and server
    side. Thus the default TestClient behavior can mask missing error-handling
    logic.
    """


def _add_root_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def convert_exception_types(request: Request, exc: Exception) -> None:
        raise UnhandledServerError("Unhandled server exception") from exc

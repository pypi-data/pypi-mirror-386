# Copyright 2024 Cisco Systems, Inc. and its affiliates

from __future__ import annotations

import logging
from enum import Enum
from functools import cached_property
from pathlib import Path
from time import monotonic, sleep
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse, urlunparse

from packaging.version import Version  # type: ignore
from requests import PreparedRequest, Request, Response, Session, get, head
from requests.exceptions import ConnectionError, HTTPError, RequestException

from catalystwan import USER_AGENT
from catalystwan.apigw_auth import ApiGwAuth, ApiGwLogin, LoginMode
from catalystwan.endpoints import APIEndpointClient
from catalystwan.endpoints.client import AboutInfo, ServerInfo
from catalystwan.exceptions import (
    DefaultPasswordError,
    ManagerHTTPError,
    ManagerReadyTimeout,
    ManagerRequestException,
    SessionNotCreatedError,
    TenantSubdomainNotFound,
)
from catalystwan.models.tenant import Tenant
from catalystwan.request_limiter import RequestLimiter
from catalystwan.response import ManagerResponse, response_history_debug
from catalystwan.utils.session_type import SessionType
from catalystwan.version import NullVersion, parse_api_version
from catalystwan.vmanage_auth import create_vmanage_auth, vManageAuth

JSON = Union[Dict[str, "JSON"], List["JSON"], str, int, float, bool, None]

if TYPE_CHECKING:
    from catalystwan.api.api_container import APIContainer
    from catalystwan.endpoints.endpoints_container import APIEndpointContainter


class UserMode(str, Enum):
    PROVIDER = "provider"
    TENANT = "tenant"


class ViewMode(str, Enum):
    PROVIDER = "provider"
    TENANT = "tenant"


class TenancyMode(str, Enum):
    SINGLE_TENANT = "SingleTenant"
    MULTI_TENANT = "MultiTenant"


class ManagerSessionState(Enum):
    # there are some similiarities to state-machine but flow is only in one direction
    # and does not depend on external inputs
    RESTART_IMMINENT = 0
    WAIT_SERVER_READY_AFTER_RESTART = 1
    LOGIN = 2
    OPERATIVE = 3
    LOGIN_IN_PROGRESS = 4
    AUTH_SYNC = 5


def determine_session_type(
    tenancy_mode: Optional[str], user_mode: Optional[str], view_mode: Optional[str]
) -> SessionType:
    modes_map = {
        (TenancyMode.SINGLE_TENANT, UserMode.TENANT, ViewMode.TENANT): SessionType.SINGLE_TENANT,
        (TenancyMode.MULTI_TENANT, UserMode.PROVIDER, ViewMode.PROVIDER): SessionType.PROVIDER,
        (TenancyMode.MULTI_TENANT, UserMode.PROVIDER, ViewMode.TENANT): SessionType.PROVIDER_AS_TENANT,
        (TenancyMode.MULTI_TENANT, UserMode.TENANT, ViewMode.TENANT): SessionType.TENANT,
    }
    try:
        return modes_map.get(
            (TenancyMode(tenancy_mode), UserMode(user_mode), ViewMode(view_mode)), SessionType.NOT_DEFINED
        )
    except ValueError:
        return SessionType.NOT_DEFINED


def create_base_url(url: str, port: Optional[int] = None) -> str:
    """Creates base url based on ip address or domain and port if provided.

    Returns:
        str: Base url shared for every request.
    """
    parsed_url = urlparse(url)
    netloc: str = parsed_url.netloc or parsed_url.path
    scheme: str = parsed_url.scheme or "https"
    base_url = urlunparse((scheme, netloc, "", None, None, None))
    if port:
        return f"{base_url}:{port}"  # noqa: E231
    return base_url


def create_apigw_session(
    url: str,
    client_id: str,
    client_secret: str,
    org_name: str,
    subdomain: Optional[str] = None,
    port: Optional[int] = None,
    mode: Optional[LoginMode] = None,
    username: Optional[str] = None,
    session: Optional[str] = None,
    tenant_user: Optional[bool] = None,
    token_duration: int = 10,
    logger: Optional[logging.Logger] = None,
) -> ManagerSession:
    """Factory method that creates session object and performs login according to parameters

    Args:
        url (str): IP address or domain name
        client_id (str): client id
        client_secret (str): client secret
        org_name (str): organization name
        subdomain: subdomain specifying to which view switch when creating provider as a tenant session,
            works only on provider user mode
        port (int): port
        mode (LoginMode): login mode
        username (str): username
        session (str): session
        tenant_user (bool): tenant user
        token_duration (int): token duration
        logger: override default module logger

    Returns:
        ManagerSession: logged-in and operative session to perform tasks on SDWAN Manager.
    """
    auth = ApiGwAuth(
        login=ApiGwLogin(
            client_id=client_id,
            client_secret=client_secret,
            org_name=org_name,
            mode=mode,
            username=username,
            session=session,
            tenant_user=tenant_user,
            token_duration=token_duration,
        ),
        logger=logger,
    )
    session_ = ManagerSession(base_url=create_base_url(url, port), auth=auth, subdomain=subdomain, logger=logger)
    session_.state = ManagerSessionState.LOGIN
    return session_


def create_manager_session(
    url: str,
    username: str,
    password: str,
    port: Optional[int] = None,
    subdomain: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> ManagerSession:
    """Factory method that creates session object and performs login according to parameters

    Args:
        url (str): IP address or domain name
        username (str): username
        password (str): password
        port (int): port
        subdomain: subdomain specifying to which view switch when creating provider as a tenant session,
            works only on provider user mode
        logger: override default module logger

    Returns:
        ManagerSession: logged-in and operative session to perform tasks on SDWAN Manager.
    """
    auth = create_vmanage_auth(username, password, subdomain, logger)
    session = ManagerSession(
        base_url=create_base_url(url, port),
        auth=auth,
        subdomain=subdomain,
        logger=logger,
    )
    session.state = ManagerSessionState.LOGIN
    return session


class ManagerResponseAdapter(Session):
    def request(self, method, url, *args, **kwargs) -> ManagerResponse:
        return ManagerResponse(super().request(method, url, *args, **kwargs))

    def get(self, url, *args, **kwargs) -> ManagerResponse:
        return ManagerResponse(super().get(url, *args, **kwargs))

    def post(self, url, *args, **kwargs) -> ManagerResponse:
        return ManagerResponse(super().post(url, *args, **kwargs))

    def put(self, url, *args, **kwargs) -> ManagerResponse:
        return ManagerResponse(super().put(url, *args, **kwargs))

    def delete(self, url, *args, **kwargs) -> ManagerResponse:
        return ManagerResponse(super().delete(url, *args, **kwargs))


class ManagerSession(ManagerResponseAdapter, APIEndpointClient):
    """Base class for API sessions for vManage client.

    Defines methods and handles session connectivity available for provider, provider as tenant, and tenant.

    Args:
        base_url: IP address or domain name, i.e. '10.0.1.200' or 'example.com'
        auth: authentication object - vManage or API Gateway
        subdomain: subdomain specifying to which view switch when creating provider as a tenant session,
            works only on provider user mode
        logger: override default module logger

    Attributes:
        api: APIContainer: container for API methods
        endpoints: APIEndpointContainter: container for API endpoints
        state: ManagerSessionState: current state of the session can be used to control session flow
        response_trace: Callable: function that logs response and request details
        server_name: str: server name
        platform_version: str: platform version
        api_version: Version: API version
        restart_timeout: int: restart timeout in seconds
        session_type: SessionType: type of session
        verify: bool: verify SSL certificate

    """

    def __init__(
        self,
        base_url: str,
        auth: Union[vManageAuth, ApiGwAuth],
        subdomain: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        request_limiter: Optional[RequestLimiter] = None,
    ) -> None:
        self.base_url = base_url
        self.subdomain = subdomain
        self._session_type = SessionType.NOT_DEFINED
        self.server_name: Optional[str] = None
        self.logger = logger or logging.getLogger(__name__)
        self.response_trace: Callable[
            [Optional[Response], Union[Request, PreparedRequest, None]], str
        ] = response_history_debug
        super(ManagerSession, self).__init__()
        self.verify = False
        self.headers.update({"User-Agent": USER_AGENT})
        self._added_to_auth = False
        self._auth = auth
        self._platform_version: str = ""
        self._api_version: Version = NullVersion  # type: ignore
        self.restart_timeout: int = 1200
        self.polling_requests_timeout: int = 10
        self.request_timeout: Optional[int] = None
        self._validate_responses = True
        self._state: ManagerSessionState = ManagerSessionState.OPERATIVE
        self._last_request: Optional[PreparedRequest] = None
        self._limiter: RequestLimiter = request_limiter or RequestLimiter()

    @cached_property
    def api(self) -> APIContainer:
        from catalystwan.api.api_container import APIContainer

        self._api = APIContainer(self)
        return self._api

    @cached_property
    def endpoints(self) -> APIEndpointContainter:
        from catalystwan.endpoints.endpoints_container import APIEndpointContainter

        self._endpoints = APIEndpointContainter(self)
        return self._endpoints

    @property
    def state(self) -> ManagerSessionState:
        return self._state

    @state.setter
    def state(self, state: ManagerSessionState) -> None:
        """Resets the session to given state and manages transition to desired OPERATIONAL state"""
        self._state = state
        self.logger.debug(f"Session entered state: {self.state.name}")

        if state == ManagerSessionState.OPERATIVE:
            # this is desired state, nothing to be done
            return
        elif state == ManagerSessionState.RESTART_IMMINENT:
            # in this state we process requests normally
            # but when ConnectionError is caught we enter WAIT_SERVER_READY_AFTER_RESTART
            # state change is achieved with cooperation with request method
            return
        elif state == ManagerSessionState.WAIT_SERVER_READY_AFTER_RESTART:
            self.wait_server_ready(self.restart_timeout)
            self.state = ManagerSessionState.LOGIN
        elif state == ManagerSessionState.LOGIN:
            self.state = ManagerSessionState.LOGIN_IN_PROGRESS
            self._sync_auth()
            server_info = self._fetch_server_info()
            self._finalize_login(server_info)
            self.state = ManagerSessionState.OPERATIVE
        elif state == ManagerSessionState.LOGIN_IN_PROGRESS:
            # nothing to be done, continue to login
            return
        elif state == ManagerSessionState.AUTH_SYNC:
            # this state can be reached when using an expired auth during the login (most likely
            # to happen when multithreading). To avoid fetching server info multiple times, we will
            # only authenticate here and then return to the previous login flow
            self._sync_auth()
            self.state = ManagerSessionState.LOGIN_IN_PROGRESS
        return

    def restart_imminent(self, restart_timeout_override: Optional[int] = None):
        """Notify session that restart is imminent.
        ConnectionError and status code 503 will cause session to wait for connectivity and perform login again

        Args:
            restart_timeout_override (Optional[int], optional): override session property which controls restart timeout
        """
        if restart_timeout_override is not None:
            self.restart_timeout = restart_timeout_override
        self.state = ManagerSessionState.RESTART_IMMINENT

    def _sync_auth(self) -> None:
        self.cookies.clear_session_cookies()
        if not self._added_to_auth:
            self._auth.increase_session_count()
            self._added_to_auth = True
        self._auth.clear(self._last_request)
        self.auth = self._auth

    def _fetch_server_info(self) -> ServerInfo:
        try:
            server_info = self.server()
        except DefaultPasswordError:
            server_info = ServerInfo.model_construct(**{})

        return server_info

    def _finalize_login(self, server_info: ServerInfo) -> None:
        self.server_name = server_info.server

        tenancy_mode = server_info.tenancy_mode
        user_mode = server_info.user_mode
        view_mode = server_info.view_mode

        self._session_type = determine_session_type(tenancy_mode, user_mode, view_mode)

        if user_mode is UserMode.TENANT and self.subdomain:
            raise SessionNotCreatedError(
                f"Session not created. Subdomain {self.subdomain} passed to tenant session, "
                "cannot switch to tenant from tenant user mode."
            )
        elif self._session_type is SessionType.NOT_DEFINED:
            self.logger.warning(
                "Cannot determine session type for "
                f"tenancy-mode: {tenancy_mode}, user-mode: {user_mode}, view-mode: {view_mode}"
            )

        self.logger.info(
            f"Logged to vManage({self.platform_version}) as {self.auth}. The session type is {self.session_type}"
        )

    def login(self) -> ManagerSession:
        """Performs login to SDWAN Manager and fetches important server info to instance variables

        Raises:
            SessionNotCreatedError: indicates session configuration is not consistent

        Returns:
            ManagerSession: (self)
        """
        self.state = ManagerSessionState.LOGIN
        return self

    def wait_server_ready(self, timeout: int, poll_period: int = 10) -> None:
        """Waits until server is ready for API requests with given timeout in seconds"""

        begin = monotonic()
        self.logger.info(f"Waiting for server ready with timeout {timeout} seconds.")

        def elapsed() -> float:
            return monotonic() - begin

        # wait for http available
        while elapsed() < timeout:
            available = False
            try:
                resp = head(
                    self.base_url,
                    timeout=self.polling_requests_timeout,
                    verify=self.verify,
                    headers={"User-Agent": USER_AGENT},
                )
                self.logger.debug(self.response_trace(resp, None))
                if resp.status_code != 503:
                    available = True
            except ConnectionError as error:
                self.logger.debug(self.response_trace(error.response, error.request))
            if not available:
                sleep(poll_period)
                continue
            break

        # wait server ready flag
        server_ready_url = self.get_full_url("/dataservice/client/server/ready")
        while elapsed() < timeout:
            try:
                resp = get(
                    server_ready_url,
                    timeout=self.polling_requests_timeout,
                    verify=self.verify,
                    headers={"User-Agent": USER_AGENT},
                )
                self.logger.debug(self.response_trace(resp, None))
                if resp.status_code == 200:
                    if resp.json().get("isServerReady") is True:
                        self.logger.debug(f"Waiting for server ready took: {elapsed()} seconds.")
                        return
                sleep(poll_period)
                continue
            except RequestException as exception:
                self.logger.debug(self.response_trace(exception.response, exception.request))
                raise ManagerRequestException(*exception.args)

        raise ManagerReadyTimeout(f"Waiting for server ready took longer than {timeout} seconds.")

    def request(self, method, url, *args, **kwargs) -> ManagerResponse:
        full_url = self.get_full_url(url)
        _kwargs = dict(kwargs)
        if self.request_timeout is not None:  # do not modify user provided kwargs unless property is set
            _kwargs.update(timeout=self.request_timeout)
        try:
            with self._limiter:
                response = super(ManagerSession, self).request(method, full_url, *args, **_kwargs)
            self.logger.debug(self.response_trace(response, None))
            if self.state == ManagerSessionState.RESTART_IMMINENT and response.status_code == 503:
                self.state = ManagerSessionState.WAIT_SERVER_READY_AFTER_RESTART
        except RequestException as exception:
            self.logger.debug(self.response_trace(exception.response, exception.request))
            if self.state == ManagerSessionState.RESTART_IMMINENT and isinstance(exception, ConnectionError):
                self.state = ManagerSessionState.WAIT_SERVER_READY_AFTER_RESTART
                return self.request(method, url, *args, **_kwargs)
            self.logger.debug(exception)
            raise ManagerRequestException(*exception.args, request=exception.request, response=exception.response)

        self._last_request = response.request
        if response.jsessionid_expired and self.state in [
            ManagerSessionState.OPERATIVE,
            ManagerSessionState.LOGIN_IN_PROGRESS,
        ]:
            # detected expired auth during login, resync
            if self.state == ManagerSessionState.LOGIN_IN_PROGRESS:
                self.state = ManagerSessionState.AUTH_SYNC
            else:
                self.logger.warning("Logging to session. Reason: expired JSESSIONID detected in response headers")
                self.state = ManagerSessionState.LOGIN
            return self.request(method, url, *args, **_kwargs)

        if response.api_gw_unauthorized and self.state in [
            ManagerSessionState.OPERATIVE,
            ManagerSessionState.LOGIN_IN_PROGRESS,
        ]:
            # detected expired auth during login, resync
            if self.state == ManagerSessionState.LOGIN_IN_PROGRESS:
                self.state = ManagerSessionState.AUTH_SYNC
            else:
                self.logger.warning("Logging to API GW session. Reason: token is expired")
                self.state = ManagerSessionState.LOGIN
            return self.request(method, url, *args, **_kwargs)

        if response.request.url and "passwordReset.html" in response.request.url:
            raise DefaultPasswordError("Password must be changed to use this session.")

        try:
            response.raise_for_status()
        except HTTPError as error:
            self.logger.debug(error)
            error_info = response.get_error_info()
            raise ManagerHTTPError(*error.args, error_info=error_info, request=error.request, response=error.response)
        return response

    def get_full_url(self, url_path: str) -> str:
        """Returns base API url plus given url path."""
        return urljoin(self.base_url, url_path)

    def about(self) -> AboutInfo:
        return self.endpoints.client.about()

    def server(self) -> ServerInfo:
        server_info = self.endpoints.client.server()
        self.platform_version = server_info.platform_version
        return server_info

    def get_data(self, url: str) -> Any:
        return self.get_json(url)["data"]

    def get_json(self, url: str) -> Any:
        response = self.get(url)
        return response.json()

    def get_file(self, url: str, filename: Path) -> Response:
        """Get a file using session get.

        Args:
            url: dataservice api.
            filename: Filename to write download file to.

        Returns:
            http response.

        Example usage:
            response = self.session.get_file(url, filename)

        """
        with self.get(url) as response:
            with open(filename, "wb") as file:
                file.write(response.content)
        return response

    def get_tenant_id(self) -> str:
        """Gets tenant UUID for its subdomain.

        Returns:
            Tenant UUID.
        """
        tenants = self.get("dataservice/tenant").dataseq(Tenant)
        tenant = tenants.filter(subdomain=self.subdomain).single_or_default()

        if not tenant or not tenant.tenant_id:
            raise TenantSubdomainNotFound(f"Tenant ID for sub-domain: {self.subdomain} not found")

        return tenant.tenant_id

    def logout(self) -> None:
        if self._added_to_auth:
            self._auth.decrease_session_count()
        self._auth.logout(self)

    def close(self) -> None:
        """Closes the ManagerSession.

        This method is overrided from requests.Session.
        Firstly it cleans up any resources associated with vManage.
        Then it closes all adapters and as such the session.

        Note: It is generally recommended to use the session as a context manager
        using the `with` statement, which ensures that the session is properly
        closed and resources are cleaned up even in case of exceptions.
        """
        self.logout()
        super().close()

    @property
    def session_type(self) -> SessionType:
        return self._session_type

    @property
    def platform_version(self) -> str:
        return self._platform_version

    @platform_version.setter
    def platform_version(self, version: str):
        self._platform_version = version
        self._api_version = parse_api_version(version)

    @property
    def api_version(self) -> Version:
        return self._api_version

    @property
    def validate_responses(self) -> bool:
        return self._validate_responses

    @validate_responses.setter
    def validate_responses(self, value: bool):
        self._validate_responses = value

    def __copy__(self) -> ManagerSession:
        return ManagerSession(
            base_url=self.base_url,
            auth=self._auth,
            subdomain=self.subdomain,
            logger=self.logger,
            request_limiter=self._limiter,
        )

    def __str__(self) -> str:
        return f"ManagerSession(session_type={self.session_type}, auth={self._auth})"

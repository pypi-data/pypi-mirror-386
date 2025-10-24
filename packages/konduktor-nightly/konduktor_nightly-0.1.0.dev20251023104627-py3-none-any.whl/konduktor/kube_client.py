import logging
import os
from typing import Any, Callable, List, Optional

import kubernetes
import urllib3

from konduktor import config
from konduktor import logging as konduktor_logging
from konduktor.utils import annotations, ux_utils

logger = konduktor_logging.get_logger(__name__)

# Timeout to use for API calls
API_TIMEOUT = 5
DEFAULT_NAMESPACE = 'default'
DEFAULT_IN_CLUSTER_REGION = 'in-cluster'
# The name for the environment variable that stores the in-cluster context name
# for Kubernetes clusters. This is used to associate a name with the current
# context when running with in-cluster auth. If not set, the context name is
# set to DEFAULT_IN_CLUSTER_REGION.
IN_CLUSTER_CONTEXT_NAME_ENV_VAR = 'KONDUKTOR_IN_CLUSTER_CONTEXT_NAME'

# Tracks the most recently selected/loaded context name.
# None means no explicit context was resolved/loaded yet.
_ACTIVE_CONTEXT: Optional[str] = None


def _decorate_methods(obj: Any, decorator: Callable, decoration_type: str):
    for attr_name in dir(obj):
        attr = getattr(obj, attr_name)
        # Skip methods starting with '__' since they are invoked through one
        # of the main methods, which are already decorated.
        if callable(attr) and not attr_name.startswith('__'):
            continue
    return obj


def _api_logging_decorator(logger: str, level: int):
    """Decorator to set logging level for API calls.

    This is used to suppress the verbose logging from urllib3 when calls to the
    Kubernetes API timeout.
    """

    def decorated_api(api):
        def wrapped(*args, **kwargs):
            obj = api(*args, **kwargs)
            _decorate_methods(
                obj, konduktor_logging.set_logging_level(logger, level), 'api_log'
            )
            return obj

        return wrapped

    return decorated_api


def _load_config(context: Optional[str] = None):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # If no context explicitly provided, prefer the configured allowed context
    # (first element) when present. This ensures the client defaults to the
    # user-specified context instead of kubeconfig's current-context.
    effective_context = context
    allowed_contexts: List[str] = config.get_nested(
        ('kubernetes', 'allowed_contexts'), []
    )

    is_allowed_selected = False
    if effective_context is None and allowed_contexts:
        effective_context = allowed_contexts[0]
        is_allowed_selected = True
        logger.info(
            'Detected kubernetes.allowed_contexts in config; using context: %s',
            effective_context,
        )

    def _load_config_from_kubeconfig(context: Optional[str] = None):
        try:
            kubernetes.config.load_kube_config(context=context)
        except kubernetes.config.config_exception.ConfigException as e:
            # Improve error when a configured allowed context cannot be loaded
            msg = str(e)
            if is_allowed_selected and context is not None:
                err_str = (
                    'Configured Kubernetes context not usable: '
                    f'kubernetes.allowed_contexts[0] = {context!r}. '
                    'Please ensure this context exists and is valid in your '
                    'kubeconfig (typically at ~/.kube/config).'
                )
            elif 'Expected key current-context' in msg:
                err_str = (
                    f'Failed to load Kubernetes configuration for {context!r}. '
                    'Kubeconfig does not contain any valid context(s).\n'
                )
            else:
                err_str = (
                    f'Failed to load Kubernetes configuration for {context!r}. '
                    'Please check if your kubeconfig file exists at '
                    f'~/.kube/config and is valid.'
                )
            with ux_utils.print_exception_no_traceback():
                raise ValueError(err_str) from None

    global _ACTIVE_CONTEXT
    if effective_context == in_cluster_context_name() or effective_context is None:
        try:
            # Load in-cluster config if running in a pod and context is None.
            # Kubernetes set environment variables for service discovery do not
            # show up in SkyPilot tasks. For now, we work around by using
            # DNS name instead of environment variables.
            # See issue: https://github.com/skypilot-org/skypilot/issues/2287
            os.environ['KUBERNETES_SERVICE_HOST'] = 'kubernetes.default.svc'
            os.environ['KUBERNETES_SERVICE_PORT'] = '443'
            kubernetes.config.load_incluster_config()
            _ACTIVE_CONTEXT = in_cluster_context_name()
        except kubernetes.config.config_exception.ConfigException:
            # If allowed_contexts was specified, do not fall back silently.
            if is_allowed_selected:
                _load_config_from_kubeconfig(effective_context)
            else:
                _load_config_from_kubeconfig()
            # Best effort: set active context to current-context from kubeconfig
            try:
                _, current_ctx = kubernetes.config.list_kube_config_contexts()
                _ACTIVE_CONTEXT = current_ctx.get('name') if current_ctx else None
            except kubernetes.config.config_exception.ConfigException:
                _ACTIVE_CONTEXT = None
    else:
        _load_config_from_kubeconfig(effective_context)
        _ACTIVE_CONTEXT = effective_context


@_api_logging_decorator('urllib3', logging.ERROR)
@annotations.lru_cache(scope='request')
def core_api(context: Optional[str] = None):
    _load_config(context)
    return kubernetes.client.CoreV1Api()


@_api_logging_decorator('urllib3', logging.ERROR)
@annotations.lru_cache(scope='request')
def auth_api(context: Optional[str] = None):
    _load_config(context)
    return kubernetes.client.RbacAuthorizationV1Api()


@_api_logging_decorator('urllib3', logging.ERROR)
@annotations.lru_cache(scope='request')
def networking_api(context: Optional[str] = None):
    _load_config(context)
    return kubernetes.client.NetworkingV1Api()


@_api_logging_decorator('urllib3', logging.ERROR)
@annotations.lru_cache(scope='request')
def crd_api(context: Optional[str] = None):
    _load_config(context)
    return kubernetes.client.CustomObjectsApi()


@_api_logging_decorator('urllib3', logging.ERROR)
@annotations.lru_cache(scope='request')
def node_api(context: Optional[str] = None):
    _load_config(context)
    return kubernetes.client.NodeV1Api()


@_api_logging_decorator('urllib3', logging.ERROR)
@annotations.lru_cache(scope='request')
def apps_api(context: Optional[str] = None):
    _load_config(context)
    return kubernetes.client.AppsV1Api()


@_api_logging_decorator('urllib3', logging.ERROR)
@annotations.lru_cache(scope='request')
def api_client(context: Optional[str] = None):
    _load_config(context)
    return kubernetes.client.ApiClient()


@_api_logging_decorator('urllib3', logging.ERROR)
@annotations.lru_cache(scope='request')
def batch_api(context: Optional[str] = None):
    _load_config(context)
    return kubernetes.client.BatchV1Api()


@_api_logging_decorator('urllib3', logging.ERROR)
@annotations.lru_cache(scope='request')
def crd_client(context: Optional[str] = None):
    _load_config(context)
    return kubernetes.client.CustomObjectsApi()


@_api_logging_decorator('urllib3', logging.ERROR)
@annotations.lru_cache(scope='request')
def autoscaling_api(context: Optional[str] = None):
    """Return the Kubernetes AutoscalingV2Api client."""
    _load_config(context)
    return kubernetes.client.AutoscalingV2Api()


def api_exception():
    return kubernetes.client.rest.ApiException


def config_exception():
    return kubernetes.config.config_exception.ConfigException


def max_retry_error():
    return urllib3.exceptions.MaxRetryError


def stream():
    return kubernetes.stream.stream


def in_cluster_context_name() -> Optional[str]:
    """Returns the name of the in-cluster context from the environment.

    If the environment variable is not set, returns the default in-cluster
    context name.
    """
    return os.environ.get(IN_CLUSTER_CONTEXT_NAME_ENV_VAR) or DEFAULT_IN_CLUSTER_REGION


def get_active_context() -> Optional[str]:
    """Returns the last context selected by the client loader.

    This reflects the effective context used by the most recent client init.
    May be None if no client has been initialized yet.
    """
    return _ACTIVE_CONTEXT

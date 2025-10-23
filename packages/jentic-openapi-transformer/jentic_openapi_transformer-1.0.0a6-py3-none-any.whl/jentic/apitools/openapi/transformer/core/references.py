from typing import Any, Iterator, List, MutableMapping, Tuple, cast
from urllib.parse import urljoin, urlparse

from jentic.apitools.openapi.traverse.json import JSONPath, traverse


# TODO(vladimir@jentic.com): this needs to be refactored when we have OpenAPI datamodel available

__all__ = [
    "find_relative_urls",
    "find_absolute_http_urls",
    "RewriteOptions",
    "rewrite_urls_inplace",
    "iter_url_fields",
]


def find_relative_urls(root: Any) -> List[Tuple[JSONPath, str, str]]:
    """
    Return a list of (json_path, key, value) for any URL-like field
    (including $ref) whose value is relative (e.g., 'schemas/a.yaml', '../b', '/c')
    and not a pure fragment '#/...' .
    """
    out: List[Tuple[JSONPath, str, str]] = []
    for path, _parent, key, value in iter_url_fields(root):
        assert isinstance(key, str)
        if key == "$ref" and _is_fragment_only(value):
            continue
        if _is_relative_like(value):
            new_path = cast(JSONPath, (*path, key))
            out.append((new_path, key, value))
    return out


def find_absolute_http_urls(root: Any) -> List[Tuple[JSONPath, str, str]]:
    """
    Return a list of (json_path, key, value) for any URL-like field
    (including $ref) whose value is absolute and http
    """
    out: List[Tuple[JSONPath, str, str]] = []
    for path, _parent, key, value in iter_url_fields(root):
        assert isinstance(key, str)
        if key == "$ref" and _is_fragment_only(value):
            continue
        if not _is_relative_like(value) and _is_absolute_http_uri(value):
            new_path = cast(JSONPath, (*path, key))
            out.append((new_path, key, value))
    return out


class RewriteOptions:
    """
    Options for rewrite_urls_inplace.
    - base_url:           New base for *relative* refs/URLs.
    - original_base_url:  If provided together with include_absolute_urls=True, we'll
                          retarget absolute URLs that begin with original_base_url to base_url.
    - include_absolute_urls: If True (and original_base_url given), retarget absolute URLs too.
    """

    __slots__ = ("base_url", "original_base_url", "include_absolute_urls")

    def __init__(
        self,
        base_url: str,
        original_base_url: str | None = None,
        include_absolute_urls: bool = False,
    ) -> None:
        self.base_url = base_url
        self.original_base_url = original_base_url
        self.include_absolute_urls = include_absolute_urls


def rewrite_urls_inplace(root: Any, opts: RewriteOptions) -> int:
    """
    Rewrite $ref and other URL-bearing fields in-place.
    Rules:
    - Relative values (except fragment-only) are absolutized against opts.base_url.
    - If opts.include_absolute_urls and opts.original_base_url are set,
      then any absolute URL beginning with original_base_url gets retargeted
      to opts.base_url (prefix replacement).
    Returns the number of fields changed.
    """
    changed = 0
    for _path, parent, key, value in iter_url_fields(root):
        # value is str by iter_url_fields contract
        if key == "$ref" and _is_fragment_only(value):
            continue  # keep pure fragments

        new_value = value
        if _is_relative_like(value):
            new_value = _absolutize(value, opts.base_url)
        elif opts.include_absolute_urls and opts.original_base_url and _is_absolute_uri(value):
            new_value = _retarget_absolute(value, opts.original_base_url, opts.base_url)

        if new_value != value:
            parent[key] = new_value  # parent is a mapping; key is str
            changed += 1

    return changed


def iter_url_fields(root: Any) -> Iterator[Tuple[JSONPath, MutableMapping[str, Any], str, str]]:
    """
    Iterate over all places that likely carry URL/URI/Reference strings,
    including $ref and common OpenAPI URL-bearing keys.
    """
    for node in traverse(root):
        if (
            isinstance(node.parent, MutableMapping)
            and isinstance(node.segment, str)
            and isinstance(node.value, str)
            and node.segment in _URL_KEYS_EXPLICIT
        ):
            yield node.path, node.parent, node.segment, node.value


# Keys that *by spec* or convention carry URL/URI references (OpenAPI 3.0/3.1).
_URL_KEYS_EXPLICIT: frozenset[str] = frozenset(
    {
        # JSON Reference
        "$ref",
        # JSON Schema / examples / links
        "externalValue",
        "operationRef",
        # Info/Contact/License
        "termsOfService",
        "url",  # Contact.url, License.url, ExternalDocs.url, Server.url, etc.
        # OAuth/OpenID
        "authorizationUrl",
        "tokenUrl",
        "refreshUrl",
        "openIdConnectUrl",
        # Server Variable namespace can influence URLs, but we avoid touching variables.*.default
        # Add more as needed (e.g., "namespace" in XML Object).
    }
)


def _is_fragment_only(s: str) -> bool:
    return s.startswith("#")


def _is_scheme_relative(s: str) -> bool:
    # e.g. //cdn.example.com/x.yaml   (no scheme, but host present)
    return s.startswith("//")


def _is_absolute_uri(s: str) -> bool:
    if _is_scheme_relative(s):
        return True
    p = urlparse(s)
    return bool(p.scheme)


def _is_absolute_http_uri(s: str) -> bool:
    if _is_scheme_relative(s):
        return False
    p = urlparse(s)
    return bool(p.scheme) and p.scheme in ("http", "https")


def _looks_like_uri(s: str) -> bool:
    # Heuristic: treat strings with ':' before any slash as potentially absolute
    # but we also want to catch relative paths like './x', '../x', 'a/b', '/a'
    # We'll consider *any* non-empty string that isn't pure fragment as a URI candidate,
    # and then rely on absolute/relative checks above.
    return isinstance(s, str) and s != "" and not s.isspace()


def _has_prefix(url: str, base: str) -> bool:
    # Normalize both and compare prefix; use straightforward string prefix
    # because urljoin/urlparse can recompose differently. Assumes base ends
    # at a directory or resource boundary that you control.
    return url.startswith(base)


def _retarget_absolute(url: str, original_base_url: str, new_base_url: str) -> str:
    """If url starts with original_base_url, replace with new_base_url."""
    if _has_prefix(url, original_base_url):
        return new_base_url + url[len(original_base_url) :]
    return url


def _absolutize(url: str, base_url: str) -> str:
    """Make a relative URL absolute against base_url."""
    return urljoin(base_url, url)


def _is_relative_like(s: str) -> bool:
    """Relative (incl. root-relative '/x') and not fragment-only or scheme-relative."""
    if not _looks_like_uri(s):
        return False
    if _is_fragment_only(s) or _is_scheme_relative(s) or _is_absolute_uri(s):
        return False
    # At this point treat anything else as relative: './x', '../x', 'x', 'x/y', '/x'
    return True

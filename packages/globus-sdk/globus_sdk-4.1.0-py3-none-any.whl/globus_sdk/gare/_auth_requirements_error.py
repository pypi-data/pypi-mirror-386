from __future__ import annotations

import typing as t

from globus_sdk._internal.guards import validators
from globus_sdk._internal.serializable import Serializable


class GlobusAuthorizationParameters(Serializable):
    """
    Data class containing authorization parameters that can be passed during
    an authentication flow to control how the user will authenticate.

    When used with a GARE this represents the additional authorization
    parameters needed in order to complete a request that had insufficient
    authorization state.

    :ivar session_message: A message to be displayed to the user.
    :vartype session_message: str, optional

    :ivar session_required_identities: A list of identities required for the
        session.
    :vartype session_required_identities: list of str, optional

    :ivar session_required_policies: A list of policies required for the
        session.
    :vartype session_required_policies: list of str, optional

    :ivar session_required_single_domain: A list of domains required for the
        session.
    :vartype session_required_single_domain: list of str, optional

    :ivar session_required_mfa: Whether MFA is required for the session.
    :vartype session_required_mfa: bool, optional

    :ivar required_scopes: A list of scopes for which consent is required.
    :vartype required_scopes: list of str, optional

    :ivar prompt: The OIDC 'prompt' parameter, for which Globus Auth currently supports
        the values 'login' and 'none'.
    :vartype prompt: str, optional

    :ivar extra: A dictionary of additional fields that were provided. May
        be used for forward/backward compatibility.
    :vartype extra: dict
    """

    def __init__(
        self,
        *,
        session_message: str | None = None,
        session_required_identities: list[str] | None = None,
        session_required_policies: list[str] | None = None,
        session_required_single_domain: list[str] | None = None,
        session_required_mfa: bool | None = None,
        required_scopes: list[str] | None = None,
        prompt: str | None = None,
        extra: dict[str, t.Any] | None = None,
    ) -> None:
        self.session_message = validators.opt_str("session_message", session_message)
        self.session_required_identities = validators.opt_str_list(
            "session_required_identities", session_required_identities
        )
        self.session_required_policies = validators.opt_str_list(
            "session_required_policies", session_required_policies
        )
        self.session_required_single_domain = validators.opt_str_list(
            "session_required_single_domain", session_required_single_domain
        )
        self.session_required_mfa = validators.opt_bool(
            "session_required_mfa", session_required_mfa
        )
        self.required_scopes = validators.opt_str_list(
            "required_scopes", required_scopes
        )
        self.prompt = validators.opt_str("prompt", prompt)
        self.extra = extra or {}

    def __repr__(self) -> str:
        extra_repr = ""
        if self.extra:
            extra_repr = ", extra=..."
        attrs = [
            f"{name}={getattr(self, name)!r}"
            for name in (
                "session_message",
                "session_required_identities",
                "session_required_policies",
                "session_required_single_domain",
                "session_required_mfa",
                "required_scopes",
                "prompt",
            )
        ]
        return "GlobusAuthorizationParameters(" + ", ".join(attrs) + extra_repr + ")"


class GARE(Serializable):
    """
    Represents a Globus Auth Requirements Error.

    A Globus Auth Requirements Error is a class of error that is returned by Globus
    services to indicate that additional authorization is required in order to complete
    a request and contains information that can be used to request the appropriate
    authorization.

    :ivar code: The error code for this error.
    :vartype code: str

    :ivar authorization_parameters: The authorization parameters for this error.
    :vartype authorization_parameters: GlobusAuthorizationParameters

    :ivar extra: A dictionary of additional fields that were provided. May
        be used for forward/backward compatibility.
    :vartype extra: dict
    """

    def __init__(
        self,
        code: str,
        authorization_parameters: dict[str, t.Any] | GlobusAuthorizationParameters,
        *,
        extra: dict[str, t.Any] | None = None,
    ) -> None:
        self.code = validators.str_("code", code)
        self.authorization_parameters = validators.instance_or_dict(
            "authorization_parameters",
            authorization_parameters,
            GlobusAuthorizationParameters,
        )
        self.extra = extra or {}

    def __repr__(self) -> str:
        extra_repr = ""
        if self.extra:
            extra_repr = ", extra=..."
        return (
            f"GARE(code={self.code!r}, "
            f"authorization_parameters={self.authorization_parameters!r}"
            f"{extra_repr})"
        )

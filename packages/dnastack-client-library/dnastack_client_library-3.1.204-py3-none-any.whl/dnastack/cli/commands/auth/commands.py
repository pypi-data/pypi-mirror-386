from typing import List, Optional, Any, Dict, Iterator

import click
from click import Group
from imagination import container

from dnastack.cli.commands.auth.event_handlers import handle_revoke_begin, handle_revoke_end, handle_auth_begin, \
    handle_auth_end, \
    handle_no_refresh_token, handle_refresh_skipped
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, RESOURCE_OUTPUT_ARG, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.helpers.iterator_printer import show_iterator
from dnastack.cli.helpers.printer import echo_header, echo_list
from dnastack.common.auth_manager import AuthManager, ExtendedAuthState
from dnastack.common.logger import get_logger
from dnastack.configuration.manager import ConfigurationManager
from dnastack.configuration.wrapper import ConfigurationWrapper
from dnastack.http.session_info import SessionManager


def init_auth_commands(group: Group):
    @formatted_command(
        group=group,
        name='login',
        specs=[
            ArgumentSpec(
                name='force_refresh',
                arg_names=['-force-refresh'],
                help='If set, this command will only refresh any existing session(s).',
            ),
            ArgumentSpec(
                name='revoke_existing',
                arg_names=['-revoke-existing'],
                help='If set, the existing session(s) will be force-revoked before the authentication.',
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ],
    )
    def login(context: Optional[str],
              endpoint_id: Optional[str] = None,
              force_refresh: bool = False,
              revoke_existing: bool = False):
        """
        Log in to ALL service endpoints or ONE specific service endpoint.
    
        If the endpoint ID is not specified, it will initiate the auth process for all endpoints.
        """
        handler = AuthCommandHandler(context_name=context)
        handler.initiate_authentications(endpoint_ids=[endpoint_id] if endpoint_id else [],
                                         force_refresh=force_refresh,
                                         revoke_existing=revoke_existing)

    @formatted_command(
        group=group,
        name='status',
        specs=[
            RESOURCE_OUTPUT_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def status(context: Optional[str],
               endpoint_id: Optional[str] = None,
               output: Optional[str] = None):
        """ Check the status of all authenticators. """
        handler = AuthCommandHandler(context_name=context)
        show_iterator(output or RESOURCE_OUTPUT_ARG.default, handler.get_states([endpoint_id] if endpoint_id else None))
    
    
    @formatted_command(
        group=group,
        name='revoke',
        specs=[
            ArgumentSpec(
                name='force',
                arg_names=['-force', '-f'],
                help='Force the auth revocation without prompting the user for confirmation',
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def revoke(context: Optional[str],
               endpoint_id: Optional[str] = None,
               force: bool = False):
        """
        Revoke the authorization to one to many endpoints.
    
        If the endpoint ID is not specified, it will revoke all authorizations.
        """
        handler = AuthCommandHandler(context_name=context)
        handler.revoke([endpoint_id] if endpoint_id else [], force)
    
    

    
class AuthCommandHandler:
    def __init__(self, context_name: Optional[str] = None):
        self._logger = get_logger(type(self).__name__)
        self._session_manager: SessionManager = container.get(SessionManager)
        self._config_manager: ConfigurationManager = container.get(ConfigurationManager)
        self._context_name = context_name
        self._auth_manager = AuthManager(
            context=ConfigurationWrapper(self._config_manager.load(), self._context_name).current_context)

    def revoke(self, endpoint_ids: List[str], no_confirmation: bool):
        # NOTE: This is currently designed exclusively to work with OAuth2 config.
        #       Need to rework (on the output) to support other types of authenticators.

        if not no_confirmation and not endpoint_ids:
            echo_header('WARNING: You are about to revoke the access to all endpoints.', bg='yellow', fg='white')

        auth_manager = self._auth_manager
        auth_manager.events.on('revoke-begin', handle_revoke_begin)
        auth_manager.events.on('revoke-end', handle_revoke_end)

        affected_endpoint_ids: List[str] = auth_manager.revoke(
            endpoint_ids,
            confirmation_operation=(
                None
                if no_confirmation
                else lambda: click.confirm('Do you want to proceed?')
            )
        )

        echo_header('Summary')

        if affected_endpoint_ids:
            echo_list('The client is no longer authenticated to the following endpoints:',
                      affected_endpoint_ids)
        else:
            click.echo('No changes')

        print()

    def get_states(self, endpoint_ids: List[str] = None) -> Iterator[ExtendedAuthState]:
        return self._auth_manager.get_states(endpoint_ids)

    def _remove_none_entry_from(self, d: Dict[str, Any]) -> Dict[str, Any]:
        return {
            k: v
            for k, v in d.items()
            if v is not None
        }

    def initiate_authentications(self,
                                 endpoint_ids: List[str] = None,
                                 force_refresh: bool = False,
                                 revoke_existing: bool = False,
                                 context_name: Optional[str] = None):
        # NOTE: This is currently designed exclusively to work with OAuth2 config.
        #       Need to rework (on the output) to support other types of authenticators.

        auth_manager = self._auth_manager
        auth_manager.events.on('auth-begin', handle_auth_begin)
        auth_manager.events.on('auth-end', handle_auth_end)
        auth_manager.events.on('no-refresh-token', handle_no_refresh_token)
        auth_manager.events.on('refresh-skipped', handle_refresh_skipped)

        auth_manager.initiate_authentications(endpoint_ids, force_refresh, revoke_existing, allow_token_exchange=False)


# Copyright (c) 2019 Martin Lafaix (martin.lafaix@external.engie.com)
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0

"""A base class wrapping OKTA APIs.

There can be as many _OKTA_ instances as needed.

This module depends on the public **asyncio** and **okta.client**
libraries.  It also depend on two **zabel-commons** modules,
#::zabel.commons.exceptions and #::zabel.commons.utils.
"""

from typing import Any, Dict, List, Optional

import asyncio

from zabel.commons.exceptions import ApiError
from zabel.commons.utils import (
    ensure_nonemptystring,
    ensure_noneorinstance,
    api_call,
    add_if_specified,
)


class OktaException(Exception):
    """Generic Okta exception class."""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class Okta:
    """Okta Low-Level Wrapper.

    ## Reference URLs

    <https://developer.okta.com/docs/reference/api/groups/>
    <https://developer.okta.com/docs/reference/api/users/>

    ## Implemented features

    - users
    - groups

    ## Examples

    ```python
    from zabel.elements.clients import Okta

    url = 'https://okta.example.com'
    token = '...'
    okta = Okta(url, token)
    user = okta.get_user_info('JP5300')
    ```
    """

    def __init__(
        self,
        url: str,
        token: str,
    ):
        """Create an Okta instance object.

        # Required parameters

        - url: a non-empty string
        - token: a non-empty string

        # Usage

        `url` must be the URL of your Okta instance.  For example:

            'https://your-domain.okta-emea.com'
        """
        ensure_nonemptystring('url')
        ensure_nonemptystring('token')

        self.url = url
        self.client = None
        self.token = token

    def _client(self) -> 'okta.OktaClient':
        """singleton instance, only if needed."""

        if self.client is None:
            from okta.client import Client as OktaClient

            self.client = OktaClient({'orgUrl': self.url, 'token': self.token})
        return self.client

    ####################################################################
    # users
    #
    # create_user
    # list_users
    # get_user_info
    # list_groups_by_user_id

    @api_call
    def create_user(
        self,
        login: str,
        first_name: str,
        last_name: str,
        email: str,
        credentials: Optional[Dict[str, Any]] = None,
        group_ids: Optional[List[str]] = None,
        user_type: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create an Okta user.

        # Required parameters

        - login: a non-empty string
        - first_name: a non-empty string
        - last_name: a non-empty string
        - email: a non-empty string

        # Optional parameters

        - credentials: a dictionary.  Refer to Okta API documentation
          for more information.
        - group_ids: a list of strings.  Each string is a group ID.
        - user_type: a dictionary.  Refer to Okta API documentation
          for more information.
        - kwargs: other profile attributes.  Refer to Okta API
          documentation for more information.

        # Returned value

        A dictionary with following entries:

        - activated: a string (a timestamp)
        - created: a string (a timestamp)
        - credentials: a dictionary
        - id: a string
        - lastLogin: a string (a timestamp)
        - lastUpdated: a string (a timestamp)
        - passwordChanged: a boolean
        - profile: a dictionary
        - status: an enum
        - statusChanged: a string (a timestamp)
        - type: a dictionary
        """
        ensure_nonemptystring('login')
        ensure_nonemptystring('first_name')
        ensure_nonemptystring('last_name')
        ensure_nonemptystring('email')
        ensure_noneorinstance('credentials', dict)
        ensure_noneorinstance('group_ids', list)
        ensure_noneorinstance('user_type', dict)

        async def create_user_async(self, body: Dict[str, Any]):
            user, _, error = await self._client().create_user(body)
            if error:
                raise ApiError(error)
            return user.as_dict()

        body = {
            'profile': {
                'login': login,
                'firstName': first_name,
                'lastName': last_name,
                'email': email,
                **kwargs,
            }
        }

        add_if_specified(body, 'credentials', credentials)
        add_if_specified(body, 'groupIds', group_ids)
        add_if_specified(body, 'type', user_type)

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(create_user_async(self, body))

    @api_call
    def list_users(
        self, query_params: Dict[str, str] = {}
    ) -> List[Dict[str, Any]]:
        """Return users list.

        # Optional parameters

        - query_params: a dictionary.  Refer to Okta API documentation
          for more information.

        # Returned value

        A list of _users_.  Each user is a dictionary. See
        #get_user_info() for its format.
        """

        async def list_users_async(self, params: Dict[str, str] = {}):
            users, response, error = await self._client().list_users(
                query_params=params
            )
            if error:
                raise ApiError(error)
            collected = users
            while response.has_next():
                users, error = await response.next()
                if error:
                    raise ApiError(error)
                collected += users
            users_dict = [user.as_dict() for user in collected]
            return users_dict

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(list_users_async(self, query_params))

    @api_call
    def get_user_info(self, user: str) -> Dict[str, Any]:
        """Request the Okta user info.

        # Required parameters

        - user: a non-empty string

        # Returned value

        A dictionary with following entries:

        - activated: a string (a timestamp)
        - created: a string (a timestamp)
        - credentials: a dictionary
        - id: a string
        - lastLogin: a string (a timestamp)
        - lastUpdated: a string (a timestamp)
        - passwordChanged: a boolean
        - profile: a dictionary
        - status: an enum
        - statusChanged: a string (a timestamp)
        - type: a dictionary

        The `profile` dictionary contains the user profile information:

        - countryCode: a string
        - department: a string
        - displayName: a string
        - division: a string
        - email: a string
        - engieb2ectrl: a string
        - equansb2ectrl: a string
        - firstName: a string
        - gbu: a string
        - gid: a string
        - lastName: a string
        - locale: a string
        - login: a string
        - organization: a string
        - orgid: a string
        - userType: a string
        - userprincipalname: a string
        """
        ensure_nonemptystring('user')

        async def get_user_info_async(self, user: str):
            okta_user, _, error = await self._client().get_user(user)
            if error:
                # TODO : check if error is itself an exception, no time
                # for this for now
                raise OktaException(error)
            if okta_user is not None:
                return okta_user.as_dict()
            raise OktaException(f'User {user} not found')

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(get_user_info_async(self, user))

    @api_call
    def list_groups_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """Return the groups for an user.

        # Required parameters

        - user_id: a non-empty string

        # Returned value

        Return a list of groups. Refer to #get_group_by_name() for more
        information.

        # Raised exceptions

        Raises an _ApiError_ exception if an error is thrown by Okta.
        """
        ensure_nonemptystring('user_id')

        async def list_groups_by_user_id_async(self, user_id: str):
            groups, _, error = await self._client().list_user_groups(user_id)
            groups_dict = [group.as_dict() for group in groups]
            return groups_dict

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            list_groups_by_user_id_async(self, user_id)
        )

    ####################################################################
    # groups
    #
    # get_group_by_name
    # add_user_to_group
    # remove_user_from_group
    # list_users_by_group_id

    @api_call
    def get_group_by_name(self, group_name: str) -> Dict[str, Any]:
        """Requet Okta group by his name.

        # Required parameters

        - group_name: a non-empty string

        # Returned value

        A dictionary with following entries:

        - id: a string
        - created: a timestamp
        - lastUpdated: a timestamp
        - lastMembershipUpdated: a timestamp
        - objectClass: an array
        - type: a string
        - profile: a dictionary
        - _links: a dictionary

        # Raised exceptions

        Raises an _ApiError_ exception if zero or more than one
        group is return by Okta API.
        """
        ensure_nonemptystring('group_name')

        async def find_group_async(self, group_name):
            param = {'q': group_name}
            groups, _, error = await self._client().list_groups(
                query_params=param
            )
            if len(groups) == 0:
                raise ApiError(f'The group {group_name} is not an Okta group')
            if len(groups) > 1:
                raise ApiError(
                    f'More than one group with the name: {group_name}'
                )
            return groups[0].as_dict()

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(find_group_async(self, group_name))

    @api_call
    def add_user_to_group(self, group_id: str, user_id: str) -> None:
        """Add user to Okta group.

        # Required parameters

        - group_id: a non-empty string
        - user_id: a non-empty string

        # Raised exceptions

        Raises an _ApiError_ exception if an error is thrown by Okta
        during the operation.
        """
        ensure_nonemptystring('group_id')
        ensure_nonemptystring('user_id')

        async def add_user_to_group_async(self, group_id, user_id):
            _, error = await self._client().add_user_to_group(
                userId=user_id, groupId=group_id
            )
            if error:
                raise ApiError(error)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            add_user_to_group_async(self, group_id, user_id)
        )

    @api_call
    def remove_user_from_group(self, group_id: str, user_id: str) -> None:
        """Remove user from Okta group.

        # Required parameters

        - group_id: a non-empty string
        - user_id: a non-empty string

        # Raised exceptions

        Raises an _ApiError_ exception if an error is thrown by Okta
        during the operation.
        """
        ensure_nonemptystring('group_id')
        ensure_nonemptystring('user_id')

        async def remove_user_from_group_async(self, group_id, user_id):
            _, error = await self._client().remove_user_from_group(
                userId=user_id, groupId=group_id
            )
            if error:
                raise ApiError(error)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            remove_user_from_group_async(self, group_id, user_id)
        )

    @api_call
    def list_users_by_group_id(self, group_id: str) -> List[Dict[str, Any]]:
        """List users in Okta group.

        # Required parameters

        - group_id: a non-empty string

        # Returned value

        Return a list of users. Refer to #get_user_info() for more
        information.

        # Raised exceptions

        Raises an _ApiError_ exception if an error is thrown by Okta.
        """
        ensure_nonemptystring('group_id')

        async def list_users_by_group_id_async(self, group_id):
            users, response, error = await self._client().list_group_users(
                group_id
            )

            collected = users
            while response.has_next():
                users, error = await response.next()
                collected += users
            if error:
                raise ApiError(error)
            users_dict = [user.as_dict() for user in collected]
            return users_dict

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            list_users_by_group_id_async(self, group_id)
        )

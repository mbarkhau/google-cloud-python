# Copyright 2017 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Non-API-specific IAM policy definitions

For allowed roles / permissions, see:
https://cloud.google.com/iam/docs/understanding-roles

Example usage:

.. code-block:: python

   # ``get_iam_policy`` returns a :class:'~google.api_core.iam.Policy`.
   policy = resource.get_iam_policy()

   phred = policy.user("phred@example.com")
   admin_group = policy.group("admins@groups.example.com")
   account = policy.service_account("account-1234@accounts.example.com")
   policy["roles/owner"] = [phred, admin_group, account]
   policy["roles/editor"] = policy.authenticated_users()
   policy["roles/viewer"] = policy.all_users()

   resource.set_iam_policy(policy)
"""

import collections
import warnings

try:
    from collections import abc as collections_abc
except ImportError:  # Python 2.7
    import collections as collections_abc

# Generic IAM roles

OWNER_ROLE = "roles/owner"
"""Generic role implying all rights to an object."""

EDITOR_ROLE = "roles/editor"
"""Generic role implying rights to modify an object."""

VIEWER_ROLE = "roles/viewer"
"""Generic role implying rights to access an object."""

_ASSIGNMENT_DEPRECATED_MSG = """\
Assigning to '{}' is deprecated.  Replace with 'policy[{}] = members."""


class InvalidOperationException(Exception):
    """Raised when trying to use Policy class as a dict."""
    pass


class Policy(collections_abc.MutableMapping):
    """IAM Policy

    See
    https://cloud.google.com/iam/reference/rest/v1/Policy

    Args:
        etag (Optional[str]): ETag used to identify a unique of the policy
        version (Optional[int]): unique version of the policy
    """

    _OWNER_ROLES = (OWNER_ROLE,)
    """Roles mapped onto our ``owners`` attribute."""

    _EDITOR_ROLES = (EDITOR_ROLE,)
    """Roles mapped onto our ``editors`` attribute."""

    _VIEWER_ROLES = (VIEWER_ROLE,)
    """Roles mapped onto our ``viewers`` attribute."""

    def __init__(self, etag=None, version=None):
        self.etag = etag
        self.version = version
        self._bindings = []

    def __iter__(self):
        self.__check_version__()
        return (binding['role'] for binding in self._bindings)

    def __len__(self):
        self.__check_version__()
        return len(self._bindings)

    def __getitem__(self, key):
        self.__check_version__()
        for b in self._bindings:
            if b['role'] is key:
                return set(b['members'])
        return set()

    def __setitem__(self, key, value):
        self.__check_version__()
        value = list(set(value))
        for binding in self._bindings:
            if binding['role'] is key:
                binding['member'] = value
                return
        self._bindings.append({'role': key, 'members': value})

    def __delitem__(self, key):
        self.__check_version__()
        for b in self._bindings:
            if b['role'] is key:
                self._bindings.remove(b)
                return
        raise KeyError(key)

    def __check_version__(self):
        """Raise InvalidOperationException if version is greater than 1."""
        if self.version is not None and self.version > 1: # TODO: add check for conditions in bindings (mirror C#)
            raise InvalidOperationException("TODO: insert migration message")

    @property
    def bindings(self):
        """Gets the policy's bindings."""
        return self._bindings

    @bindings.setter
    def bindings(self, bindings):
        """Sets the policy's bindings."""
        self._bindings = bindings

    @property
    def owners(self):
        """Legacy access to owner role.

        DEPRECATED:  use `policy.bindings` to access bindings instead.
        """
        result = set()
        for role in self._OWNER_ROLES:
            for member in self.get(role, ()):
                result.add(member)
        return frozenset(result)

    @owners.setter
    def owners(self, value):
        """Update owners.

        DEPRECATED:  use `policy.bindings` to access bindings instead.
        """
        warnings.warn(
            _ASSIGNMENT_DEPRECATED_MSG.format("owners", OWNER_ROLE), DeprecationWarning
        )
        self[OWNER_ROLE] = value

    @property
    def editors(self):
        """Legacy access to editor role.

        DEPRECATED:  use `policy.bindings` to access bindings instead.
        """
        result = set()
        for role in self._EDITOR_ROLES:
            for member in self.get(role, ()):
                result.add(member)
        return frozenset(result)

    @editors.setter
    def editors(self, value):
        """Update editors.

        DEPRECATED:  use `policy.bindings` to modify bindings instead.
        """
        warnings.warn(
            _ASSIGNMENT_DEPRECATED_MSG.format("editors", EDITOR_ROLE),
            DeprecationWarning,
        )
        self[EDITOR_ROLE] = value

    @property
    def viewers(self):
        """Legacy access to viewer role.

        DEPRECATED:  use `policy.bindings` to modify bindings instead.
        """
        result = set()
        for role in self._VIEWER_ROLES:
            for member in self.get(role, ()):
                result.add(member)
        return frozenset(result)

    @viewers.setter
    def viewers(self, value):
        """Update viewers.

        DEPRECATED:  use `policy.bindings` to modify bindings instead.
        """
        warnings.warn(
            _ASSIGNMENT_DEPRECATED_MSG.format("viewers", VIEWER_ROLE),
            DeprecationWarning,
        )
        self[VIEWER_ROLE] = value

    @staticmethod
    def user(email):
        """Factory method for a user member.

        Args:
            email (str): E-mail for this particular user.

        Returns:
            str: A member string corresponding to the given user.

        DEPRECATED:  set the role `user:{email}` in the binding instead.
        """
        return "user:%s" % (email,)

    @staticmethod
    def service_account(email):
        """Factory method for a service account member.

        Args:
            email (str): E-mail for this particular service account.

        Returns:
            str: A member string corresponding to the given service account.

        DEPRECATED:  set the role `serviceAccount:{email}` in the binding instead.
        """
        return "serviceAccount:%s" % (email,)

    @staticmethod
    def group(email):
        """Factory method for a group member.

        Args:
            email (str): An id or e-mail for this particular group.

        Returns:
            str: A member string corresponding to the given group.

        DEPRECATED:  set the role `group:{email}` in the binding instead.
        """
        return "group:%s" % (email,)

    @staticmethod
    def domain(domain):
        """Factory method for a domain member.

        Args:
            domain (str): The domain for this member.

        Returns:
            str: A member string corresponding to the given domain.

        DEPRECATED:  set the role `domain:{email}` in the binding instead.
        """
        return "domain:%s" % (domain,)

    @staticmethod
    def all_users():
        """Factory method for a member representing all users.

        Returns:
            str: A member string representing all users.

        DEPRECATED:  set the role `allUsers` in the binding instead.
        """
        return "allUsers"

    @staticmethod
    def authenticated_users():
        """Factory method for a member representing all authenticated users.

        Returns:
            str: A member string representing all authenticated users.

        DEPRECATED:  set the role `allAuthenticatedUsers` in the binding instead.
        """
        return "allAuthenticatedUsers"

    @classmethod
    def from_api_repr(cls, resource):
        """Factory: create a policy from a JSON resource.

        Args:
            resource (dict): policy resource returned by ``getIamPolicy`` API.

        Returns:
            :class:`Policy`: the parsed policy
        """
        version = resource.get("version")
        etag = resource.get("etag")
        policy = cls(etag, version)
        policy.bindings = resource.get("bindings", ())
        return policy

    def to_api_repr(self):
        """Render a JSON policy resource.

        Returns:
            dict: a resource to be passed to the ``setIamPolicy`` API.
        """
        resource = {}

        if self.etag is not None:
            resource["etag"] = self.etag

        if self.version is not None:
            resource["version"] = self.version

        if self._bindings and len(self._bindings) > 0:
            resource["bindings"] = self._bindings

        return resource

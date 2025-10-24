#  Copyright (c) 2023-2026. ECCO Data & AI and other project contributors.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

from typing import final


@final
class BadRequestError(RuntimeError):
    """
    Nexus client error returned if response decoding failed - in case of non-successful HTTP codes.
    """

    def __init__(self, *args, **kwargs):
        pass


@final
class NotFoundError(RuntimeError):
    """
    Nexus client error returned if response decoding failed - in case of non-successful HTTP codes.
    """

    def __init__(self, *args, **kwargs):
        pass


@final
class SdkError(RuntimeError):
    """
    Nexus client error returned if response decoding failed - in case of non-successful HTTP codes.
    """

    def __init__(self, *args, **kwargs):
        pass


@final
class UnauthorizedError(RuntimeError):
    """
    Nexus client error returned if response decoding failed - in case of non-successful HTTP codes.
    """

    def __init__(self, *args, **kwargs):
        pass


@final
class NetworkError(RuntimeError):
    """
    Nexus client error returned if a connection or other networking error occurs.
    """

    def __init__(self, *args, **kwargs):
        pass

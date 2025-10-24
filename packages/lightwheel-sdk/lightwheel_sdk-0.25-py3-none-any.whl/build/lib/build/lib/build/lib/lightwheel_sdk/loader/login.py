# Copyright 2025 Lightwheel Team
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

from .client import LightwheelClient


class Login:
    """
    Login to the API.

    Args:
        client (LightwheelClient): The client to use for login
    """

    def __init__(self, client: LightwheelClient):
        self.client = client

    def login(
        self,
        force_login=False,
        *,
        username: str = None,
        password: str = None,
    ):
        return self.client.login(force_login=force_login, username=username, password=password)

    def logout(self):
        return self.client.logout()

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

from pathlib import Path
import zipfile
from urllib.parse import unquote, urlparse
import requests

from .exception import ApiException
from .client import LightwheelClient

CACHE_PATH = Path("~/.cache/lightwheel_sdk/object/").expanduser()
CACHE_PATH.mkdir(parents=True, exist_ok=True)


class RegistryQuery:
    """
    Query for registry.
    MustHave: registry_type, file_type
    QueryRules:
        registry_name must be provided when file_name is provided, source is recommended to ensure the query is unique
    """

    def __init__(self, registry_type: str, registry_name: list[str] = [], exclude_registry_name: list[str] = [], equals: dict = None, contains: dict = None):
        """Registry Parameter Controller

        Args:
            registry_type (str): objects/fixtures/textures
            registry_name (list[str], optional): _description_. Defaults to [].
            exclude_registry_name (list[str], optional): _description_. Defaults to [].
            equals (dict, optional): _description_. Defaults to {}.
            contains (dict, optional): _description_. Defaults to {}.
        """
        if registry_type not in ["objects", "fixtures", "textures"]:
            raise ValueError("Invalid registry type")
        self.registry_type = registry_type
        self.registry_name = registry_name
        self.exclude_registry_name = exclude_registry_name
        self.eqs = []
        if equals is not None:
            for key, value in equals.items():
                self.eqs.append({"key": key, "value": value})
        self.contains_list = []
        if contains is not None:
            for key, value in contains.items():
                self.contains_list.append({"key": key, "value": value})

    def query_file(self, file_type: str, file_name: str = "", source: list[str] = [], projects: list[str] = [], quality_levels: list[int] = []):
        """Query for a file in the registry

        Args:
            file_type (str): USD/MJCF
            file_name (str, optional): _description_. Defaults to "".
            source (list[str], optional): _description_. Defaults to [].
            projects (list[str], optional): _description_. Defaults to [].
            quality_levels (list[int], optional): _description_. Defaults to [], BASIC = 1, GOOD = 2.
        """
        file_type_to_enum = {"USD": 1, "MJCF": 2, "other": 3}
        file_type_enum = file_type_to_enum.get(file_type, "")
        if file_type_enum == "":
            raise ValueError(f"Invalid file type: {file_type}")
        query_dict = {
            "file_type": file_type_enum,
            "registry_type": self.registry_type,
            "eq": self.eqs,
            "contain": self.contains_list,
        }
        if len(source) > 0:
            query_dict["source"] = source
        if len(self.registry_name) > 0:
            query_dict["registry_name"] = self.registry_name
        if len(self.exclude_registry_name) > 0:
            query_dict["exclude_registry_name"] = self.exclude_registry_name
        if file_name != "":
            if len(self.registry_name) == 0:
                raise ValueError("registry_name is required when file_name is provided")
            query_dict["file_name"] = file_name
        if len(projects) > 0:
            query_dict["project_names"] = projects
        if len(quality_levels) > 0:
            query_dict["quality_levels"] = quality_levels
        return query_dict


class ObjectLoader:
    """
    Load an object from the floorplan service.

    Args:
        host (str): The host of the API
    """

    def __init__(self, client: LightwheelClient):
        self.client = client
        self.version_cache = []

    def acquire_by_registry(
        self,
        registry_type: str,
        registry_name: list[str] = [],
        exclude_registry_name: list[str] = [],
        eqs: dict = None,
        contains: dict = None,
        file_type: str = "USD",
        file_name: str = "",
        source: list[str] = [],
        projects: list[str] = [],
        quality_levels: list[int] = [],
    ):
        q = RegistryQuery(registry_type, registry_name, exclude_registry_name, eqs, contains)
        data = q.query_file(file_type, file_name, source, projects, quality_levels)
        res = self.client.post("/floorplan/v1/registry/get-object", data=data)
        object_res = res.json()
        del object_res["fileUrl"]
        return *self.download_to_cache(res), object_res

    def acquire_by_file_version(self, file_version_id: str):
        res = self.client.post("/floorplan/v1/object/version-get", data={"id": file_version_id}, timeout=300)
        object_res = res.json()
        del object_res["fileUrl"]
        return *self.download_to_cache(res), object_res

    def list_registry(self):
        res = self.client.post("/floorplan/v1/registry/list", data={})
        return res.json()["data"]

    def acquire_object(self, rel_path, file_type: str, version=None):
        """
        DEPRECATED! Use acquire_by_registry instead.
        """
        try:
            return self._acquire_object(rel_path, file_type, version)
        except ApiException as e:
            print(e)
        finally:
            pass

    def _acquire_object(self, rel_path, file_type: str, version=None):
        """
        Acquire an object from the floorplan.

        Args:
            levels (list[str]): The levels of the object
            file_type (str): The type of the object, USD, MJCF
        """
        rel_path = rel_path.strip("/")
        levels = rel_path.split("/")
        file_type_to_enum = {"USD": 1, "MJCF": 2}
        if len(levels) > 6 or len(levels) == 0:
            raise ValueError(f"Invalid levels number: {len(levels)}")
        file_type_enum = file_type_to_enum.get(file_type, "")
        if file_type_enum == "":
            raise ValueError(f"Invalid file type: {file_type}")
        if version:
            usd_path, object_name, res = self.acquire_by_file_version(version)
        else:
            filename = rel_path.split("/")[-1]
            registry_name = rel_path.split("/")[-2]
            source = [rel_path.split("/")[-3]]
            usd_path, object_name, res = self.acquire_by_registry("objects", file_type=file_type, file_name=filename, registry_name=[registry_name], source=source)
        self.version_cache.append({object_name: res.get("fileVersionId", None)})
        return usd_path

    def download_to_cache(self, res):
        object_type, object_name, s3_url, cache_file_path = self.get_object_type_and_path(res)
        r = requests.get(s3_url, timeout=300)
        if r.status_code != 200:
            raise ApiException(r)
        with open(cache_file_path, "wb") as f:
            f.write(r.content)
        with zipfile.ZipFile(cache_file_path, "r") as zip_ref:
            zip_ref.extractall(CACHE_PATH)
        if object_type == "USD":
            return str(CACHE_PATH / object_name / (object_name + ".usd")), object_name
        elif object_type == "MJCF":
            return str(CACHE_PATH / object_name / "model.xml"), object_name
        else:
            raise ValueError(f"Invalid object type: {object_type}")

    def get_object_type_and_path(self, res):
        res_json = res.json()
        s3_url = res_json["fileUrl"]
        url_path = urlparse(s3_url).path
        url_path = unquote(url_path)
        path_list = url_path.strip("/").split("/")
        object_file_path = path_list[-1]
        object_name = object_file_path.split(".")[0]
        object_type = "USD"
        return object_type, object_name, s3_url, CACHE_PATH / object_file_path

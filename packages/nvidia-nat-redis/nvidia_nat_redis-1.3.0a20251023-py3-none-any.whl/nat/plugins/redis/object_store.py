# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pydantic import Field

from nat.builder.builder import Builder
from nat.cli.register_workflow import register_object_store
from nat.data_models.object_store import ObjectStoreBaseConfig


class RedisObjectStoreClientConfig(ObjectStoreBaseConfig, name="redis"):
    """
    Object store that stores objects in a Redis database.
    """

    host: str = Field(default="localhost", description="The host of the Redis server")
    db: int = Field(default=0, description="The Redis logical database number")
    port: int = Field(default=6379, description="The port of the Redis server")
    bucket_name: str = Field(description="The name of the bucket to use for the object store")


@register_object_store(config_type=RedisObjectStoreClientConfig)
async def redis_object_store_client(config: RedisObjectStoreClientConfig, _builder: Builder):

    from .redis_object_store import RedisObjectStore

    async with RedisObjectStore(**config.model_dump(exclude={"type"})) as store:
        yield store

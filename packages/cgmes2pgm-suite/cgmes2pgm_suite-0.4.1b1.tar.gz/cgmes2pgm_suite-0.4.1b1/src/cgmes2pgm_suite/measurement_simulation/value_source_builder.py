# Copyright [2025] [SOPTIM AG]
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

import uuid

import pandas as pd
from cgmes2pgm_converter.common import (
    CIM_ID_OBJ,
    CgmesDataset,
    MeasurementValueSource,
    Profile,
)


class ValueSourceBuilder:

    def __init__(
        self,
        datasource: CgmesDataset,
    ):
        self._datasource = datasource
        self._sources: dict[MeasurementValueSource, str] = {}

    def build_from_sv(self):

        for source in MeasurementValueSource:
            self._sources[source] = f'"{uuid.uuid4()}"'

        df = pd.DataFrame()
        df[f"{CIM_ID_OBJ}.name"] = [f'"{source}"' for source in MeasurementValueSource]
        df[f"{CIM_ID_OBJ}.mRID"] = [
            self._sources[source] for source in MeasurementValueSource
        ]
        df["rdf:type"] = f"<{self._datasource.cim_namespace}MeasurementValueSource>"

        # mrids in sources to urn
        for source in MeasurementValueSource:
            self._sources[source] = self._datasource.mrid_to_urn(self._sources[source])

        [self._datasource.insert_df(df, pr) for pr in self._to_graph(Profile.OP)]

    def get_sources(self) -> dict[MeasurementValueSource, str]:
        return self._sources

    def _to_graph(self, profile: Profile) -> list[Profile | str]:
        to_graph: list[Profile | str] = [profile]
        if not self._datasource.split_profiles:
            to_graph.append(self._datasource.named_graphs.default_graph)

        return to_graph

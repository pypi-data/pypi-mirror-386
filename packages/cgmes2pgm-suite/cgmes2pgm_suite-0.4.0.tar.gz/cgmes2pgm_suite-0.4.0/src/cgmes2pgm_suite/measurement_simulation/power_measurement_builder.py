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
    CIM_MEAS,
    CgmesDataset,
    MeasurementValueSource,
    Profile,
)

from .meas_ranges import MeasurementRangeSet


# pylint: disable=too-few-public-methods
class PowerMeasurementBuilder:

    default_query = """
        SELECT
            (SAMPLE(?_sv) as ?sv)
            ?term
            (SAMPLE(?_eq) as ?eq)
            (SAMPLE(?_name) as ?name)
            (SAMPLE(?_tn) as ?tn)
            (SAMPLE(?_p) as ?p)
            (SAMPLE(?_q) as ?q)
            (SAMPLE(?_nomV) as ?nomV)
        WHERE {
            ?_sv cim:SvPowerFlow.p ?_p;
                    cim:SvPowerFlow.q ?_q;
                    cim:SvPowerFlow.Terminal ?term.

            ?term cim:Terminal.ConductingEquipment ?_eq;
                  cim:Terminal.TopologicalNode ?_tn;
                  cim:IdentifiedObject.name ?_name.

            ?_tn cim:TopologicalNode.BaseVoltage/cim:BaseVoltage.nominalVoltage ?_nomV.

            OPTIONAL {
                ?_eq cim:RotatingMachine.GeneratingUnit ?_genUnit.
                ?_genUnit cim:GeneratingUnit.maxOperatingP ?_maxP;
                        cim:GeneratingUnit.minOperatingP ?_minP.
            }

            OPTIONAL {
                ?_eq cim:ExternalNetworkInjection.maxP ?_maxP;
                        cim:ExternalNetworkInjection.minP ?_minP.
            }

            OPTIONAL {
                ?_trEnd cim:TransformerEnd.Terminal ?term;
                        cim:PowerTransformerEnd.ratedS ?_maxP.
            }

            OPTIONAL {
                ?_limitSet cim:OperationalLimitSet.Terminal ?term.
                ?_currentLimit cim:OperationalLimit.OperationalLimitSet ?_limitSet;
                                cim:CurrentLimit.value ?_maxI.
            }
            BIND(coalesce(?_maxP, xsd:string(xsd:float(?_maxI) * xsd:float(?_nomV) * 0.001)) as ?_maxIxU)
        }
        GROUP BY ?term
        ORDER BY ?term
    """

    graph_query = """
        SELECT
            (SAMPLE(?_sv) as ?sv)
            ?term
            (SAMPLE(?_eq) as ?eq)
            (SAMPLE(?_name) as ?name)
            (SAMPLE(?_tn) as ?tn)
            (SAMPLE(?_p) as ?p)
            (SAMPLE(?_q) as ?q)
            (SAMPLE(?_nomV) as ?nomV)
            (SAMPLE(?_maxIxU) as ?maxIxU)
        WHERE {

            VALUES ?sv_graph { $SV_GRAPH }
            GRAPH ?sv_graph {
                ?_sv cim:SvPowerFlow.p ?_p;
                    cim:SvPowerFlow.q ?_q;
                    cim:SvPowerFlow.Terminal ?term.
            }

            VALUES ?eq_graph { $EQ_GRAPH }
            GRAPH ?eq_graph {
                ?term cim:Terminal.ConductingEquipment ?_eq;
                    cim:IdentifiedObject.name ?_name.


                OPTIONAL {
                    ?_eq cim:RotatingMachine.GeneratingUnit ?_genUnit.
                    ?_genUnit cim:GeneratingUnit.maxOperatingP ?_maxP;
                            cim:GeneratingUnit.minOperatingP ?_minP.
                }

                OPTIONAL {
                    ?_eq cim:ExternalNetworkInjection.maxP ?_maxP;
                            cim:ExternalNetworkInjection.minP ?_minP.
                }

                OPTIONAL {
                    ?_trEnd cim:TransformerEnd.Terminal ?term;
                            cim:PowerTransformerEnd.ratedS ?_maxP.
                }

                OPTIONAL {
                    ?_limitSet cim:OperationalLimitSet.Terminal ?term.
                    ?_currentLimit cim:OperationalLimit.OperationalLimitSet ?_limitSet;
                                    cim:CurrentLimit.value ?_maxI.
                }
                BIND(coalesce(?_maxP, xsd:string(xsd:float(?_maxI) * xsd:float(?_nomV) * 0.001)) as ?_maxIxU)
            }

            VALUES ?tp_graph { $TP_GRAPH }
            GRAPH ?tp_graph {
                ?term cim:Terminal.TopologicalNode ?_tn.
                ?_tn cim:TopologicalNode.BaseVoltage ?_bv.
            }

            VALUES ?eq_graph_bv { $EQ_GRAPH }
            GRAPH ?eq_graph_bv {
                ?_bv cim:BaseVoltage.nominalVoltage ?_nomV.
            }
        }
        GROUP BY ?term
        ORDER BY ?term
    """

    def __init__(
        self,
        datasource: CgmesDataset,
        pq_ranges: MeasurementRangeSet,
        sources: dict[MeasurementValueSource, str],
        with_sigmas: bool = True,
    ):
        self._datasource = datasource
        self._sv_power_to_p_meas: dict = {}
        self._sv_power_to_q_meas: dict = {}
        self._pq_ranges = pq_ranges
        self._sources = sources
        self._with_sigmas = with_sigmas

    def build_from_sv(self):
        sv = self._get_sv_powers()

        self._create_p_meas(sv)
        self._create_q_meas(sv)
        self._create_p_meas_vals(sv)
        self._create_q_meas_vals(sv)

    def _get_sv_powers(self):
        # get IRIs with base_uri, because we are writing into the graph again and need this
        # for referential consistency
        if self._datasource.split_profiles:
            named_graphs = self._datasource.named_graphs
            args = {
                "$TP_GRAPH": named_graphs.format_for_query(Profile.TP),
                "$EQ_GRAPH": named_graphs.format_for_query(Profile.EQ),
                "$SV_GRAPH": named_graphs.format_for_query(Profile.SV),
            }
            q = self._datasource.format_query(self.graph_query, args)
            res = self._datasource.query(q, remove_uuid_base_uri=False)
        else:
            res = self._datasource.query(self.default_query, remove_uuid_base_uri=False)

        return res

    def _create_p_meas(self, sv: pd.DataFrame):
        meas_p = pd.DataFrame()

        meas_p[f"{CIM_MEAS}.Terminal"] = "<" + sv["term"] + ">"
        meas_p[f"{CIM_MEAS}.PowerSystemResource"] = "<" + sv["eq"] + ">"
        meas_p[f"{CIM_MEAS}.measurementType"] = '"ThreePhaseActivePower"'
        meas_p[f"{CIM_MEAS}.unitSymbol"] = (
            f"<{self._datasource.cim_namespace}UnitSymbol.W>"
        )
        meas_p[f"{CIM_MEAS}.unitMultiplier"] = (
            f"<{self._datasource.cim_namespace}UnitMultiplier.M>"
        )

        meas_p[f"{CIM_ID_OBJ}.name"] = '"' + sv["name"] + ' Meas P"'
        meas_p[f"{CIM_ID_OBJ}.mRID"] = [f'"{uuid.uuid4()}"' for _ in range(len(meas_p))]
        self._sv_power_to_p_meas = dict(
            zip(sv["sv"], meas_p[f"{CIM_ID_OBJ}.mRID"].replace('"', ""))
        )

        meas_p["rdf:type"] = f"<{self._datasource.cim_namespace}Analog>"

        ranges = [self._pq_ranges.get_by_value(nomV) for nomV in sv["nomV"]]

        meas_p["cim:Analog.minValue"] = [r.min_value for r in ranges]
        meas_p["cim:Analog.maxValue"] = [r.max_value for r in ranges]
        meas_p["cim:Analog.normalValue"] = meas_p["cim:Analog.maxValue"]

        [self._datasource.insert_df(meas_p, pr) for pr in self._to_graph(Profile.OP)]

    def _create_q_meas(self, sv: pd.DataFrame):
        meas_q = pd.DataFrame()

        meas_q[f"{CIM_MEAS}.Terminal"] = "<" + sv["term"] + ">"
        meas_q[f"{CIM_MEAS}.PowerSystemResource"] = "<" + sv["eq"] + ">"
        meas_q[f"{CIM_MEAS}.measurementType"] = '"ThreePhaseReactivePower"'

        meas_q[f"{CIM_MEAS}.unitSymbol"] = (
            f"<{self._datasource.cim_namespace}UnitSymbol.VAr>"
        )
        meas_q[f"{CIM_MEAS}.unitMultiplier"] = (
            f"<{self._datasource.cim_namespace}UnitMultiplier.M>"
        )

        meas_q[f"{CIM_ID_OBJ}.name"] = '"' + sv["name"] + ' Meas Q"'
        meas_q[f"{CIM_ID_OBJ}.mRID"] = [f'"{uuid.uuid4()}"' for _ in range(len(meas_q))]
        self._sv_power_to_q_meas = dict(
            zip(sv["sv"], meas_q[f"{CIM_ID_OBJ}.mRID"].replace('"', ""))
        )

        meas_q["rdf:type"] = f"<{self._datasource.cim_namespace}Analog>"

        ranges = [self._pq_ranges.get_by_value(nomV) for nomV in sv["nomV"]]

        meas_q["cim:Analog.minValue"] = [r.min_value for r in ranges]
        meas_q["cim:Analog.maxValue"] = [r.max_value for r in ranges]
        meas_q["cim:Analog.normalValue"] = meas_q["cim:Analog.maxValue"]

        [self._datasource.insert_df(meas_q, pr) for pr in self._to_graph(Profile.OP)]

    def _create_p_meas_vals(self, sv: pd.DataFrame):
        vals_p_op = pd.DataFrame()
        vals_p_meas = pd.DataFrame()

        vals_p_op[f"{CIM_ID_OBJ}.mRID"] = [f'"{uuid.uuid4()}"' for _ in range(len(sv))]
        vals_p_meas[f"{CIM_ID_OBJ}.mRID"] = vals_p_op[f"{CIM_ID_OBJ}.mRID"]

        # Op-Profile

        vals_p_op[f"{CIM_ID_OBJ}.name"] = '"' + sv["name"] + ' P Measurement Value"'
        vals_p_op["rdf:type"] = f"<{self._datasource.cim_namespace}AnalogValue>"
        vals_p_meas["rdf:type"] = f"<{self._datasource.cim_namespace}AnalogValue>"

        analogs = [self._sv_power_to_p_meas[sv] for sv in sv["sv"]]
        vals_p_op["cim:AnalogValue.Analog"] = [
            self._datasource.mrid_to_urn(analog) for analog in analogs
        ]
        vals_p_op["cim:AnalogValue.MeasurementValueSource"] = self._sources[
            MeasurementValueSource.SCADA
        ]

        ranges = [self._pq_ranges.get_by_value(nomV) for nomV in sv["nomV"]]
        if self._with_sigmas:
            vals_p_op["cim:MeasurementValue.sensorSigma"] = [r.sigma for r in ranges]

        # Meas-Profile

        vals_p_meas["cim:MeasurementValue.timeStamp"] = '"2021-01-01T00:00:00Z"'
        vals_p_meas["cim:AnalogValue.value"] = [
            self._pq_ranges.distort_measurement(r, p) for r, p in zip(ranges, sv["p"])
        ]

        [self._datasource.insert_df(vals_p_op, pr) for pr in self._to_graph(Profile.OP)]
        [
            self._datasource.insert_df(vals_p_meas, pr, include_mrid=False)
            for pr in self._to_graph(Profile.MEAS)
        ]

    def _create_q_meas_vals(self, sv: pd.DataFrame):
        vals_q_op = pd.DataFrame()
        vals_q_meas = pd.DataFrame()

        vals_q_op[f"{CIM_ID_OBJ}.mRID"] = [f'"{uuid.uuid4()}"' for _ in range(len(sv))]
        vals_q_meas[f"{CIM_ID_OBJ}.mRID"] = vals_q_op[f"{CIM_ID_OBJ}.mRID"]

        # Op-Profile

        vals_q_op[f"{CIM_ID_OBJ}.name"] = '"' + sv["name"] + ' P Measurement Value"'
        vals_q_op["rdf:type"] = f"<{self._datasource.cim_namespace}AnalogValue>"
        vals_q_meas["rdf:type"] = f"<{self._datasource.cim_namespace}AnalogValue>"

        analogs = [self._sv_power_to_q_meas[sv] for sv in sv["sv"]]
        vals_q_op["cim:AnalogValue.Analog"] = [
            self._datasource.mrid_to_urn(analog) for analog in analogs
        ]
        vals_q_op["cim:AnalogValue.MeasurementValueSource"] = self._sources[
            MeasurementValueSource.SCADA
        ]

        ranges = [self._pq_ranges.get_by_value(nomV) for nomV in sv["nomV"]]
        if self._with_sigmas:
            vals_q_op["cim:MeasurementValue.sensorSigma"] = [r.sigma for r in ranges]

        # Meas-Profile

        vals_q_meas["cim:MeasurementValue.timeStamp"] = '"2021-01-01T00:00:00Z"'
        vals_q_meas["cim:AnalogValue.value"] = [
            self._pq_ranges.distort_measurement(r, q) for r, q in zip(ranges, sv["q"])
        ]

        [self._datasource.insert_df(vals_q_op, pr) for pr in self._to_graph(Profile.OP)]
        [
            self._datasource.insert_df(vals_q_meas, pr, include_mrid=False)
            for pr in self._to_graph(Profile.MEAS)
        ]

    def _to_graph(self, profile: Profile) -> list[Profile | str]:
        to_graph: list[Profile | str] = [profile]
        if not self._datasource.split_profiles:
            to_graph.append(self._datasource.named_graphs.default_graph)

        return to_graph

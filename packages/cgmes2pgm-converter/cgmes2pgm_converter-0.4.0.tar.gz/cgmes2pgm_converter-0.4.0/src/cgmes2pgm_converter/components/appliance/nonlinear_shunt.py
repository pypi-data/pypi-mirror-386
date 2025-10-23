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

import numpy as np
from power_grid_model import ComponentType, initialize_array

from cgmes2pgm_converter.common.cgmes_literals import Profile

from ..component import AbstractPgmComponentBuilder


class NonLinearShuntBuilder(AbstractPgmComponentBuilder):
    _query = """
        SELECT  (SAMPLE(?_name) as ?name)
                (SAMPLE(?_topologicalNode) as ?topologicalNode)
                (SAMPLE(?_connected) as ?connected)
                (SAMPLE(?_Terminal) as ?terminal)
                ?ShuntCompensator
                (SUM(xsd:double(?_b)) as ?b)
                (SUM(xsd:double(?_g)) as ?g)
                (SAMPLE(xsd:float(?_sections)) as ?sections)
        WHERE {
            ?_Terminal a cim:Terminal;
                        cim:Terminal.TopologicalNode ?_topologicalNode;
                        cim:ACDCTerminal.connected ?_connected;
                        cim:Terminal.ConductingEquipment ?ShuntCompensator.

            ?ShuntCompensator a cim:NonlinearShuntCompensator;
                                $IN_SERVICE
                                # cim:Equipment.inService "true";
                                cim:IdentifiedObject.name ?_name;
                                cim:ShuntCompensator.sections ?_sections.

            ?Point a cim:NonlinearShuntCompensatorPoint;
                    cim:NonlinearShuntCompensatorPoint.NonlinearShuntCompensator ?ShuntCompensator;
                    cim:NonlinearShuntCompensatorPoint.sectionNumber ?_sectionNum;
                    cim:NonlinearShuntCompensatorPoint.g ?_g;
                    cim:NonlinearShuntCompensatorPoint.b ?_b.

            $TOPO_ISLAND
            #?topoIsland cim:IdentifiedObject.name "Network";
            #            cim:TopologicalIsland.TopologicalNodes ?_topologicalNode.

            filter(xsd:float(?_sectionNum) <= xsd:float(?_sections))
        }

        GROUP BY ?ShuntCompensator
        ORDER BY ?ShuntCompensator
    """

    _query_graph = """
        SELECT  (SAMPLE(?_name) as ?name)
                (SAMPLE(?_topologicalNode) as ?topologicalNode)
                (SAMPLE(?_connected) as ?connected)
                (SAMPLE(?_Terminal) as ?terminal)
                ?ShuntCompensator
                (SUM(xsd:double(?_b)) as ?b)
                (SUM(xsd:double(?_g)) as ?g)
                (SAMPLE(xsd:float(?_sections)) as ?sections)
        WHERE {
            VALUES ?eq_graph { $EQ_GRAPH }
            VALUES ?tp_graph { $TP_GRAPH }
            VALUES ?ssh_graph { $SSH_GRAPH }

            GRAPH ?eq_graph {
                ?_Terminal a cim:Terminal;
                            cim:Terminal.ConductingEquipment ?ShuntCompensator.

                ?ShuntCompensator a cim:NonlinearShuntCompensator;
                                    cim:IdentifiedObject.name ?_name.

                ?Point a cim:NonlinearShuntCompensatorPoint;
                        cim:NonlinearShuntCompensatorPoint.NonlinearShuntCompensator ?ShuntCompensator;
                        cim:NonlinearShuntCompensatorPoint.sectionNumber ?_sectionNum;
                        cim:NonlinearShuntCompensatorPoint.g ?_g;
                        cim:NonlinearShuntCompensatorPoint.b ?_b.
            }

            $IN_SERVICE
            # GRAPH ?ssh_graph { ?ShuntCompensator cim:Equipment.inService "true"; }

            GRAPH ?ssh_graph {
                ?_Terminal cim:ACDCTerminal.connected ?_connected.
                ?ShuntCompensator cim:ShuntCompensator.sections ?_sections.
            }
            GRAPH ?tp_graph {
                ?_Terminal cim:Terminal.TopologicalNode ?_topologicalNode.
            }

            $TOPO_ISLAND
            # GRAPH ?sv_graph {
            #     ?topoIsland # cim:IdentifiedObject.name "Network";
            #                 cim:TopologicalIsland.TopologicalNodes ?topologicalNode.
            # }

            filter(xsd:float(?_sectionNum) <= xsd:float(?_sections))
        }

        GROUP BY ?ShuntCompensator
        ORDER BY ?ShuntCompensator
    """

    def build_from_cgmes(self, _) -> tuple[np.ndarray, dict | None]:
        if self._source.split_profiles:
            named_graphs = self._source.named_graphs
            args = {
                "$IN_SERVICE": self._in_service_graph("?ShuntCompensator"),
                "$TOPO_ISLAND": self._at_topo_island_node_graph("?_topologicalNode"),
                "$EQ_GRAPH": named_graphs.format_for_query(Profile.EQ),
                "$TP_GRAPH": named_graphs.format_for_query(Profile.TP),
                "$SSH_GRAPH": named_graphs.format_for_query(Profile.SSH),
                "$SV_GRAPH": named_graphs.format_for_query(Profile.SV),
            }
            q = self._replace(self._query_graph, args)
            res = self._source.query(q)
        else:
            args = {
                "$IN_SERVICE": self._in_service(),
                "$TOPO_ISLAND": self._at_topo_island_node("?_topologicalNode"),
            }
            q = self._replace(self._query, args)
            res = self._source.query(q)

        arr = initialize_array(self._data_type, self.component_name(), res.shape[0])
        arr["id"] = self._id_mapping.add_cgmes_iris(
            res["ShuntCompensator"], res["name"]
        )
        arr["node"] = [
            self._id_mapping.get_pgm_id(uuid) for uuid in res["topologicalNode"]
        ]
        arr["status"] = res["connected"]
        arr["b1"] = res["b"]
        arr["g1"] = res["g"]

        extra_info = self._create_extra_info_with_type(arr, "NonlinearShuntCompensator")

        for i, pgm_id in enumerate(arr["id"]):
            extra_info[pgm_id]["_terminal"] = res["terminal"][i]

        self._log_type_counts(extra_info)

        return arr, extra_info

    def component_name(self) -> ComponentType:
        return ComponentType.shunt

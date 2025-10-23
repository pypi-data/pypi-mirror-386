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


class LinkBuilder(AbstractPgmComponentBuilder):
    _query = """
        SELECT  ?eq
                ?name
                ?tn1
                ?tn2
                ?status1
                ?status2
                ?term1
                ?term2
                ?open
                ?type
        WHERE {

            VALUES ?_type { cim:Breaker cim:Switch cim:Disconnector}
            ?eq a ?_type;
                cim:IdentifiedObject.name ?name;
                $IN_SERVICE
                # cim:Equipment.inService "true";
                cim:Switch.retained "true";
                cim:Switch.open ?open.

            BIND(STRAFTER(STR(?_type), "#") AS ?type)

            ?term1 a cim:Terminal;
                    cim:Terminal.ConductingEquipment ?eq;
                    cim:Terminal.TopologicalNode ?tn1;
                    cim:ACDCTerminal.sequenceNumber "1";
                    cim:ACDCTerminal.connected ?status1.

            ?term2 a cim:Terminal;
                      cim:Terminal.ConductingEquipment ?eq;
                      cim:Terminal.TopologicalNode ?tn2;
                      cim:ACDCTerminal.sequenceNumber "2";
                      cim:ACDCTerminal.connected ?status2.

            $TOPO_ISLAND
            #?topoIsland cim:IdentifiedObject.name "Network";
            #            cim:TopologicalIsland.TopologicalNodes ?tn1;
            #            cim:TopologicalIsland.TopologicalNodes ?tn2.

            FILTER(?tn1 != ?tn2)
            FILTER(?status1 = "true" && ?status2 = "true" && ?open = "false")
        }
        ORDER BY ?eq
    """
    _query_graph = """
        SELECT  ?eq
                ?name
                ?tn1
                ?tn2
                ?status1
                ?status2
                ?term1
                ?term2
                ?open
                ?type
                # ?retained
        WHERE {
            VALUES ?_type { cim:Breaker cim:Switch cim:Disconnector}

            VALUES ?eq_graph { $EQ_GRAPH }
            GRAPH ?eq_graph {
                ?eq a ?_type;
                    cim:Switch.retained "true";
                    cim:IdentifiedObject.name ?name.

                ?term1 a cim:Terminal;
                        cim:Terminal.ConductingEquipment ?eq;
                        cim:ACDCTerminal.sequenceNumber "1".

                ?term2 a cim:Terminal;
                        cim:Terminal.ConductingEquipment ?eq;
                        cim:ACDCTerminal.sequenceNumber "2".
            }
            BIND(STRAFTER(STR(?_type), "#") AS ?type)

            $IN_SERVICE
            # GRAPH ?ssh_graph { ?eq cim:Equipment.inService "true"; }

            VALUES ?ssh_graph { $SSH_GRAPH }
            GRAPH ?ssh_graph {
                ?eq cim:Switch.open ?open.
                ?term1 cim:ACDCTerminal.connected ?status1.
                ?term2 cim:ACDCTerminal.connected ?status2.
            }

            VALUES ?tp_graph { $TP_GRAPH }
            GRAPH ?tp_graph {
                ?term1 cim:Terminal.TopologicalNode ?tn1.
                ?term2 cim:Terminal.TopologicalNode ?tn2.
            }

            $TOPO_ISLAND
            # GRAPH ?sv_graph {
            #     ?topoIsland # cim:IdentifiedObject.name "Network";
            #                 cim:TopologicalIsland.TopologicalNodes ?tn1;
            #                 cim:TopologicalIsland.TopologicalNodes ?tn2.
            # }

            FILTER(?tn1 != ?tn2)
            FILTER(?status1 = "true" && ?status2 = "true" && ?open = "false")
        }
        ORDER BY ?eq
    """

    def build_from_cgmes(self, _) -> tuple[np.ndarray, dict | None]:
        if self._source.split_profiles:
            named_graphs = self._source.named_graphs
            args = {
                "$IN_SERVICE": self._in_service_graph("?eq"),
                "$TOPO_ISLAND": self._at_topo_island_node_graph("?tn1", "?tn2"),
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
                "$TOPO_ISLAND": self._at_topo_island_node("?tn1", "?tn2"),
            }
            q = self._replace(self._query, args)
            res = self._source.query(q)

        arr = initialize_array(self._data_type, self.component_name(), res.shape[0])
        arr["id"] = self._id_mapping.add_cgmes_iris(res["eq"], res["name"])
        arr["from_node"] = [self._id_mapping.get_pgm_id(uuid) for uuid in res["tn1"]]
        arr["to_node"] = [self._id_mapping.get_pgm_id(uuid) for uuid in res["tn2"]]
        arr["from_status"] = res["status1"] & ~res["open"]
        arr["to_status"] = res["status2"] & ~res["open"]

        extra_info = self._create_extra_info_with_types(arr, res["type"])

        for i, pgm_id in enumerate(arr["id"]):
            extra_info[pgm_id]["_term1"] = res["term1"][i]
            extra_info[pgm_id]["_term2"] = res["term2"][i]

        self._log_type_counts(extra_info)

        return arr, extra_info

    def component_name(self) -> ComponentType:
        return ComponentType.link

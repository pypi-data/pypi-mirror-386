import networkx as nx


class SemanticQueryMatch:
    def __init__(self):
        self.match_relations = []
        self.query_relations = []

    @classmethod
    def from_semantic_match(cls, semantic_match):
        new_semantic_match = cls()
        new_semantic_match.match_relations = list(semantic_match.match_relations)
        new_semantic_match.query_relations = list(semantic_match.query_relations)
        return new_semantic_match

    def add_relation(self, match_relation, query_relation, direction):
        assert direction in ["FW", "BW"]
        status = (self.check_consistency(match_relation, query_relation),)
        if False in status:
            return False
        if direction == "FW":
            self.match_relations = self.match_relations + [match_relation]
            self.query_relations = self.query_relations + [query_relation]
        elif direction == "BW":
            self.match_relations = [match_relation] + self.match_relations
            self.query_relations = [query_relation] + self.query_relations
        return True

    def check_consistency(self, match_relation, query_relation):
        obj_pairs = []
        for qr, mr in zip(
            self.query_relations + [query_relation], self.match_relations + [match_relation]
        ):
            obj_pairs.append((qr.source_obj.id, mr.source_obj.id))
            obj_pairs.append((qr.target_obj.id, mr.target_obj.id))
        obj_consistency = len({qr: mr for qr, mr in obj_pairs}) == len(
            {mr: qr for qr, mr in obj_pairs}
        )

        rel_pairs = []
        for qr, mr in zip(
            self.query_relations + [query_relation], self.match_relations + [match_relation]
        ):
            rel_pairs.append((qr.id, mr.id))
        rel_consistency = len({qr: mr for qr, mr in rel_pairs}) == len(
            {mr: qr for qr, mr in rel_pairs}
        )

        return obj_consistency and rel_consistency

    def get_mapping(self):
        rel_mapping = {}
        obj_mapping = {}
        for qr, mr in zip(self.query_relations, self.match_relations):
            rel_mapping[qr.id] = mr.id
            obj_mapping[qr.source_obj.id] = mr.source_obj.id
            obj_mapping[qr.target_obj.id] = mr.target_obj.id
        return obj_mapping, rel_mapping


def check_connected_and_cycled(sub_graph):
    G = nx.DiGraph()
    for o in sub_graph.get_object_iterator():
        G.add_node(hash(o.id))
    for r in sub_graph.get_relation_iterator():
        G.add_edge(hash(r.source_obj.id), hash(r.target_obj.id))
    assert nx.is_weakly_connected(G) == True, 'Graph must be weakly connected'
    assert len(list(nx.simple_cycles(G))) == 0, 'Graph must be acyclic'


def get_start_relation_id(base_graph, sub_graph):
    rel_ids = set([r.id for r in sub_graph.get_relation_iterator()])
    assert len(rel_ids) > 0
    if len(rel_ids.intersection(base_graph.relations_by_relation_id.keys())) == 0:
        min_rel_id = list(rel_ids)[0]
    else:
        rel_in_length = {
            r_id: (len(base_graph.relations_by_relation_id.get(r_id, set()))) for r_id in rel_ids
        }
        filtered = filter(lambda x: rel_in_length[x] > 0, rel_ids)
        min_rel_id = sorted(filtered, key=lambda x: rel_in_length[x])[0]
    return min_rel_id


def search_pattern(base_graph, sub_graph, required_obj_ids=set(), required_rel_ids=set()):

    check_connected_and_cycled(sub_graph)
    start_relation_id = get_start_relation_id(base_graph, sub_graph)

    sub_triplets = []
    for rel in sub_graph.get_relation_iterator():
        if rel.id == start_relation_id:
            sub_triplets.append((rel.id, rel.source_obj.id, rel.target_obj.id))

    def iteration(
        base_graph, sub_graph, q_relation, chains, direction, passed_relations, out_mapping
    ):

        query_triplet = (
            q_relation.id if q_relation.id in required_rel_ids else None,
            q_relation.source_obj.id if q_relation.source_obj.id in required_obj_ids else None,
            q_relation.target_obj.id if q_relation.target_obj.id in required_obj_ids else None,
        )

        next_chains = []
        if direction is None:
            matched_relations = base_graph.select_relations(*query_triplet)
            next_chains = []
            for matched_relation in matched_relations:
                semantic_match = SemanticQueryMatch()
                add_status = semantic_match.add_relation(matched_relation, q_relation, "FW")
                if add_status:
                    next_chains.append(semantic_match)

        else:
            assert direction in ["FW", "BW"]

            if direction == "FW":
                for chain in chains:
                    obj_mapping, rel_mapping = chain.get_mapping()
                    query_triplet = (
                        q_relation.id if q_relation.id in required_rel_ids else None,
                        obj_mapping[q_relation.source_obj.id],
                        q_relation.target_obj.id
                        if q_relation.target_obj.id in required_obj_ids
                        else None,
                    )
                    matched_relations = base_graph.select_relations(*query_triplet)

                    for matched_relation in matched_relations:
                        semantic_match = SemanticQueryMatch.from_semantic_match(chain)
                        add_status = semantic_match.add_relation(matched_relation, q_relation, "FW")
                        if add_status:
                            next_chains.append(semantic_match)

            elif direction == "BW":
                for chain in chains:
                    obj_mapping, rel_mapping = chain.get_mapping()
                    query_triplet = (
                        q_relation.id if q_relation.id in required_rel_ids else None,
                        q_relation.source_obj.id
                        if q_relation.source_obj.id in required_obj_ids
                        else None,
                        obj_mapping[q_relation.target_obj.id],
                    )
                    matched_relations = base_graph.select_relations(*query_triplet)

                    for matched_relation in matched_relations:
                        semantic_match = SemanticQueryMatch.from_semantic_match(chain)
                        add_status = semantic_match.add_relation(matched_relation, q_relation, "BW")
                        if add_status:
                            next_chains.append(semantic_match)

        chains.clear()
        chains.extend(next_chains)

        for next_q_relation in sub_graph.relations_by_source_id.get(
            q_relation.target_obj.id, set()
        ):
            if next_q_relation in passed_relations:
                continue
            passed_relations.add(next_q_relation)
            iteration(
                base_graph, sub_graph, next_q_relation, chains, "FW", passed_relations, out_mapping
            )

        for next_q_relation in sub_graph.relations_by_target_id.get(
            q_relation.target_obj.id, set()
        ):
            if next_q_relation in passed_relations:
                continue
            passed_relations.add(next_q_relation)
            iteration(
                base_graph, sub_graph, next_q_relation, chains, "BW", passed_relations, out_mapping
            )

        for next_q_relation in sub_graph.relations_by_target_id.get(
            q_relation.source_obj.id, set()
        ):
            if next_q_relation in passed_relations:
                continue
            passed_relations.add(next_q_relation)
            iteration(
                base_graph, sub_graph, next_q_relation, chains, "BW", passed_relations, out_mapping
            )

        for next_q_relation in sub_graph.relations_by_source_id.get(
            q_relation.source_obj.id, set()
        ):
            if next_q_relation in passed_relations:
                continue
            passed_relations.add(next_q_relation)
            iteration(
                base_graph, sub_graph, next_q_relation, chains, "FW", passed_relations, out_mapping
            )

        return chains

    q_relation = sub_graph.select_relations(start_relation_id, None, None)[0]
    chains = iteration(base_graph, sub_graph, q_relation, [], None, set([q_relation]), None)
    return chains

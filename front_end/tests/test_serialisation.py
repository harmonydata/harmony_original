import unittest

from utils.serialisation_tools import deserialise_manual_edges, serialise_manual_edges


class TestSerialisation(unittest.TestCase):

    def test_round_trip_empty(self):
        manual_edges_serialised = {}
        manual_edges_deserialised = deserialise_manual_edges(manual_edges_serialised)
        manual_edges_reserialised = serialise_manual_edges(manual_edges_deserialised)
        self.assertEqual(0, len(manual_edges_reserialised))

    def test_round_trip_one_item(self):
        manual_edges_serialised = {"0,1,2,3": 5}
        manual_edges_deserialised = deserialise_manual_edges(manual_edges_serialised)
        manual_edges_reserialised = serialise_manual_edges(manual_edges_deserialised)
        self.assertEqual(manual_edges_serialised, manual_edges_reserialised)

    def test_one_way_deserialisation(self):
        manual_edges_serialised = {"0,1,5,6": 5, "1,9,2,3": 2}
        manual_edges_deserialised = deserialise_manual_edges(manual_edges_serialised)
        desired_result = {((0, 1), (5, 6)): 5, ((1, 9), (2, 3)): 2}
        self.assertEqual(desired_result, manual_edges_deserialised)

    def test_one_way_serialisation(self):
        manual_edges_deserialised = {((0, 1), (5, 6)): 5, ((1, 9), (2, 3)): 2}
        manual_edges_serialised = serialise_manual_edges(manual_edges_deserialised)
        desired_result = {"0,1,5,6": 5, "1,9,2,3": 2}
        self.assertEqual(desired_result, manual_edges_serialised)

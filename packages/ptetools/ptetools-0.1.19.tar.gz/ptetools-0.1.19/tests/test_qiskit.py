import unittest

import numpy as np
from qiskit.circuit import QuantumCircuit

from ptetools.qiskit import (
    ModifyDelayGate,
    RemoveGateByName,
    RemoveZeroDelayGate,
    bitlist_to_int,
    circuit2matrix,
    counts2dense,
    counts2fractions,
    dense2sparse,
    fractions2counts,
    generate_bitstring_tuples,
    generate_bitstrings,
    invert_permutation,
    largest_remainder_rounding,
    normalize_probability,
    permute_bits,
    permute_counts,
    permute_string,
    random_clifford_circuit,
)


def circuit_instruction_names(qc):
    return [i.operation.name for i in qc]


class TestBitConversions(unittest.TestCase):
    def test_generate_bitstring_tuples(self):
        assert list(generate_bitstring_tuples(1)) == [(0,), (1,)]

    def test_generate_bitstrings(self):
        assert generate_bitstrings(1) == ["0", "1"]
        assert generate_bitstrings(2) == ["00", "01", "10", "11"]

    def test_bitlist_to_int(self):
        assert bitlist_to_int([0, 1, 1]) == 3

    def test_invert_permutation(self):
        np.testing.assert_array_equal(invert_permutation([0, 1]), [0, 1])
        np.testing.assert_array_equal(invert_permutation([1, 0]), [1, 0])
        np.testing.assert_array_equal(invert_permutation([1, 2, 0]), [2, 0, 1])
        np.testing.assert_array_equal(invert_permutation([0, 1, 3, 2]), np.array([0, 1, 3, 2]))

    def test_permute_bits(self):
        permutation = [0, 1, 3, 2]
        assert permute_bits(idx=0, permutation=permutation) == 0
        assert permute_bits(idx=1, permutation=permutation) == 1
        assert permute_bits(idx=2, permutation=permutation) == 2
        assert permute_bits(idx=4, permutation=permutation) == 8

        assert permute_bits(idx=0, permutation=[1, 0]) == 0
        assert permute_bits(idx=1, permutation=[1, 0]) == 2
        assert permute_bits(idx=1, permutation=[1, 2, 0]) == 4
        assert permute_bits(idx=3, permutation=[3, 4, 0, 1, 2]) == 12

    def test_permute_string(self):
        assert permute_string("abcd", [1, 0, 2, 3]) == "bacd"

    def test_permute_counts(self):
        assert permute_counts({"00": 10, "01": 20}, [1, 0]) == {"00": 10, "10": 20}

        counts = {"1110": 945, "0010": 7, "1011": 16}
        permutation = [1, 0, 2, 3]
        assert permute_counts(counts, permutation) == {"1101": 945, "0001": 7, "1011": 16}


class TestQiskit(unittest.TestCase):
    def test_ModifyDelayGate(self):
        time_unit = 20e-9
        qc = QuantumCircuit(1)
        qc.delay(duration=6.1 * time_unit, unit="s")
        p = ModifyDelayGate(dt=time_unit, round=True)
        qc = p(qc)
        assert list(qc)[0].operation.duration == 6

    def test_dense2sparse(self):
        assert dense2sparse([1, 0]) == {"0": 1}
        assert dense2sparse([1, 2]) == {"0": 1, "1": 2}
        assert dense2sparse([1, 2, 3, 4]) == {"00": 1, "01": 2, "10": 3, "11": 4}

    def test_counts2dense(self):
        np.testing.assert_array_equal(counts2dense({"1": 100}, number_of_bits=1), np.array([0, 100]))
        np.testing.assert_array_equal(counts2dense({"1": 100}, number_of_bits=2), np.array([0, 100, 0, 0]))

    def test_counts2fractions(self):
        assert counts2fractions({"1": 0}) == {"1": 0.0}
        assert counts2fractions({"1": 100, "0": 50}) == {"0": 0.3333333333333333, "1": 0.6666666666666666}

    def test_random_clifford_circuit(self):
        c, index = random_clifford_circuit(1)
        assert isinstance(index, int)
        assert c.num_qubits == 1
        c, index = random_clifford_circuit(2)
        assert c.num_qubits == 2

    def test_RemoveGateByName(self):
        qc = QuantumCircuit(3)
        qc.h(0)
        qc.x(1)

        qc_transpiled = RemoveGateByName("none")(qc)
        self.assertEqual(circuit_instruction_names(qc_transpiled), circuit_instruction_names(qc))

        for name in ["x", "h", "dummy"]:
            qc_transpiled = RemoveGateByName(name)(qc)
            self.assertNotIn(name, circuit_instruction_names(qc_transpiled))

    def test_RemoveZeroDelayGate(self):
        qc = QuantumCircuit(3)
        qc.delay(0)
        qc.barrier()
        qc.delay(10, 0)
        qc.barrier()
        qc.delay(10)

        qc_transpiled = RemoveZeroDelayGate()(qc)
        self.assertEqual(
            circuit_instruction_names(qc_transpiled), ["barrier", "delay", "barrier", "delay", "delay", "delay"]
        )

    def test_fractions2counts(self):
        number_set = np.array([20.2, 20.2, 20.2, 20.2, 19.2]) / 100
        r = largest_remainder_rounding(number_set, 100)
        np.testing.assert_array_equal(r, [21, 20, 20, 20, 19])

        fractions = dict(zip(range(3), [10.1, 80.4, 9.6]))
        assert fractions2counts(fractions, 100) == {0: 10, 1: 80, 2: 10}
        assert fractions2counts(fractions, 1024) == {0: 103, 1: 823, 2: 98}

    def test_circuit2matrix(self):
        for k in range(1, 4):
            x = circuit2matrix(QuantumCircuit(k))
            np.testing.assert_array_equal(x, np.eye(2**k, dtype=complex))

        c = QuantumCircuit(1)
        c.x(0)
        x = circuit2matrix(c)
        expected = np.array([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]])
        np.testing.assert_array_equal(x, expected)

    def test_normalize_probability(self):
        np.testing.assert_array_equal(normalize_probability([0, 0.99]), [0, 1])
        np.testing.assert_array_equal(normalize_probability([-0.01, 1.0099]), [0, 1])
        assert sum(normalize_probability([1.2342, 123.321, -0.001])) == 1


if __name__ == "__main__":
    unittest.main()

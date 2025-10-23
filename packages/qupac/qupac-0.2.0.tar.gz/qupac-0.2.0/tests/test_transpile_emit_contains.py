from qupac.parser import parse_qupac
from qupac.transpiler import transpile_to_python


def test_transpile_simple_contains_expected_calls():
    src = """
use qiskit
qubits: 2
entangle 0,1
""".strip()
    ir = parse_qupac(src)
    py = transpile_to_python(ir)
    assert "QuantumCircuit(2)" in py
    assert "qc.cx(0, 1)" in py


def test_param_expr_transpile_includes_pi_expr():
    src = """
qubits: 1
apply RZ(pi/2) to 0
""".strip()
    ir = parse_qupac(src)
    py = transpile_to_python(ir)
    assert "from math import pi" in py
    assert "qc.rz((pi/2), 0)" in py


def test_draw_file_relative_path_unresolved_when_no_source_dir():
    src = """
qubits: 1
draw file: "circ.txt" text
""".strip()
    ir = parse_qupac(src)
    py = transpile_to_python(ir)
    # When parsing from a string (no source file), path should be used as-is in the assigned path
    assert "_p = 'circ.txt'" in py

from qupac.parser import parse_qupac


def test_parse_minimal_entangle():
    src = """
use qiskit
qubits: 2
entangle 0,1
""".strip()
    ir = parse_qupac(src)
    assert ir["use_qiskit"] is True
    assert ir["qubits"] == 2
    # one op: CX 0->1
    ops = ir["ops"]
    assert any(o.get("op") == "apply" and o.get("gate") == "CX" and o.get("controls") == [0] and o.get("targets") == [1] for o in ops)


def test_parse_draw_default_text():
    src = """
qubits: 1
draw
""".strip()
    ir = parse_qupac(src)
    # default draw mode is text
    assert ir.get("draw") == "text"

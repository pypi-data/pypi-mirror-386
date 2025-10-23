from __future__ import annotations

from lark import Lark, Transformer, v_args
from pathlib import Path

_GRAMMAR_PATH = Path(__file__).with_name("grammar.lark")

_lark = Lark(
    _GRAMMAR_PATH.read_text(encoding="utf-8"),
    parser="lalr",
    propagate_positions=True,
    maybe_placeholders=False,
)


class QupacTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.ir = {
            "use_qiskit": False,
            "qubits": None,
            "classical": None,
            "ops": [],
            "simulate": False,
            "symbols": set(),
            "subcircuits": [],
        }
        self._ops_target = self.ir["ops"]

    def _append_op(self, op: dict):
        self._ops_target.append(op)

    def use_stmt(self, _):
        self.ir["use_qiskit"] = True

    def qubits_decl(self, items):
        n = int(items[0])
        if n <= 0:
            raise ValueError("qubits count must be positive")
        self.ir["qubits"] = n

    def classical_decl(self, items):
        n = int(items[0])
        if n < 0:
            raise ValueError("classical count must be >= 0")
        self.ir["classical"] = n

    @v_args(inline=True)
    def apply_stmt(self, gate_obj, targets):
        # gate_obj can be a string gate name or a dict with gate+param_expr
        if isinstance(gate_obj, str):
            g = gate_obj
            op = {"op": "apply", "gate": g}
        else:
            g = gate_obj.get("gate")
            op = {"op": "apply", "gate": g}
            if "param_expr" in gate_obj:
                op["param_expr"] = gate_obj["param_expr"]
                for s in gate_obj.get("param_symbols", []):
                    self.ir["symbols"].add(s)
            elif "param" in gate_obj:
                # legacy fallback
                p = gate_obj["param"]
                if isinstance(p, dict) and "symbol" in p:
                    sym = p["symbol"]
                    self.ir["symbols"].add(sym)
                    op["param_symbol"] = sym
                else:
                    op["param_value"] = float(p)
        op.update(targets)
        self._append_op(op)

    @v_args(inline=True)
    def gate_call(self, gate, param=None):
        g = str(gate)
        if param is None:
            return g
        # param is an expression dict with src and symbols
        expr = param
        for s in expr.get("symbols", set()):
            self.ir["symbols"].add(s)
        return {"gate": g, "param_expr": expr["src"], "param_symbols": list(expr.get("symbols", set()))}

    @v_args(inline=True)
    # Expression nodes for parameter expressions
    @v_args(inline=True)
    def number(self, tok):
        return {"src": str(tok), "symbols": set()}

    @v_args(inline=True)
    def symbol(self, name):
        s = str(name)
        return {"src": s, "symbols": {s}}

    def pi(self, _):
        return {"src": "pi", "symbols": set()}

    @v_args(inline=True)
    def add(self, a, b):
        return {"src": f"({a['src']}+{b['src']})", "symbols": set(a["symbols"]) | set(b["symbols"]) }

    @v_args(inline=True)
    def sub(self, a, b):
        return {"src": f"({a['src']}-{b['src']})", "symbols": set(a["symbols"]) | set(b["symbols"]) }

    @v_args(inline=True)
    def mul(self, a, b):
        return {"src": f"({a['src']}*{b['src']})", "symbols": set(a["symbols"]) | set(b["symbols"]) }

    @v_args(inline=True)
    def div(self, a, b):
        return {"src": f"({a['src']}/{b['src']})", "symbols": set(a["symbols"]) | set(b["symbols"]) }

    @v_args(inline=True)
    def entangle_stmt(self, a, b):
        # entangle a,b -> CX a to b
        self._append_op({"op": "apply", "gate": "CX", "controls": [int(a)], "targets": [int(b)]})

    @v_args(inline=True)
    def superpose_stmt(self, q):
        # superpose q -> H q
        self._append_op({"op": "apply", "gate": "H", "targets": [int(q)]})

    @v_args(inline=True)
    def single_target(self, tgt):
        return {"targets": [int(tgt)]}

    def index_list(self, items):
        # items are Token(INT) instances; convert to ints
        return [int(i) for i in items]

    @v_args(inline=True)
    def targets_list(self, idxs):
        # idxs is a list of ints from index_list
        return {"targets": list(idxs)}

    @v_args(inline=True)
    def controls_to_targets(self, ctrls, tgts):
        return {"controls": list(ctrls), "targets": list(tgts)}

    @v_args(inline=True)
    def control_target(self, ctrl, tgt):
        return {"controls": [int(ctrl)], "targets": [int(tgt)]}

    def measure_all(self, _):
        self._append_op({"op": "measure_all"})

    @v_args(inline=True)
    def measure_one(self, q, c):
        self._append_op({"op": "measure_one", "q": int(q), "c": int(c)})

    def measure_list(self, items):
        # items is [q_list, c_list]
        q_list, c_list = items
        q_list = list(q_list)
        c_list = list(c_list)
        if len(q_list) != len(c_list):
            raise ValueError("measure lists must have same length: measure q1,q2 -> c1,c2")
        for q, c in zip(q_list, c_list):
            self._append_op({"op": "measure_one", "q": int(q), "c": int(c)})

    def reset_stmt(self, items):
        # items is an index_list
        idxs = list(items[0]) if items and items[0] else []
        for q in idxs:
            self._append_op({"op": "reset", "q": int(q)})

    def simulate_stmt(self, _):
        self.ir["simulate"] = True

    @v_args(inline=True)
    def simulator_decl(self, simtype):
        self.ir["simulator"] = str(simtype)

    def noise_none(self, _):
        self.ir["noise"] = {"kind": "none"}

    @v_args(inline=True)
    def noise_depol(self, p):
        self.ir["noise"] = {"kind": "depol", "p": float(p)}

    # Layout & routing
    def initial_layout_decl(self, items):
        # items: [int_list]
        ints = [int(i) for i in items[0]]
        self.ir["initial_layout"] = ints

    def int_list(self, items):
        return [int(i) for i in items]

    def coupling_map_decl(self, items):
        pairs = []
        # items is a flattened list per grammar; easier to parse via string? We'll iterate tokens two by two
        # However, due to how lark groups, we can rebuild from children
        # Accept a sequence like [ [i,j], [k,l], ... ]
        # We'll scan all integers in items in order pairs
        ints = [int(tok) for tok in items if str(tok).isdigit() or isinstance(tok, int)]
        for i in range(0, len(ints), 2):
            pairs.append([ints[i], ints[i+1]])
        self.ir["coupling_map"] = pairs

    def shots_decl(self, items):
        n = int(items[0])
        if n <= 0:
            raise ValueError("shots must be positive")
        self.ir["shots"] = n

    def optimize_decl(self, items):
        lvl = int(items[0])
        if lvl < 0 or lvl > 3:
            raise ValueError("optimize level must be between 0 and 3")
        self.ir["optimize_level"] = lvl

    def draw_stmt(self, items):
        # optional argument: 'text' or 'mpl' (matplotlib). Default to 'text'
        mode = None
        if items:
            mode = str(items[0])
        self.ir["draw"] = mode or "text"

    def draw_file_stmt(self, items):
        path = str(items[0])[1:-1]  # strip quotes
        mode = str(items[1]) if len(items) > 1 else "mpl"
        self.ir["draw_file"] = {"path": path, "mode": mode}

    # ---------- Subcircuits ----------
    def name_list(self, items):
        return [str(x) for x in items]

    @v_args(inline=True)
    def sub_targets_list(self, names):
        return {"targets_names": list(names)}

    @v_args(inline=True)
    def sub_controls_to_targets(self, ctrls, tgts):
        return {"controls_names": list(ctrls), "targets_names": list(tgts)}

    def sub_apply(self, items):
        gate_obj, tgtinfo = items
        if isinstance(gate_obj, str):
            g = gate_obj
            op = {"op": "apply", "gate": g}
        else:
            g = gate_obj.get("gate")
            op = {"op": "apply", "gate": g}
            if "param_expr" in gate_obj:
                op["param_expr"] = gate_obj["param_expr"]
                for s in gate_obj.get("param_symbols", []):
                    self.ir["symbols"].add(s)
        op.update(tgtinfo)
        return op

    def sub_reset(self, items):
        names = list(items[0]) if items else []
        return [{"op": "reset", "q_name": str(n)} for n in names]

    def sub_measure_list(self, items):
        qs, cs = items
        qs = list(qs)
        cs = list(cs)
        if len(qs) != len(cs):
            raise ValueError("measure lists in subcircuit must have same length")
        return [{"op": "measure_one", "q_name": str(q), "c_name": str(c)} for q, c in zip(qs, cs)]

    def sub_body(self, items):
        # Flatten and collect ops (items may contain dicts or lists)
        ops = []
        for it in items:
            if isinstance(it, list):
                ops.extend(it)
            else:
                ops.append(it)
        return ops

    @v_args(inline=True)
    def subcircuit_def(self, name, params, body_ops):
        self.ir["subcircuits"].append({"name": str(name), "params": list(params), "ops": list(body_ops)})

    @v_args(inline=True)
    def call_stmt(self, name, idxs):
        self._append_op({"op": "call", "name": str(name), "args": [int(i) for i in idxs]})

    # ---------- Conditionals (single-line apply) ----------
    @v_args(inline=True)
    def if_apply(self, c_idx, value, gate_obj, targets):
        # Build a conditional apply op
        if isinstance(gate_obj, str):
            g = gate_obj
            op = {"op": "apply", "gate": g}
        else:
            g = gate_obj.get("gate")
            op = {"op": "apply", "gate": g}
            if "param_expr" in gate_obj:
                op["param_expr"] = gate_obj["param_expr"]
                for s in gate_obj.get("param_symbols", []):
                    self.ir["symbols"].add(s)
        op.update(targets)
        op["cond"] = {"c": int(c_idx), "val": int(value)}
        self._append_op(op)

    def program(self, _):
        return self.ir


def parse_qupac(source: str | Path):
    src_path: Path | None = None
    if isinstance(source, Path):
        try:
            source = source.resolve()
        except Exception:
            pass
        text = source.read_text(encoding="utf-8")
        src_path = source
    else:
        text = source
    tree = _lark.parse(text)
    ir = QupacTransformer().transform(tree)
    # carry the source directory for relative paths (e.g., draw file)
    try:
        if src_path is not None:
            ir["_source_dir"] = str(src_path.parent)
    except Exception:
        pass
    return ir

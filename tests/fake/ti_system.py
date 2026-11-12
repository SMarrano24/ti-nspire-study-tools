# Stand-in for ti_system: keys come from KEYS (comma separated, "comma" for a comma);
# calculator lists live in the JSON file named by STORE
import os, json
K = [k for k in os.environ.get("KEYS", "").split(",") if k]
def get_key():
    if not K:
        raise SystemExit(0)
    return K.pop(0)
def _load():
    p = os.environ.get("STORE")
    if not p: raise RuntimeError("no lists")
    return json.load(open(p)) if os.path.exists(p) else {}
def store_list(name, vals):
    d = _load(); d[name] = [float(v) for v in vals]
    json.dump(d, open(os.environ["STORE"], "w"))
def recall_list(name):
    return _load()[name]

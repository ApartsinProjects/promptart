from jinja2 import Template

type_prefix = {"ii": int, "ss": None, "ff": float}  # name pprefix of keys for conversion


def typed_key(k, val):  # try to convert value base on key named convention prefix
    cast_fn = type_prefix.get(k[0:2], None)
    return cast_fn(val) if cast_fn and isinstance(val, str) else val


# dict and list helpers
def safe_pop(d, k): return d.pop(k) if k in d else None


def pop_keys(d, kl):  # in-place
    for k in kl: safe_pop(d, k)
    return d


def _getBranch(d, branch):
    for k in branch: d = d[k]
    return d


def resolveKey(d, key, branch=[]):
    branch = branch if isinstance(branch, list) else [branch]
    src = _getBranch(d, branch)
    for k, v in src[key].items():
        src[key][k] = resolveKey(d, k, branch + [key]) if isinstance(v, dict) else typed_key(k, Template(v).render(d))

    if '$' in src[key]: src[key] = {**eval(src[key]['$']), **src[key]}
    if '$$' in src[key]: src[key] = {**src[key], **eval(src[key]['$$'])}
    return pop_keys(src[key], ["$", "$$"])

def _mergeResolveKey(d,key,params): #copykey from params,resolvpython --versione its values (could be a dict by themselves)
    if not params.get(key,None): params[key]={}
    d[key]={**d.get(key,{}), **params.get(key,{})}
    return resolveKey(d,key)

def prepContext(cfg,ctx):
    print(f"prep context cfg={cfg} ctx={ctx}")
    for k in ["vars", "in_doc"]:cfg[k]=_mergeResolveKey(cfg,k,ctx) 
    return cfg #now its reolved context
        
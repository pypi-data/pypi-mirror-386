import cpmpy as cp

bv = cp.boolvar()
idx1 = cp.intvar(0,2,name="idx1")
idx2 = cp.intvar(0,2,name="idx2")

p,q = cp.intvar(-3, 5, shape=2)

arr = cp.intvar(-3, 5, shape=3, name=tuple("xyz"))
less_then = cp.boolvar(name="lt")
greater_then = cp.boolvar(name="gt")

model = cp.Model([
    bv == (less_then | greater_then),
    # even without these, the solver crashes
    # less_then == (idx1 < idx2),
    # greater_then == (idx1 > idx2),
    arr[idx1] == q,
    arr[idx2] == p
])

model.solve(solver='gcs')
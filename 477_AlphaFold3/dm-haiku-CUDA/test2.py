import jax, jax.numpy as jnp, numpy as np, sys, time
import haiku as hk
def net(x):
    mlp=hk.nets.MLP([64,32,3])
    return mlp(x)
trans=hk.without_apply_rng(hk.transform(net))
key=jax.random.key(0)
X=jax.random.normal(key,(512,8))
w_true=jax.random.normal(jax.random.key(1),(8,3)); y=jnp.argmax(X@w_true,axis=-1)
params=trans.init(key, X[:1])
def loss(p,x,y):
    logits=trans.apply(p,x)
    y1=jax.nn.one_hot(y,3)
    logp=jax.nn.log_softmax(logits)
    return -(y1*logp).sum(-1).mean()
def acc(p,x,y):
    logits=trans.apply(p,x)
    return (logits.argmax(-1)==y).mean()
def step(p,x,y,lr=1e-1):
    l,g=jax.value_and_grad(loss)(p,x,y)
    p=jax.tree_util.tree_map(lambda a,b:a-lr*b, p, g)
    return p,l
acc0=float(acc(params,X,y)); l0=loss(params,X,y)
for i in range(10): params,l=step(params,X,y)
acc1=float(acc(params,X,y)); l1=loss(params,X,y)
print("Haiku acc [before, after]:", round(acc0,3), round(acc1,3))
print("Haiku loss [before, after]:", float(l0), float(l1))
print("OK: Haiku init/apply/grad/update", flush=True)

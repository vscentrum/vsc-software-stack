import jax, jax.numpy as jnp, numpy as np, sys, time
import flax.linen as nn
key = jax.random.key(0)
class MLP(nn.Module):
    features: tuple=(64,32,3)
    @nn.compact
    def __call__(self,x):
        for f in self.features[:-1]: x=nn.relu(nn.Dense(f)(x))
        return nn.Dense(self.features[-1])(x)
def ce_loss(params, x, y, model):
    logits=model.apply(params,x)
    y_onehot=jax.nn.one_hot(y, logits.shape[-1])
    logp=nn.log_softmax(logits)
    return -(y_onehot*logp).sum(-1).mean()
def accuracy(params, x, y, model):
    logits=model.apply(params,x)
    return (logits.argmax(-1)==y).mean()
def step(params, x, y, model, lr=1e-2):
    l,gr=jax.value_and_grad(ce_loss)(params,x,y,model)
    params=jax.tree_util.tree_map(lambda p,g:p-lr*g, params, gr)
    return params,l
model=MLP()
X=jax.random.normal(key,(512,8))
w_true=jax.random.normal(jax.random.key(1),(8,3)); y=jnp.argmax(X@w_true,axis=-1)
params=model.init(key, X[:1])
acc0=float(accuracy(params,X,y,model))
l0=ce_loss(params,X,y,model)
for i in range(10): params,l=step(params,X,y,model,1e-1)
acc1=float(accuracy(params,X,y,model)); l1=ce_loss(params,X,y,model)
print("Flax acc [before, after]:", round(acc0,3), round(acc1,3))
print("Flax loss [before, after]:", float(l0), float(l1))
print("OK: Flax init/apply/grad/update", flush=True)
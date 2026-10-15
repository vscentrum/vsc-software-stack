import os
import sys
import traceback
from importlib.metadata import version

import haiku as hk
import jax
import jax.numpy as jnp
import jaxlib
import jmp


def finite(tree):
    leaves = jax.tree_util.tree_leaves(tree)
    assert leaves, 'Empty output/parameter tree'
    assert all(bool(jnp.all(jnp.isfinite(a))) for a in leaves), 'Non-finite values'


def test_versions():
    import absl
    import tabulate
    assert hk.__version__ == '0.0.16', f'Unexpected dm-haiku: {hk.__version__}'
    assert jax.__version__ == '0.7.0', f'Unexpected JAX: {jax.__version__}'
    assert version('jmp') == '0.0.4', f'Unexpected jmp: {version("jmp")}'
    return f'absl-py {version("absl-py")}, tabulate {version("tabulate")}'


def test_gpu():
    devices = jax.devices()
    assert any(d.platform == 'gpu' for d in devices), f'No JAX GPU devices: {devices}'
    assert jax.default_backend() == 'gpu', f'Default backend is {jax.default_backend()}'
    return ', '.join(str(d) for d in devices if d.platform == 'gpu')


def test_transform_jit():
    net = hk.without_apply_rng(hk.transform(lambda x: hk.nets.MLP([16, 3])(x)))
    x = jnp.arange(32, dtype=jnp.float32).reshape(8, 4) / 16
    params = net.init(jax.random.PRNGKey(0), x)
    y = jax.jit(net.apply)(params, x)
    y.block_until_ready()
    assert y.shape == (8, 3)
    assert y.device.platform == jax.default_backend()
    finite((params, y))
    return f'output {y.shape}, device {y.device}'


def test_training():
    net = hk.without_apply_rng(hk.transform(lambda x: hk.nets.MLP([16, 1])(x)))
    x = jnp.arange(64, dtype=jnp.float32).reshape(16, 4) / 32 - 1
    target = jnp.sum(x, axis=1, keepdims=True) * 0.25
    params = net.init(jax.random.PRNGKey(1), x)

    def loss_fn(p):
        return jnp.mean((net.apply(p, x) - target) ** 2)

    loss, grads = jax.jit(jax.value_and_grad(loss_fn))(params)
    finite((loss, grads))
    assert any(bool(jnp.any(g != 0)) for g in jax.tree_util.tree_leaves(grads))
    new_params = jax.tree_util.tree_map(lambda p, g: p - 0.01 * g, params, grads)
    new_loss = jax.jit(loss_fn)(new_params)
    finite(new_loss)
    assert float(new_loss) < float(loss), f'Loss did not decrease: {loss} -> {new_loss}'
    return f'loss {float(loss):.6f} -> {float(new_loss):.6f}'


def test_jax_vmap():
    net = hk.without_apply_rng(hk.transform(lambda x: hk.Linear(3)(x)))
    x = jnp.arange(32, dtype=jnp.float32).reshape(8, 4) / 8
    params = net.init(jax.random.PRNGKey(2), x)
    batched = jax.jit(net.apply)(params, x)
    mapped = jax.jit(jax.vmap(lambda row: net.apply(params, row)))(x)
    finite(mapped)
    assert bool(jnp.allclose(batched, mapped, rtol=1e-5, atol=1e-5))
    return 'jax.vmap agrees with batched Haiku apply'


def test_rng_dropout():
    def model(x):
        return hk.dropout(hk.next_rng_key(), 0.3, hk.Linear(8)(x))

    net = hk.transform(model)
    x = jnp.ones((32, 8), dtype=jnp.float32)
    params = net.init(jax.random.PRNGKey(3), x)
    apply = jax.jit(net.apply)
    for key_type in (jax.random.PRNGKey, jax.random.key):
        y1 = apply(params, key_type(10), x)
        y2 = apply(params, key_type(10), x)
        y3 = apply(params, key_type(11), x)
        finite((y1, y2, y3))
        assert bool(jnp.array_equal(y1, y2)), 'Identical RNG keys produced different outputs'
        assert not bool(jnp.array_equal(y1, y3)), 'Different RNG keys produced identical outputs'
    return 'legacy PRNGKey and typed jax.random.key both work'


def test_batchnorm_state():
    def model(x, training):
        return hk.BatchNorm(True, True, decay_rate=0.9)(x, is_training=training)

    net = hk.transform_with_state(model)
    x = jnp.arange(128, dtype=jnp.float32).reshape(16, 8) / 32
    params, state = net.init(jax.random.PRNGKey(4), x, True)
    train_apply = jax.jit(lambda p, s, z: net.apply(p, s, None, z, True))
    eval_apply = jax.jit(lambda p, s, z: net.apply(p, s, None, z, False))
    train_y, new_state = train_apply(params, state, x + 1)
    eval_y, eval_state = eval_apply(params, new_state, x)
    finite((train_y, eval_y, new_state))
    assert train_y.shape == eval_y.shape == x.shape
    old_leaves = jax.tree_util.tree_leaves(state)
    new_leaves = jax.tree_util.tree_leaves(new_state)
    assert any(not bool(jnp.array_equal(a, b)) for a, b in zip(old_leaves, new_leaves)), 'State did not update'
    assert all(bool(jnp.array_equal(a, b)) for a, b in zip(new_leaves, jax.tree_util.tree_leaves(eval_state))), 'Eval changed state'
    return 'BatchNorm state updates during training, stays fixed during evaluation'


def test_haiku_scan():
    def model(xs):
        layer = hk.Linear(4)

        def step(carry, x):
            carry = jnp.tanh(layer(carry + x))
            return carry, carry

        _, outputs = hk.scan(step, jnp.zeros((4,), dtype=jnp.float32), xs)
        return outputs

    net = hk.without_apply_rng(hk.transform(model))
    xs = jnp.arange(24, dtype=jnp.float32).reshape(6, 4) / 24
    params = net.init(jax.random.PRNGKey(5), xs)
    outputs = jax.jit(net.apply)(params, xs)
    finite(outputs)
    assert outputs.shape == (6, 4)
    return 'hk.scan parameter reuse and JIT work'


def test_haiku_vmap():
    def model(xs):
        return hk.vmap(hk.Linear(5), split_rng=False)(xs)

    net = hk.without_apply_rng(hk.transform(model))
    xs = jnp.arange(32, dtype=jnp.float32).reshape(8, 4) / 32
    params = net.init(jax.random.PRNGKey(6), xs)
    outputs = jax.jit(net.apply)(params, xs)
    finite(outputs)
    assert outputs.shape == (8, 5)
    return 'hk.vmap correctly threads Haiku parameters'


def test_mixed_precision():
    policy = jmp.get_policy('params=float32,compute=float16,output=float32')
    hk.mixed_precision.set_policy(hk.Linear, policy)
    try:
        net = hk.without_apply_rng(hk.transform(lambda x: hk.Linear(6)(x)))
        x = jnp.ones((8, 4), dtype=jnp.float32)
        params = net.init(jax.random.PRNGKey(7), x)
        y = jax.jit(net.apply)(params, x)
        finite((params, y))
        assert all(p.dtype == jnp.float32 for p in jax.tree_util.tree_leaves(params))
        assert y.dtype == jnp.float32 and y.shape == (8, 6)
        return 'jmp float32 params / float16 compute / float32 output'
    finally:
        hk.mixed_precision.clear_policy(hk.Linear)


def main():
    print('=== dm-haiku 0.0.16 / JAX 0.7.0 CUDA compatibility smoke test ===', flush=True)
    print(f'Python:  {sys.version.split()[0]}')
    print(f'Haiku:   {hk.__version__}')
    print(f'JAX:     {jax.__version__}')
    print(f'jaxlib:  {jaxlib.__version__}')
    print(f'jmp:     {version("jmp")}')
    print(f'Backend: {jax.default_backend()}')
    print(f'Devices: {jax.devices()}', flush=True)
    tests = [
        ('Installed versions and runtime dependencies', test_versions),
        ('GPU backend', test_gpu),
        ('Haiku transform + JAX JIT', test_transform_jit),
        ('JIT + autodiff + SGD update', test_training),
        ('JAX vmap over Haiku', test_jax_vmap),
        ('PRNG keys + Haiku dropout', test_rng_dropout),
        ('Stateful BatchNorm + JIT', test_batchnorm_state),
        ('Haiku scan + JIT', test_haiku_scan),
        ('Haiku vmap + JIT', test_haiku_vmap),
        ('jmp mixed precision on GPU', test_mixed_precision),
    ]
    if os.environ.get('REQUIRE_GPU', '1') == '0':
        tests = [item for item in tests if item[0] != 'GPU backend']
    failed = 0
    for label, fn in tests:
        try:
            detail = fn()
            print(f'[PASS] {label}: {detail}', flush=True)
        except Exception as exc:
            failed += 1
            print(f'[FAIL] {label}: {type(exc).__name__}: {exc}', flush=True)
            traceback.print_exc()
    print(f'=== {len(tests) - failed}/{len(tests)} passed; {failed} failed ===', flush=True)
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()

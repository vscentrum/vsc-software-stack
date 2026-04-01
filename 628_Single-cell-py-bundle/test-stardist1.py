import tempfile
import numpy as np
import tensorflow as tf
import stardist
from stardist.models import Config2D, StarDist2D

print("stardist:", stardist.__version__)
print("tensorflow:", tf.__version__)

rng = np.random.default_rng(42)

def circle_image(shape=(160, 160), circles=((45, 45, 18), (110, 70, 16), (90, 120, 20))):
    yy, xx = np.ogrid[:shape[0], :shape[1]]
    lbl = np.zeros(shape, dtype=np.uint16)
    for i, (cy, cx, r) in enumerate(circles, start=1):
        lbl[(yy - cy) ** 2 + (xx - cx) ** 2 <= r ** 2] = i
    img = (lbl > 0).astype(np.float32)
    return img, lbl

X, Y = [], []
circle_sets = [
    ((45, 45, 18), (110, 70, 16), (90, 120, 20)),
    ((40, 55, 16), (105, 65, 18), (100, 118, 17)),
    ((50, 50, 17), (112, 72, 15), (88, 115, 19)),
]

for cs in circle_sets:
    img, lbl = circle_image(circles=cs)
    x = img + 0.6 * rng.random(img.shape, dtype=np.float32)
    X.append(x.astype(np.float32))
    Y.append(lbl)

conf = Config2D(
    n_rays=32,
    grid=(2, 2),
    use_gpu=False,
    train_epochs=2,
    train_steps_per_epoch=1,
    train_batch_size=2,
    train_loss_weights=(4, 1),
    train_patch_size=(128, 128),
    train_sample_cache=True,
)

with tempfile.TemporaryDirectory() as td:
    model = StarDist2D(conf, name="smoke", basedir=td)
    model.train(X, Y, validation_data=(X[:2], Y[:2]), workers=1)

    prob, dist = model.predict(X[0])
    prob_t, dist_t = model.predict(X[0], n_tiles=(2, 3))

    print("input shape:", X[0].shape)
    print("prob shape:", prob.shape)
    print("dist shape:", dist.shape)
    print("prob_t shape:", prob_t.shape)
    print("dist_t shape:", dist_t.shape)

    assert prob.shape == dist.shape[:2]
    assert prob_t.shape == dist_t.shape[:2]
    assert dist.shape[-1] == conf.n_rays
    assert dist_t.shape[-1] == conf.n_rays
    assert np.isfinite(prob).all()
    assert np.isfinite(dist).all()
    assert np.isfinite(prob_t).all()
    assert np.isfinite(dist_t).all()

print("StarDist CPU smoke test OK")
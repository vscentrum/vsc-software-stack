import numpy as np
import tensorflow as tf
import csbdeep
from csbdeep.models import Config, CARE

print("csbdeep:", csbdeep.__version__)
print("tensorflow:", tf.__version__)

rng = np.random.default_rng(42)
x = rng.random((32, 32), dtype=np.float32)

config = Config(
    axes='YX',
    n_channel_in=1,
    n_channel_out=1,
    unet_n_depth=1,
    unet_kern_size=3,
    unet_n_first=4,
    train_batch_size=2,
    train_steps_per_epoch=1,
    train_epochs=1,
)

model = CARE(config, name='smoke', basedir=None)
y = model.predict(x, axes='YX')

assert y.shape == x.shape
assert np.isfinite(y).all()
assert model.keras_model is not None

print("input shape :", x.shape)
print("output shape:", y.shape)
print("CSBDeep import + TensorFlow backend + CARE predict OK")
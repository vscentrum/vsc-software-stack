cat > /tmp/slicer_biomedisa_test.py <<'PYEOF'
import gc

import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk

from biomedisa_extension.SegmentEditorBiomedisa.Logic.BiomedisaLogic import BiomedisaLogic
from biomedisa_extension.SegmentEditorBiomedisa.Logic.BiomedisaParameter import BiomedisaParameter


def numpy_to_vtk_image(array, vtk_type):
    image = vtk.vtkImageData()
    z, y, x = array.shape
    image.SetDimensions(x, y, z)
    image.SetExtent(0, x - 1, 0, y - 1, 0, z - 1)

    vtk_array = numpy_to_vtk(
        array.ravel(),
        deep=True,
        array_type=vtk_type,
    )
    vtk_array.SetName("ImageScalars")
    image.GetPointData().SetScalars(vtk_array)
    return image


# Synthetic 3D source image.
shape = (16, 32, 32)  # z, y, x

zz, yy, xx = np.indices(shape)
source = (
    200.0
    - ((xx - 16.0) ** 2 + (yy - 16.0) ** 2)
    - 0.5 * (zz - 8.0) ** 2
).astype(np.float32)

# Sparse segmentation on two axial slices.
labels = np.zeros(shape, dtype=np.uint16)

mask = (xx[0] - 16) ** 2 + (yy[0] - 16) ** 2 <= 7 ** 2
labels[4][mask] = 1
labels[11][mask] = 1

source_vtk = numpy_to_vtk_image(source, vtk.VTK_FLOAT)
labels_vtk = numpy_to_vtk_image(labels, vtk.VTK_UNSIGNED_SHORT)

parameter = BiomedisaParameter()

# Keep the functional test small while still exercising the algorithm.
parameter.nbrw = 2
parameter.sorw = 100
parameter.platform = "cuda"
parameter.smooth_active = False
parameter.clean_active = False
parameter.fill_active = False

direction_matrix = np.eye(3)

print("Running Biomedisa Smart Interpolation...")
result = BiomedisaLogic.runBiomedisa(
    input=source_vtk,
    labels=labels_vtk,
    direction_matrix=direction_matrix,
    parameter=parameter,
)

assert result is not None, "Biomedisa returned no result"
assert result.shape == shape, f"Unexpected result shape: {result.shape}"
assert np.max(result) == 1, f"Unexpected labels in result: {np.unique(result)}"

# There must be generated segmentation between our two labelled slices.
interpolated_voxels = np.count_nonzero(result[5:11])
assert interpolated_voxels > 0, "No interpolation was generated between labelled slices"

print("Result shape:", result.shape)
print("Result labels:", np.unique(result))
print("Interpolated voxels:", interpolated_voxels)
print("Biomedisa Smart Interpolation test PASSED")

del source_vtk
del labels_vtk
gc.collect()
PYEOF

QT_QPA_PLATFORM=offscreen \
QT_QPA_OFFSCREEN_NO_GLX=1 \
Slicer \
    --no-splash \
    --no-main-window \
    --python-script /tmp/slicer_biomedisa_test.py \
    --exit-after-startup

echo "exit code: $?"
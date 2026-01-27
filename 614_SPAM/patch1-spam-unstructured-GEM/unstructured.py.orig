# Library of SPAM functions for dealing with unstructured 3D meshes made of tetrahedra
# Copyright (C) 2020 SPAM Contributors
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
"""
This module offers a set of tools for unstructured 3D meshes made of tetrahedra.

>>> # import module
>>> import spam.mesh
>>> spam.mesh.createCuboid()
"""

import multiprocessing

try:
    multiprocessing.set_start_method("fork")
except RuntimeError:
    pass

import gmsh
import numpy
import progressbar
import scipy
import spam.mesh
from spambind.mesh.meshToolkit import triangulateCGAL, countTetrahedraCGAL

# Global number of processes
nProcessesDefault = multiprocessing.cpu_count()


def gmshToSpam(elementsByType, nodesByType):
    """Helper function
    Converts gmsh mesh data to SPAM format by:
    1. reordering by z y x
    2. keeping only tetrahedra

    Parameters
    ----------
        elementsByType: array
            Should be the output of `gmsh.model.mesh.getElementsByType(4)`
        nodesByType: array
            Should be the output of `gmsh.model.mesh.getNodesByType(4)`

    Returns
    -------
        points: 2D numpy array
            The coordinates of the mesh nodes (zyx)
            Each line is [zPos, yPos, xPos]

        connectivity: 2D numpy array
            The connectivity matrix of the tetrahedra elements
            Each line is [node1, node2, node3, node4]
    """

    # Get connectivity and node coordinates
    element_tags, node_tags_element = elementsByType
    node_tags, coord, _ = nodesByType

    # NOTE: gmsh returns coordinates in xyz. This means that:
    # 1. the coordinates array must be switched back to zyx
    # 2. the connectivity array must change so that the nodes of each tetrahedron are numbered
    #    in such a way that the Jacobian is positive. Which means a permutation of the node numbering.
    # 3. in some cases the connectivity matrix has some holes in the node numerotations (some nodes are not used)
    #    it needs to be rebuild for the projection

    # get number of nodes and elements
    n_elements = element_tags.shape[0]
    nodes_set = set(node_tags)
    n_nodes = len(nodes_set)

    # get new node numbering (without holes)
    new_node_numbering = {}
    for i, n in enumerate(nodes_set):
        new_node_numbering[n] = i

    # reshape the connectivity matrix from flatten gmsh output
    connectivity = node_tags.reshape((n_elements, 4))

    # create nodes matrix
    nodes = numpy.zeros((n_nodes, 3))
    for i, (nodes_4x1, coord_4x3) in enumerate(zip(connectivity, coord.reshape((n_elements, 4, 3)))):
        # change connectivity with new orderning
        connectivity[i] = [new_node_numbering[n] for n in nodes_4x1]

        # fill node vector with new connectivity numbering and switch x&z
        for j, n in enumerate(connectivity[i]):
            nodes[n] = coord_4x3[j][::-1]

    # rearange connectivity
    _ = connectivity.copy()
    connectivity[:, 1] = _[:, 3]
    connectivity[:, 3] = _[:, 1]

    i = 0
    for e in list(set(connectivity.ravel())):
        if e != i:
            print("unused node {e}")
        i += 1

    return nodes, connectivity


def getMeshCharacteristicLength(points, connectivity):
    """
    Computes the average distance between two nodes of the edges of each elements.

    Parameters
    ----------
        points: Nx3 array
            List of coordinates of the mesh nodes.

        connectivity: Mx4 array
            Connectivity matrix of the mesh.

    Returns
    -------
        float: the characteristic length
    """

    def _computeDist(n1, n2, points):
        d = [(x1 - x2) ** 2 for x1, x2 in zip(points[n1], points[n2])]
        return sum(d) ** 0.5

    lc = 0.0
    for n1, n2, n3, n4 in connectivity:
        lc += sum(
            [_computeDist(n1, n2, points), _computeDist(n1, n3, points), _computeDist(n1, n4, points), _computeDist(n2, n3, points), _computeDist(n2, n4, points), _computeDist(n3, n4, points)]
        ) / (6.0 * len(connectivity))

    return lc


def createCuboid(
    lengths,
    lc,
    origin=[0.0, 0.0, 0.0],
    periodicity=False,
    verbosity=1,
    gmshFile=None,
    vtkFile=None,
    binary=False,
    skipOutput=False,
):
    """
    Creates an unstructured mesh of tetrahedra inside a cuboid.

    Parameters
    ----------
        lengths: 1D array
            The lengths of the cuboid in the three directions
            The axis order is zyx

        origin: 1D array
            The origin of the cuboid (zyx)

        lc: float
            characteristic length of the elements of the mesh
            (`i.e.`, the average distance between two nodes)

        periodicity: bool, optional
            if periodicity is True, the generated cube will have a periodicity of mesh on surfaces
            Default = False

        gmshFile: string, optional
            If not None, save the gmsh file with name ``gmshFile`` and suffix ``.msh``
            Default = None

        vtkFile: string, optional
            If not None, save the vtk file with name ``vtkFile`` and suffix ``.vtk``
            Defaut = None

        binary: bool, optional
            Save files in binary when possible
            Default = False

        skipOutput: bool, optional
            Returns None to save time (only write the files)
            Default = False

        verbosity: int, optional
            Level  of  information  printed  on  the  terminal  and  the  message  console.
            0: silent except  for  fatal  errors
            1: +errors
            2: +warnings
            3: +direct
            4: +information
            5: +status
            99: +debug
            Default = 1

    Returns
    -------
        points: 2D numpy array
            The coordinates of the mesh nodes (zyx)
            Each line is [zPos, yPos, xPos]

        connectivity: 2D numpy array
            The connectivity matrix of the tetrahedra elements
            Each line is [node1, node2, node3, node4]

    Example
    -------
        >>> points, connectivity = spam.mesh.createCuboid((1.0,1.5,2.0), 0.5)
        create a mesh in a cuboid of size 1,1.5,2 with a characteristic length of 0.5
    """

    # We will switch the input arrays from zyx to xyz before passing them to gmsh
    lengths = lengths[::-1]
    origin = origin[::-1]

    lx, ly, lz = lengths
    ox, oy, oz = origin

    # https://gmsh.info/doc/texinfo/gmsh.pdf

    # initialize mesh
    gmsh.initialize()
    gmsh.model.add("SPAM cuboid")

    # set mesh length options
    # gmsh.option.setNumber("Mesh.MeshSizeMin", lc)
    # gmsh.option.setNumber("Mesh.MeshSizeMax", lc)
    gmsh.option.setNumber("Mesh.Algorithm", 1)  # is the delaunay one (it's the gmsh default)
    gmsh.option.setNumber("Mesh.Optimize", True)
    gmsh.option.setNumber("Mesh.OptimizeNetgen", True)

    # gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    # gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    # gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

    # set general options
    gmsh.option.setNumber("General.Verbosity", verbosity)
    gmsh.option.setNumber("Mesh.Binary", binary)

    # Create cuboid geometry
    gmsh.model.occ.addBox(ox, oy, oz, lx, ly, lz)  # create cube
    gmsh.model.occ.synchronize()

    # set mesh density at all points of the box
    gmsh.model.mesh.setSize(gmsh.model.getEntities(0), lc)  # set mesh density to the 8 vertices
    gmsh.model.occ.synchronize()

    if periodicity:

        def tr(t):
            phi = [1, 0, 0, t[0], 0, 1, 0, t[1], 0, 0, 1, t[2], 0, 0, 0, 1]
            phi = numpy.array(phi).astype("<f4")
            return phi

        gmsh.model.mesh.setPeriodic(2, [2], [1], tr([lx, 0, 0]))  # surface -> dim=2, surface 2 set as surface 1 based on translationX
        gmsh.model.mesh.setPeriodic(2, [4], [3], tr([0, ly, 0]))  # surface -> dim=2, surface 4 set as surface 3 based on translationY
        gmsh.model.mesh.setPeriodic(2, [6], [5], tr([0, 0, lz]))  # surface -> dim=2, surface 6 set as surface 5 based on translationZ
        gmsh.model.occ.synchronize()

    # Generate mesh and optimize
    gmsh.model.mesh.generate(3)
    gmsh.model.occ.synchronize()

    # write gmsh/vtk file
    if gmshFile is not None:
        gmsh.write(f"{gmshFile}.msh")

    # can have additional nodes
    if vtkFile is not None:
        gmsh.write(f"{vtkFile}.vtk")

    # finish here if no output
    if skipOutput:
        gmsh.finalize()
        return None

    # Get connectivity and node coordinates
    nodes, connectivity = gmshToSpam(gmsh.model.mesh.getElementsByType(4), gmsh.model.mesh.getNodesByElementType(4))

    # DEBUG: gmsh GUI
    # gmsh.fltk.run()

    # done with gmsh
    gmsh.finalize()

    # if vtkFile is not None:
    #     meshio.write_points_cells(
    #         f"{vtkFile}.vtk",
    #         nodes,
    #         {"tetra": connectivity},
    #     )

    # return coordinates and connectivity matrix
    return nodes, connectivity


def createCylinder(
    centre,
    radius,
    height,
    lc,
    zOrigin=0.0,
    membrane=0.0,
    verbosity=0,
    gmshFile=None,
    vtkFile=None,
    binary=False,
    skipOutput=False,
):
    """
    Creates an unstructured mesh of tetrahedra inside a cylinder.
    The height of the cylinder is along the z axis.

    Parameters
    ----------
        centre: 1D array
            The two coordinates of the centre of the base disk (yx).

        radius: float
            The radius of the base disk.

        height: float
            The height of the cylinder.

        lc: float
            characteristic length of the elements of the mesh
            (`i.e.`, the average distance between two nodes)

        zOrigin: float, default = 0.0
            Translate the points coordinates by zOrigin in the z direction.

        membrane: float, default = 0.0
            Radius of the membrane (pipe added outside of the cylinder).
            If membrane < lc the membrane is ignored.

        gmshFile: string, optional
            If not None, save the gmsh file with name ``gmshFile`` and suffix ``.msh``
            Default = None

        vtkFile: string, optional
            If not None, save the vtk file with name ``vtkFile`` and suffix ``.vtk``
            Defaut = None

        binary: bool, optional
            Save files in binary when possible
            Default = False

        skipOutput: bool, optional
            Returns None to save time (only write the files)
            Default = False

        verbosity: int, optional
            GMSH level  of  information  printed  on  the  terminal  and  the  message  console.
            0: silent except  for  fatal  errors
            1: +errors
            2: +warnings
            3: +direct
            4: +information
            5: +status
            99: +debug
            Default = 1

    Returns
    -------
        points: 2D numpy array
            The coordinates of the mesh nodes (zyx)
            Each line is [zPos, yPos, xPos]

        connectivity: 2D numpy array
            The connectivity matrix of the tetrahedra elements
            Each line is [node1, node2, node3, node4]

    Example
    -------
        >>> points, connectivity =  spam.mesh.createCylinder((0.0,0.0), 0.5, 2.0, 0.5)
        create a mesh in a cylinder of centre 0,0,0 radius, 0.5 and height 2.0 with a characteristic length of 0.5
    """

    # unpack
    cy, cx = centre
    r = radius

    # https://gmsh.info/doc/texinfo/gmsh.pdf

    # initialize mesh
    gmsh.initialize()
    gmsh.model.add("SPAM cylinder")

    # set mesh length options
    gmsh.option.setNumber("Mesh.MeshSizeMin", lc)
    gmsh.option.setNumber("Mesh.MeshSizeMax", lc)
    gmsh.option.setNumber("Mesh.Algorithm", 5)  # is the delaunay one
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

    # set general options
    gmsh.option.setNumber("General.Verbosity", verbosity)
    gmsh.option.setNumber("Mesh.Binary", binary)

    # Create disk surface
    p0 = gmsh.model.geo.addPoint(cx, cy, zOrigin, lc, 1)
    p1 = gmsh.model.geo.addPoint(cx + r, cy, zOrigin, lc, 2)
    p2 = gmsh.model.geo.addPoint(cx, cy + r, zOrigin, lc, 3)
    p3 = gmsh.model.geo.addPoint(cx - r, cy, zOrigin, lc, 4)
    p4 = gmsh.model.geo.addPoint(cx, cy - r, zOrigin, lc, 5)
    c1 = gmsh.model.geo.addCircleArc(p1, p0, p2)
    c2 = gmsh.model.geo.addCircleArc(p2, p0, p3)
    c3 = gmsh.model.geo.addCircleArc(p3, p0, p4)
    c4 = gmsh.model.geo.addCircleArc(p4, p0, p1)
    l1 = gmsh.model.geo.addCurveLoop([c1, c2, c3, c4])
    s1 = gmsh.model.geo.addPlaneSurface([l1])

    # Create membrane surface
    if membrane > lc:
        r += membrane
        p5 = gmsh.model.geo.addPoint(cx + r, cy, zOrigin, lc, 6)
        p6 = gmsh.model.geo.addPoint(cx, cy + r, zOrigin, lc, 7)
        p7 = gmsh.model.geo.addPoint(cx - r, cy, zOrigin, lc, 8)
        p8 = gmsh.model.geo.addPoint(cx, cy - r, zOrigin, lc, 9)
        c5 = gmsh.model.geo.addCircleArc(p5, p0, p6)
        c6 = gmsh.model.geo.addCircleArc(p6, p0, p7)
        c7 = gmsh.model.geo.addCircleArc(p7, p0, p8)
        c8 = gmsh.model.geo.addCircleArc(p8, p0, p5)
        l2 = gmsh.model.geo.addCurveLoop([c5, c6, c7, c8])
        s2 = gmsh.model.geo.addPlaneSurface([l1, l2])
    # elif membrane > :
    #     warnings.warn(f"membrane thickness is smaller than the characteristic length of the mesh ({membrane} < {lc})")

    gmsh.model.geo.synchronize()

    # Create volume
    gmsh.model.geo.extrude([(2, s1)], 0, 0, height)
    if membrane > lc:
        gmsh.model.geo.extrude([(2, s2)], 0, 0, height)

    # Generate mesh and optimize
    gmsh.model.geo.synchronize()
    gmsh.model.mesh.generate()
    gmsh.model.mesh.optimize("Netgen", True)

    # DEBUG: gmsh GUI
    # gmsh.fltk.run()

    # write gmsh/vtk file
    if gmshFile is not None:
        gmsh.write(f"{gmshFile}.msh")

    # can have additional nodes
    if vtkFile is not None:
        gmsh.write(f"{vtkFile}.vtk")

    # finish here if no output
    if skipOutput:
        gmsh.finalize()
        return None

    # Get connectivity and node coordinates
    nodes, connectivity = gmshToSpam(gmsh.model.mesh.getElementsByType(4), gmsh.model.mesh.getNodesByElementType(4))

    # done with gmsh
    gmsh.finalize()

    # if vtkFile is not None:
    #     meshio.write_points_cells(
    #         f"{vtkFile}.vtk",
    #         nodes,
    #         {"tetra": connectivity},
    #     )

    # return coordinates and connectivity matrix
    return nodes, connectivity


def triangulate(points, alpha=None, weights=None):
    """
    Takes a series of points and optionally their weights and returns a tetrahedral connectivity matrix.

    If a completely regular grid is passed, there will be trouble, add some tiny noise.

    This function uses CGAL's Regular Triangulation in the background (with all weights=1 if they are not passed).
    Weights are passed to CGAL's Regular Triangulation directly and so should be squared if they are radii of particles.

    Users can optionally pass an alpha value to the function with the goal of carving flat boundary tetrahedra away from
    the final mesh. Typical use of the alpha shape could be the removal of flat (almost 0 volume) boundary tetrahedra
    from concave/convex boundaries. Another example might be the removal of tetrahedra from an internal void that exists
    within the domain. In all cases, the user can imagine the alpha tool as a spherical "scoop" that will remove any
    tetrahedra that it is capable of entering. It follows that flat tetrahedra have a very large open face which are
    easily entered by large alpha "scoops". Thus, the user should imagine using a very large alpha value (try starting
    with 5*domain size) to avoid letting the alpha "scoop" enter well formed tetrahedra.

    Consider the following CGAL analogy: The full mesh is an ice cream sundae and the vertices are the
    chocolate chips. The value of alpha is the squared radius of the icecream scoop (following the mesh coordinate units)
    that will go in and remove any tetrahedra that it can pass into. Positive alpha is user defined, negative alpha
    allows CGAL to automatically select a continuous solid (not recommended).
    For more information visit:
    https://doc.cgal.org/latest/Alpha_shapes_3/index.html

    Parameters
    ----------
        points : Nx3 2D numpy array of floats
            N points to triangulate (Z, Y, X)

        weights : numpy vector of N floats
            list of weights associated with points.
            Default = None (which means all weights = 1).

        alpha : float
            size of the alpha shape used for carving the mesh.
            Zero is no carving.
            Negative is CGAL-autocarve which gives an overcut mesh.
            positive is a user-selected size, try 5*domain size.
            Default = 0 (no carving).

    Returns
    -------
        connectivity : Mx4 numpy array of unsigned ints
            delaunay triangulation with each row containing point numbers

    Note
    ----
        Function contributed by Robert Caulk (Laboratoire 3SR, Grenoble)

    """
    # There are two passes here -- CGAL is all based in templates, and just stores the triangulation
    #   in a smart way.
    # We want the connectivity matrix, which CGAL doesn't know about, so we use a first pass to get the
    #   number of tetrahedra, so that we can allocate the connectivity matrix in python, and pass it to
    #   the next pass through the code, which fills the connectivity matrix

    if weights is None:
        weights = numpy.ones(len(points))

    elif weights.shape[0] != points.shape[0]:
        raise Exception("weights array dim1 != points array dim1")

    if alpha is None:
        alpha = numpy.array([0])
    else:
        alpha = numpy.array([alpha])

    points = points.astype("<f4")
    weights = weights.astype("<f4")
    alpha = alpha.astype("<f4")

    # get the number of tetrahedra so we can properly size our connectivityMatrix
    nTet = countTetrahedraCGAL(points, weights, alpha)
    connectivity = numpy.zeros([nTet, 4], dtype="<u4")

    # setup the return types and argument types
    triangulateCGAL(points, weights, connectivity, alpha)

    return connectivity


def projectTetFieldToGrains(points, connectivity, tetField):
    """
    Projects/coarse-grains any field defined on tetrahedra onto grains by volume-averaging over
    all tetrahedra for which a given grain is a node.
    This can be useful for smoothing out a noisy strain field and will not affect the overall agreement between
    the average of strains and the macroscopically observed strains (R.C. Hurley has verified this in a 2017 paper).

    Parameters
    ----------
        points: m x 3 numpy array
            M Particles' coordinates (in deformed configuration for strain field)

        connectivity: n x 4 numpy array
            Delaunay triangulation connectivity generated by spam.mesh.triangulate for example

        tetField: n x 3 x 3 numpy array
            Any field defined on tetrahedra (e.g., Bagi strains from bagiStrain).

    Returns
    -------
        grainField: m x 3 x 3
            array containing (3x3) arrays of strain

    Example
    -------
        grainStrain = spam.mesh.projectBagiStrainToGrains(connectivity,bagiStrain[0],points)
            Returns strains for each grain.

    Notes
    ------
        Function contributed by Ryan Hurley (Johns Hopkins University)

    """
    # grainStrainVoigt:  Ng array containing (6x1) arrays of strain in Voigt notation.
    # RCH Oct 2018.

    # from progressbar import ProgressBar
    # pbar = ProgressBar()

    # print("spam.mesh.projectTetFieldToGrains(): Pre-computing volumes...", end='')
    tetVolumes2 = spam.mesh.tetVolumes(points, connectivity)
    # print("done.")

    # Initialize list of grain values
    grainField = numpy.zeros(([points.shape[0]] + list(tetField.shape[1:])), dtype="<f4")
    # Get all the unique grain IDs in the Deluanay triangulation

    # print("spam.mesh.projectTetFieldToGrains(): Projecting tetrahedal to grains...")
    # Loop through grains...
    # for label in pbar(range(points.shape[0])):
    for label in range(points.shape[0]):
        # print("label = ", label)
        # Get the list of tets for which this label is a node
        touchingTets = numpy.where(connectivity == label)[0]

        volTot = 0.0
        fieldTot = numpy.zeros(list(tetField.shape[1:]), dtype="<f4")
        # Loop through list of tets, summing the strains
        for touchingTet in touchingTets:
            # print("\ttet = ", touchingTet)
            vol = tetVolumes2[touchingTet]
            # Track total volume
            volTot += vol

            # Add volume-weighted field
            fieldTot += tetField[touchingTet] * vol

        # Divide strainTot by volTot
        fieldTot = fieldTot / volTot

        # Store in particles
        grainField[label] = fieldTot

    return grainField


def BCFieldFromDVCField(
    points,
    dvcField,
    mask=None,
    pixelSize=1.0,
    meshType="cube",
    centre=[0, 0],
    radius=1.0,
    topBottom=False,
    tol=1e-6,
    neighbours=4,
):
    """
    This function imposes boundary conditions coming from a DVC result to the nodes of an unstructured FE mesh.

    Parameters
    ----------
        points: 2D numpy array
            Array of ``n`` node positions of the unstructured mesh
            Each line is [nodeNumber, z, y, x]

        dvcField: 2D numpy array
            Array of ``m`` points of the dvc field
            Each line is [zPos, yPos, xPos, zDisp, yDisp, xDisp]

        mask: 2D numpy array, optional
            Boolean array of ``m`` points of the dvc field
            Points with 0 will be ignored for the field interpolation
            Default = None (`i.e.` interpolate based on all of the dvc points)

        pixelSize: float, optional
            physical size of a pixel (`i.e.` 1mm/px)
            Default = 1.0

        meshType: string, optional
            For the moment, valid inputs are ``cube`` and ``cylinder``
            The axis of a cylinder is considered to be ``z``
            Note that if a cylindrical mesh is passed, ``centre`` and ``radius`` are highly recommended
            Default = `cube`

        centre: float, optional
            The centre of the cylinder [y, x] in physical units (`i.e.` mm)
            Default = [0, 0]

        radius: float, optional
            The radius of the cylinder in physical units (`i.e.` mm)
            Default = 1.0

        topBottom: bool, optional
            If boundary conditions are passed only for the top (`i.e.` z=zmax)  and bottom (`i.e.` z=zmin) surfaces of the mesh
            Default = False

        tol: float, optional
            Numerical tolerance for floats equality
            Default = 1e-6

        neighbours: int, , optional
            Neighbours for field interpolation
            Default = 4
    Returns
    -------
        bc: 2D numpy array
            Boundary node displacements
            Each line is [nodeNumber, zPos, yPos, xPos, zDisp, yDisp, xDisp]

    WARNING
    -------
        1. All coordinates and displacement arrays are ``z``, ``y``, ``x``
        2. The axis of a cylinder is considered to be ``z``
    """

    # STEP 1: find the edge nodes
    posMax = [points[:, i].max() for i in range(1, 4)]
    posMin = [points[:, i].min() for i in range(1, 4)]
    bcNodes = []

    if meshType == "cube":
        # extract edge nodes from the mesh
        for point in points:
            if topBottom:
                testMin = abs(point[1] - posMin[0]) < tol
                testMax = abs(point[1] - posMax[0]) < tol
            else:
                testMin = abs(point[1] - posMin[0]) < tol or abs(point[2] - posMin[1]) < tol or abs(point[3] - posMin[2]) < tol
                testMax = abs(point[1] - posMax[0]) < tol or abs(point[2] - posMax[1]) < tol or abs(point[3] - posMax[2]) < tol
            if testMin or testMax:
                bcNodes.append(point)
    elif meshType == "cylinder":
        # extract edge nodes from the mesh
        for point in points:
            testZ = abs(point[1] - posMin[0]) < tol or abs(point[1] - posMax[0]) < tol
            testXY = False
            if not topBottom:
                testXY = (point[2] - centre[0]) ** 2 + (point[3] - centre[1]) ** 2 >= (radius - tol) ** 2
            if testZ or testXY:
                bcNodes.append(point)

    bcNodes = numpy.array(bcNodes)
    m = bcNodes.shape[0]

    # STEP 2: convert dvc field to physical unit
    dvcField *= pixelSize

    # STEP 3: Interpolate the disp values of FE using a weighted influence of the k nearest neighbours from DVC coord
    bcDisp = numpy.zeros((m, 3))
    # create the k-d tree of the coordinates of DVC good points
    if mask is None:
        mask = numpy.ones(dvcField.shape[0])

    goodPoints = numpy.where(mask == 1)
    treeCoord = scipy.spatial.KDTree(dvcField[:, :3][goodPoints])

    for point in range(m):
        distance, ind = treeCoord.query(bcNodes[point, 1:], k=neighbours)

        # Check if we've hit the same point
        if numpy.any(distance == 0):
            bcDisp[point, 0] = dvcField[goodPoints][ind][numpy.where(distance == 0)][0, 3]
            bcDisp[point, 1] = dvcField[goodPoints][ind][numpy.where(distance == 0)][0, 4]
            bcDisp[point, 2] = dvcField[goodPoints][ind][numpy.where(distance == 0)][0, 5]

        else:
            weightSumInv = sum(1 / distance)
            # loop over neighbours
            for neighbour in range(neighbours):
                # calculate its weight
                weightInv = (1 / distance[neighbour]) / float(weightSumInv)
                # replace the disp values the weighted disp components of the ith nearest neighbour
                bcDisp[point, 0] += dvcField[goodPoints][ind[neighbour], 3] * weightInv
                bcDisp[point, 1] += dvcField[goodPoints][ind[neighbour], 4] * weightInv
                bcDisp[point, 2] += dvcField[goodPoints][ind[neighbour], 5] * weightInv

    # return node number and displacements
    return numpy.hstack((bcNodes, bcDisp))


def tetVolumes(points, connectivity):
    """
    This function computes volumes of the tetrahedra passed with a connectivity matrix.
    Using algorithm in https://en.wikipedia.org/wiki/Tetrahedron#Volume

    Parameters
    ----------
        points : Nx3 array
            Array of ``N`` coordinates of the points

        connectivity : Mx4 array
            Array of ``M`` none numbers that are connected as tetrahedra (e.g., the output from triangulate)

    Returns
    -------
        volumes : vector of length M
            Volumes of tetrahedra

    Note
    -----
        Pure python function.
    """

    # Sanity checks on lengths:
    # if connectivity.shape[1] != 4 or points.shape[1] != 3 or connectivity.max() > points.shape[0]:
    #     print("spam.mesh.tetVolumes(): Dimensionality problem, not running")
    #     print("connectivity.max()", connectivity.max(), "points.shape[0]", points.shape[0])
    #     return

    volumes = numpy.zeros(connectivity.shape[0], dtype="<f4")
    connectivity = connectivity.astype(numpy.uint)

    # loop through tetrahedra
    for tetNumber in range(connectivity.shape[0]):
        fourNodes = connectivity[tetNumber]

        if max(fourNodes) >= points.shape[0]:
            print("spam.mesh.unstructured.tetVolumes(): this tet has node > points.shape[0], skipping.")
        else:
            if numpy.isfinite(points[fourNodes]).sum() != 3 * 4:
                print("spam.mesh.unstructured.bagiStrain(): nans in position, skipping")
            else:
                a = points[fourNodes[0]]
                b = points[fourNodes[1]]
                c = points[fourNodes[2]]
                d = points[fourNodes[3]]
                volumes[tetNumber] = numpy.abs(numpy.dot((a - d), numpy.cross((b - d), (c - d)))) / 6.0

    return volumes


# def create2Patche(lengths, mesh_size_1, mesh_size_2, origin=[0., 0., 0.], verbose=False, gmshFile=None, vtkFile=None):
#     import pygmsh
#     import meshio
#
#     lx, ly, lz = lengths
#     ox, oy, oz = origin
#
#     # We will switch the input arrays from zyx to xyz before passing them to pygmsh
#     lengths = lengths[::-1]
#     origin = origin[::-1]
#
#     # raw code
#     code = []
#
#     code.append("SetFactory(\"OpenCASCADE\");")
#     code.append("Mesh.RandomSeed = 0.5;")
#     code.append("Point(1) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox, y=oy, z=oz, mesh_size=mesh_size_1))
#     code.append("Point(2) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox+lx, y=oy, z=oz, mesh_size=mesh_size_1))
#     code.append("Point(3) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox+lx, y=oy+ly, z=oz, mesh_size=mesh_size_1))
#     code.append("Point(4) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox, y=oy+ly, z=oz, mesh_size=mesh_size_1))
#     code.append("Point(5) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox, y=oy, z=oz+lz, mesh_size=mesh_size_1))
#     code.append("Point(6) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox+lx, y=oy, z=oz+lz, mesh_size=mesh_size_1))
#     code.append("Point(7) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox+lx, y=oy+ly, z=oz+lz, mesh_size=mesh_size_1))
#     code.append("Point(8) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox, y=oy+ly, z=oz+lz, mesh_size=mesh_size_1))
#     code.append("Line(1) = {1,2};")
#     code.append("Line(2) = {2,3};")
#     code.append("Line(3) = {3,4};")
#     code.append("Line(4) = {4,1};")
#     code.append("Line(5) = {5,6};")
#     code.append("Line(6) = {6,7};")
#     code.append("Line(7) = {7,8};")
#     code.append("Line(8) = {8,5};")
#     code.append("Line(9) = {5,1};")
#     code.append("Line(10) = {2,6};")
#     code.append("Line(11) = {7,3};")
#     code.append("Line(12) = {8,4};")
#     code.append("Line Loop(13) = { 7, 8, 5, 6 };")
#     code.append("Plane Surface(14) = {13};")
#     code.append("Line Loop(15) = {1, 2, 3, 4};")
#     code.append("Plane Surface(16) = {15};")
#     code.append("Line Loop(17) = {8, 9, -4, -12};")
#     code.append("Plane Surface(18) = {17};")
#     code.append("Line Loop(19) = {1, 10, -5, 9};")
#     code.append("Plane Surface(20) = {19};")
#     code.append("Line Loop(21) = {10, 6, 11, -2};")
#     code.append("Plane Surface(22) = {21};")
#     code.append("Line Loop(23) = {11, 3, -12, -7};")
#     code.append("Plane Surface(24) = {23};")
#     code.append("Surface Loop(25) = {14, 24, 22, 20, 16, 18};")
#     code.append("Volume(26) = {25};")
#     code2 = code[:] # this one is for auxiliary (coarse) patch
#     code2.append("Point(28) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox+lx/2, y=oy+ly/2, z=oz+lz/2, mesh_size=mesh_size_2))
#     code2.append("Point{28} In Volume{26};")
#     e = 1e-6 #### this part is to enforce periodicity conditions for the patch mes
#     code.append("back_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz+lz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code2.append("back_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz+lz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code.append("front_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+e))
#     code2.append("front_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+e))
#     code.append("left_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz-e,xmax=ox+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code2.append("left_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz-e,xmax=ox+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code.append("right_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox+lx-e,ymin=oy-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code2.append("right_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox+lx-e,ymin=oy-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code.append("down_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+e,zmax=oz+lz+e))
#     code2.append("down_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+e,zmax=oz+lz+e))
#     code.append("up_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy+ly-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code2.append("up_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy+ly-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code.append("Periodic Surface{ right_surface() } = { left_surface() } Translate{ "+str(lx)+",0,0 };")
#     code2.append("Periodic Surface{ right_surface() } = { left_surface() } Translate{ "+str(lx)+",0,0 };")
#     code.append("Periodic Surface{ up_surface() } = { down_surface() } Translate{ 0,"+str(ly)+",0 };")
#     code2.append("Periodic Surface{ up_surface() } = { down_surface() } Translate{ 0,"+str(ly)+",0 };")
#     code.append("Periodic Surface{ back_surface() } = { front_surface() } Translate{ 0,0,"+str(lz)+" };")
#     code2.append("Periodic Surface{ back_surface() } = { front_surface() } Translate{ 0,0,"+str(lz)+" };")
#
# #    geom = pygmsh.opencascade.Geometry(characteristic_length_min=mesh_size, characteristic_length_max=mesh_size,)
# #    geom = pygmsh.geo.Geometry()
#     geom = pygmsh.opencascade.Geometry()
#     geom2 = pygmsh.opencascade.Geometry()
#
#     # add raw code to geometry
#     geom.add_raw_code(code)
#     geom2.add_raw_code(code2)
#
#     # mesh
#     # points, cells, _, _, _ = geom.generate_mesh(verbose=verbose, extra_gmsh_arguments=["-optimize_netgen"])
#     # points, cells, _, _, _ = geom.generate_mesh(verbose=verbose, extra_gmsh_arguments=["-optimize","-algo","del3d","-clmin",str(mesh_size),"-clmax",str(mesh_size)])
#     mesh = geom.generate_mesh(verbose=verbose, extra_gmsh_arguments=["-3", "-optimize", "-algo", "del3d"])
#     points = mesh.points
#     cells = mesh.cells
#     connectivity = cells['tetra']
#     meshaux = geom2.generate_mesh(verbose=verbose, extra_gmsh_arguments=["-3", "-optimize", "-algo", "del3d"])
#     pointsaux = meshaux.points
#     cellsaux = meshaux.cells
#     connectivityaux = cellsaux['tetra']
#
#     # write gmsh/vtk file
#     if gmshFile is not None:
#         meshio.write_points_cells("{}_fin.msh".format(gmshFile), points, cells, file_format='gmsh22')
#         meshio.write_points_cells("{}_aux.msh".format(gmshFile), pointsaux, {'tetra': connectivityaux}, file_format='gmsh22')
#     if vtkFile is not None:
#         meshio.write_points_cells("{}_fin.vtk".format(vtkFile), points, {'tetra': connectivity}, file_format='vtk')
#         meshio.write_points_cells("{}_aux.vtk".format(vtkFile), pointsaux, {'tetra': connectivityaux}, file_format='vtk')
#
# ### TEST pour 1 translation de lx (ox = ox + lx) dans la direction x
# # on veut produire :
# ### 2 fichiers msh "fin" domain_fin_i.msh (et aussi domain_fin_i.vtk pour la visu)
# ### 2 fichiers msh "aux" domain_aux_i.msh (et aussi vtk pour la visu)
# ### 1 fichier msh "global" qui reunit les deux fichiers aux (et aussi vtk pour la visu)
#     points[:, 0] += lx # pour les fichiers "fin"
#
#     temppoints = copy.deepcopy(pointsaux)
#     pointsaux[:, 0] += lx #translate aux mesh
#     glob_points = numpy.concatenate((temppoints,pointsaux), axis = 0)  #create an array for global mesh (union of aux meshes)
#     tempconnec = copy.deepcopy(connectivityaux)
#     connectivityaux[:, :] += pointsaux.shape[0] #translate aux connectivity
#     glob_connectivity = numpy.concatenate((tempconnec,connectivityaux), axis = 0)  #create an array for global mesh (union of aux meshes)
#
#     # write gmsh/vtk file for second fine and aux mesh
#     if gmshFile is not None:
#         meshio.write_points_cells("{}_fin_2.msh".format(gmshFile), points, cells, file_format='gmsh22')
#         meshio.write_points_cells("{}_aux_2.msh".format(gmshFile), pointsaux, {'tetra': tempconnec}, file_format='gmsh22')
#     if vtkFile is not None:
#         meshio.write_points_cells("{}_fin_2.vtk".format(vtkFile), points, {'tetra': connectivity}, file_format='vtk')
#         meshio.write_points_cells("{}_aux_2.vtk".format(vtkFile), pointsaux, {'tetra': tempconnec}, file_format='vtk') # attention ici on ne decale pas la connectivité
#
# # now try to generate global mesh
# # its a three step process
# # first, make a list of a list of all nodes that appear more than once in glob_points.
# # second, replace each one of those "double" node by the smaller number in the connectivity (glob_connectivity). At this stage all those double nodes are now unlinked to any element.
# # third, remove the double nodes from the node list and modify the connectivity accordingly (most difficult step!)
#
#
#     print('Start to build GLOBAL mesh - step 1')
#     double = []
#     for i,node1 in enumerate(glob_points): # look at every point in the mesh
#         for j,node2 in enumerate(glob_points[i+1:]): #and check for existing node at the same place
#             if ((node1[0]==node2[0]) and (node1[1]==node2[1]) and (node1[2]==node2[2])):
#                 print('Finding double node of coordinates: ', i+1, '=',glob_points[i], j+i+2, '=',glob_points[j+i+1])
#                 double.append(i+1)
#                 double.append(j+i+2)
#
#
#     print('Start to build GLOBAL mesh - step 2')
#     #here we should replace the nodes written in the double list in the glob_connectivity
#     for node1,node2 in zip(double[0::2], double[1::2]):
#         for k,elem in enumerate(glob_connectivity):
#             if elem[0] == node2-1:
#                 print('Replacing double node ', node2, ' by ', node1, 'in element ', k+1, 'component ', 1)
#                 glob_connectivity[k][0] = node1-1
#             if elem[1] == node2-1:
#                 print('Replacing double node ', node2, ' by ', node1, 'in element ', k+1, 'component ', 2)
#                 glob_connectivity[k][1] = node1-1
#             if elem[2] == node2-1:
#                 print('Replacing double node ', node2, ' by ', node1, 'in element ', k+1, 'component ', 3)
#                 glob_connectivity[k][2] = node1-1
#             if elem[3] == node2-1:
#                 print('Replacing double node ', node2, ' by ', node1, 'in element ', k+1, 'component ', 4)
#                 glob_connectivity[k][3] = node1-1
#
#     print('Start to build GLOBAL mesh - step 3')
#     #here we should erase the double nodes written in the node list and shift -1 the glob_connectivity
#     toberemoved = []
#     for node1,node2 in zip(double[0::2], double[1::2]):
#         if len(toberemoved) == 0:
#             toberemoved.append(node2)
#         elif toberemoved[-1] != node2:
#             toberemoved.append(node2)
#     toberemoved.sort(reverse=True)
# #    print('toberemoved : ', toberemoved)
#     for node in toberemoved:
#         glob_points = numpy.delete(glob_points, node-1,0) # Point removing
#         for k,elem in enumerate(glob_connectivity):
#             if elem[0] > node-1:
#                 glob_connectivity[k][0] -= 1
#             if elem[1] > node-1:
#                 glob_connectivity[k][1] -= 1
#             if elem[2] > node-1:
#                 glob_connectivity[k][2] -= 1
#             if elem[3] > node-1:
#                 glob_connectivity[k][3] -= 1
#
#     meshio.write_points_cells("global.msh", glob_points, {'tetra': glob_connectivity}, file_format='gmsh22')
#     meshio.write_points_cells("global.vtk", glob_points, {'tetra': glob_connectivity}, file_format='vtk')
#
#
#     return
#
#
# def create8Patche(lengths, mesh_size_1, mesh_size_2, origin=[0., 0., 0.], verbose=False, gmshFile=None, vtkFile=None):
#     # NOT USED
#     import pygmsh
#     import meshio
#
#     lx, ly, lz = lengths
#     ox, oy, oz = origin
#
#     # We will switch the input arrays from zyx to xyz before passing them to pygmsh
#     lengths = lengths[::-1]
#     origin = origin[::-1]
#
#     # raw code
#     code = []
#
#     code.append("SetFactory(\"OpenCASCADE\");")
#     code.append("Mesh.RandomSeed = 0.5;")
#     code.append("Point(1) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox, y=oy, z=oz, mesh_size=mesh_size_1))
#     code.append("Point(2) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox+lx, y=oy, z=oz, mesh_size=mesh_size_1))
#     code.append("Point(3) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox+lx, y=oy+ly, z=oz, mesh_size=mesh_size_1))
#     code.append("Point(4) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox, y=oy+ly, z=oz, mesh_size=mesh_size_1))
#     code.append("Point(5) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox, y=oy, z=oz+lz, mesh_size=mesh_size_1))
#     code.append("Point(6) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox+lx, y=oy, z=oz+lz, mesh_size=mesh_size_1))
#     code.append("Point(7) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox+lx, y=oy+ly, z=oz+lz, mesh_size=mesh_size_1))
#     code.append("Point(8) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox, y=oy+ly, z=oz+lz, mesh_size=mesh_size_1))
#     code.append("Line(1) = {1,2};")
#     code.append("Line(2) = {2,3};")
#     code.append("Line(3) = {3,4};")
#     code.append("Line(4) = {4,1};")
#     code.append("Line(5) = {5,6};")
#     code.append("Line(6) = {6,7};")
#     code.append("Line(7) = {7,8};")
#     code.append("Line(8) = {8,5};")
#     code.append("Line(9) = {5,1};")
#     code.append("Line(10) = {2,6};")
#     code.append("Line(11) = {7,3};")
#     code.append("Line(12) = {8,4};")
#     code.append("Line Loop(13) = { 7, 8, 5, 6 };")
#     code.append("Plane Surface(14) = {13};")
#     code.append("Line Loop(15) = {1, 2, 3, 4};")
#     code.append("Plane Surface(16) = {15};")
#     code.append("Line Loop(17) = {8, 9, -4, -12};")
#     code.append("Plane Surface(18) = {17};")
#     code.append("Line Loop(19) = {1, 10, -5, 9};")
#     code.append("Plane Surface(20) = {19};")
#     code.append("Line Loop(21) = {10, 6, 11, -2};")
#     code.append("Plane Surface(22) = {21};")
#     code.append("Line Loop(23) = {11, 3, -12, -7};")
#     code.append("Plane Surface(24) = {23};")
#     code.append("Surface Loop(25) = {14, 24, 22, 20, 16, 18};")
#     code.append("Volume(26) = {25};")
#     code2 = code[:] # this one is for auxiliary (coarse) patch
#     code2.append("Point(28) = {{ {x}, {y},  {z}, {mesh_size} }};".format(x=ox+lx/2, y=oy+ly/2, z=oz+lz/2, mesh_size=mesh_size_2))
#     code2.append("Point{28} In Volume{26};")
#     e = 1e-6 #### this part is to enforce periodicity conditions for the patch mes
#     code.append("back_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz+lz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code2.append("back_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz+lz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code.append("front_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+e))
#     code2.append("front_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+e))
#     code.append("left_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz-e,xmax=ox+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code2.append("left_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz-e,xmax=ox+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code.append("right_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox+lx-e,ymin=oy-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code2.append("right_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox+lx-e,ymin=oy-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code.append("down_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+e,zmax=oz+lz+e))
#     code2.append("down_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+e,zmax=oz+lz+e))
#     code.append("up_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy+ly-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code2.append("up_surface() = Surface In BoundingBox{{{xmin},{ymin},{zmin},{xmax},{ymax},{zmax}}};".format(xmin=ox-e,ymin=oy+ly-e,zmin=oz-e,xmax=ox+lx+e,ymax=oy+ly+e,zmax=oz+lz+e))
#     code.append("Periodic Surface{ right_surface() } = { left_surface() } Translate{ "+str(lx)+",0,0 };")
#     code2.append("Periodic Surface{ right_surface() } = { left_surface() } Translate{ "+str(lx)+",0,0 };")
#     code.append("Periodic Surface{ up_surface() } = { down_surface() } Translate{ 0,"+str(ly)+",0 };")
#     code2.append("Periodic Surface{ up_surface() } = { down_surface() } Translate{ 0,"+str(ly)+",0 };")
#     code.append("Periodic Surface{ back_surface() } = { front_surface() } Translate{ 0,0,"+str(lz)+" };")
#     code2.append("Periodic Surface{ back_surface() } = { front_surface() } Translate{ 0,0,"+str(lz)+" };")
#
# #    geom = pygmsh.opencascade.Geometry(characteristic_length_min=mesh_size, characteristic_length_max=mesh_size,)
# #    geom = pygmsh.geo.Geometry()
#     geom = pygmsh.opencascade.Geometry()
#     geom2 = pygmsh.opencascade.Geometry()
#
#     # add raw code to geometry
#     geom.add_raw_code(code)
#     geom2.add_raw_code(code2)
#
#     # mesh
#     # points, cells, _, _, _ = geom.generate_mesh(verbose=verbose, extra_gmsh_arguments=["-optimize_netgen"])
#     # points, cells, _, _, _ = geom.generate_mesh(verbose=verbose, extra_gmsh_arguments=["-optimize","-algo","del3d","-clmin",str(mesh_size),"-clmax",str(mesh_size)])
#     mesh = geom.generate_mesh(verbose=verbose, extra_gmsh_arguments=["-3", "-optimize", "-algo", "del3d"])
#     points = mesh.points
#     cells = mesh.cells
#     connectivity = cells['tetra']
#     meshaux = geom2.generate_mesh(verbose=verbose, extra_gmsh_arguments=["-3", "-optimize", "-algo", "del3d"])
#     pointsaux = meshaux.points
#     cellsaux = meshaux.cells
#     connectivityaux = cellsaux['tetra']
#
# ### TEST pour 7 translations
# # on veut produire :
# ### 8 fichiers msh "fin" domain_fin_i.msh (et aussi domain_fin_i.vtk pour la visu)
# ### 8 fichiers msh "aux" domain_aux_i.msh (et aussi vtk pour la visu)
# ### 1 fichier msh "global" qui reunit les deux fichiers aux (et aussi vtk pour la visu)
#     shifts = [[0, 0, 0], [lx, 0, 0], [0, ly, 0], [-lx, 0, 0], [0, -ly, lz], [lx, 0, 0], [0, ly, 0], [-lx, 0, 0]]
#     glob_points = copy.deepcopy(pointsaux)
#     glob_connectivity = copy.deepcopy(connectivityaux)
#     connectivityaux_init = copy.deepcopy(connectivityaux)
#     for i,shift in enumerate(shifts):
#         points[:, 0] += shift[0] # pour les fichiers "fin"
#         points[:, 1] += shift[1] # pour les fichiers "fin"
#         points[:, 2] += shift[2] # pour les fichiers "fin"
#
#         pointsaux[:, 0] += shift[0] #translate aux mesh
#         pointsaux[:, 1] += shift[1] #translate aux mesh
#         pointsaux[:, 2] += shift[2] #translate aux mesh
#         glob_points = numpy.concatenate((glob_points,copy.deepcopy(pointsaux)), axis = 0)  #create an array for global mesh (union of aux meshes)
#         connectivityaux[:, :] += pointsaux.shape[0]
#         glob_connectivity = numpy.concatenate((glob_connectivity, copy.deepcopy(connectivityaux)), axis = 0)
#         # write gmsh/vtk file for fine and aux mesh
#         if gmshFile is not None:
#             meshio.write_points_cells("patch_fin_"+str(i+1)+".msh", points, cells, file_format='gmsh22')
#             meshio.write_points_cells("patch_aux_"+str(i+1)+".msh", pointsaux, {'tetra': connectivityaux_init}, file_format='gmsh22')
#         if vtkFile is not None:
#             meshio.write_points_cells("patch_fin_"+str(i+1)+".vtk", points, {'tetra': connectivity}, file_format='vtk')
#             meshio.write_points_cells("patch_aux_"+str(i+1)+".vtk", pointsaux, {'tetra': connectivityaux_init}, file_format='vtk') # attention ici on ne decale pas la connectivité
#
# # now try to generate global mesh
# # its a three step process
# # first, make a list of a list of all nodes that appear more than once in glob_points.
# # second, replace each one of those "double" node by the smaller number in the connectivity (glob_connectivity). At this stage all those double nodes are now unlinked to any element.
# # third, remove the double nodes from the node list and modify the connectivity accordingly (most difficult step!)
#
#
#     print('Start to build GLOBAL mesh - step 1')
#     double = []
#     for i,node1 in enumerate(glob_points): # look at every point in the mesh
#         for j,node2 in enumerate(glob_points[i+1:]): #and check for existing node at the same place
#             if ((node1[0]==node2[0]) and (node1[1]==node2[1]) and (node1[2]==node2[2])):
#                 print('Finding double node of coordinates: ', i+1, '=',glob_points[i], j+i+2, '=',glob_points[j+i+1])
#                 double.append(i+1)
#                 double.append(j+i+2)
#
#
#     print('Start to build GLOBAL mesh - step 2')
#     #here we should replace the nodes written in the double list in the glob_connectivity
#     for node1,node2 in zip(double[0::2], double[1::2]):
#         for k,elem in enumerate(glob_connectivity):
#             if elem[0] == node2-1:
#                 print('Replacing double node ', node2, ' by ', node1, 'in element ', k+1, 'component ', 1)
#                 glob_connectivity[k][0] = node1-1
#             if elem[1] == node2-1:
#                 print('Replacing double node ', node2, ' by ', node1, 'in element ', k+1, 'component ', 2)
#                 glob_connectivity[k][1] = node1-1
#             if elem[2] == node2-1:
#                 print('Replacing double node ', node2, ' by ', node1, 'in element ', k+1, 'component ', 3)
#                 glob_connectivity[k][2] = node1-1
#             if elem[3] == node2-1:
#                 print('Replacing double node ', node2, ' by ', node1, 'in element ', k+1, 'component ', 4)
#                 glob_connectivity[k][3] = node1-1
#
# #   print('Start to build GLOBAL mesh - step 3')
# #   #here we should erase the double nodes written in the node list and shift -1 the glob_connectivity
#     toberemoved = []
#     for node1,node2 in zip(double[0::2], double[1::2]):
#         if len(toberemoved) == 0:
#             toberemoved.append(node2)
#         elif toberemoved[-1] != node2:
#             toberemoved.append(node2)
#     toberemoved.sort(reverse=True)
# #    print('toberemoved : ', toberemoved)
#     for node in toberemoved:
#         glob_points = numpy.delete(glob_points, node-1,0) # Point removing
#         for k,elem in enumerate(glob_connectivity):
#             if elem[0] > node-1:
#                 glob_connectivity[k][0] -= 1
#             if elem[1] > node-1:
#                 glob_connectivity[k][1] -= 1
#             if elem[2] > node-1:
#                 glob_connectivity[k][2] -= 1
#             if elem[3] > node-1:
#                 glob_connectivity[k][3] -= 1
#
#     meshio.write_points_cells("global.msh", glob_points, {'tetra': glob_connectivity}, file_format='gmsh22')
#     meshio.write_points_cells("global.vtk", glob_points, {'tetra': glob_connectivity}, file_format='vtk')
#
#
#     return


def rankPoints(points, neighbourRadius=20, verbose=True):
    """
    This function ranks an array of points around the top point

    Parameters
    ----------
        points: numpy array N x 3
            Coordinates (zyx) of the points

        neighbourRadius: float, optional
            Distance from the current point to include neighbours
            If no neighbour is found, then the closest point is taken
            Default: 20

    Returns
    -------
        pointsRanked: numpy array N x 3
            Coordinates (zyx) of the ranked points

        rowNumbers : 1D numpy array N of ints
            Reorganised row numbers from input

    Note
    -----
        Based on https://gricad-gitlab.univ-grenoble-alpes.fr/DVC/pt4d
    """

    rowNumbers = numpy.zeros((points.shape[0]), dtype=int)

    points = numpy.array([points[:, 0], points[:, 1], points[:, 2], numpy.arange(points.shape[0])]).T

    # counters
    p = pR = 0

    # create the ranked array, first ranked point is the top point of the input array
    pointsRanked = numpy.zeros_like(points)
    pointsRanked[0] = points[0]
    # remove ranked point from input array
    points = numpy.delete(points, 0, 0)

    # Create progressbar
    numberOfPoints = pointsRanked.shape[0]
    if verbose:
        widgets = [
            progressbar.FormatLabel(""),
            " ",
            progressbar.Bar(),
            " ",
            progressbar.AdaptiveETA(),
        ]
        pbar = progressbar.ProgressBar(widgets=widgets, maxval=numberOfPoints)
        pbar.start()

    while points.shape[0] >= 1:
        # Try to see how many points can be found around the current point based on the given radius
        treeCoord = scipy.spatial.KDTree(points[:, 0:3])
        indRadius = numpy.array(treeCoord.query_ball_point(pointsRanked[pR, 0:3], neighbourRadius))
        indRadius = indRadius[numpy.argsort(indRadius)]

        # if no points inside the given radius, just find the closest point
        if len(indRadius) < 1:
            distance, ind = treeCoord.query(pointsRanked[pR, 0:3], k=1)
            indRadius = numpy.array([ind])

        # fill in the ranked array with the point(s) found
        pointsRanked[p + 1 : p + 1 + len(indRadius)] = points[indRadius]
        for qn, q in enumerate(range(p + 1, p + 1 + len(indRadius))):
            rowNumbers[int(points[indRadius[qn], -1])] = q
        # remove ranked point(s) from input array
        points = numpy.delete(points, indRadius, 0)

        # update counters
        p += len(indRadius)
        pR += 1

        if verbose:
            widgets[0] = progressbar.FormatLabel("{:.1f}%%".format((p / numberOfPoints) * 100))
            pbar.update(pR)

    return pointsRanked[:, 0:3], rowNumbers

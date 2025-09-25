import os, shutil, tempfile, unittest, warnings, shutil as _sh
os.environ.setdefault("JUPYTER_PLATFORM_DIRS","1")
warnings.filterwarnings("ignore")
TMP=tempfile.mkdtemp(prefix="pyiron_stack_")

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from pyiron_atomistics import Project
        cls.pr=Project(TMP)
        cls.struct=cls.pr.create.structure.bulk("Cu",a=3.6,cubic=True)

    def test_project_ok(self):
        self.assertTrue(os.path.isdir(self.pr.path))
        self.assertTrue(hasattr(self.pr,"job_table"))

    def test_neighbors_and_roundtrip(self):
        s = self.struct.copy()
        nb = s.get_neighbors(num_neighbors=12)
        self.assertTrue(len(nb.indices) > 0)

        d = s.to_dict()
        s2 = s.__class__.from_dict(d)

        self.assertEqual(len(s), len(s2))
        self.assertEqual(s.get_chemical_formula(), s2.get_chemical_formula())

    def test_lammps_persist(self):
        j=self.pr.create_job("Lammps","lmp_smoke")
        j.structure=self.struct
        j.input.control["units"]="lj"
        j.save()
        self.assertTrue(os.path.exists(j.project_hdf5.file_name))
        j2=self.pr.load(j.job_id)
        self.assertEqual(j2.name,"lmp_smoke")

    def test_vasp_persist_or_skip(self):
        v=_sh.which("vasp_std") or _sh.which("vasp_gam")
        p=os.environ.get("VASP_PP_PATH")
        if not (v and p and os.path.isdir(p)):
            self.skipTest("VASP executable/potentials not configured")
        j=self.pr.create_job("Vasp","vasp_smoke")
        j.structure=self.struct
        j.input.incar.update(dict(ENCUT=250,ISMEAR=0,SIGMA=0.1,EDIFF=1e-5,IBRION=-1,NSW=0))
        j.input.kpoints["mesh"]=[1,1,1]
        j.save()
        self.assertTrue(os.path.exists(j.project_hdf5.file_name))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TMP,ignore_errors=True)

if __name__=="__main__": unittest.main(verbosity=2)

from qgis.testing import unittest

from modelbaker.iliwrapper.ili2dbutils import get_all_modeldir_in_path
from tests.utils import testdata_path


class TestILI2DBUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.parent_dir = testdata_path("")
        cls.ilimodels = testdata_path("ilimodels")
        cls.invalid_ilimodels = testdata_path("invalid_ilimodels")
        cls.ciaf_ladm = testdata_path("ilimodels/CIAF_LADM")
        cls.empty = testdata_path("ilimodels/subparent_dir/empty")
        cls.hidden = testdata_path("ilimodels/subparent_dir/.hidden")
        cls.not_hidden = testdata_path("ilimodels/subparent_dir/not_hidden")
        cls.ilirepo_24_additional_local_ili_files = testdata_path(
            "ilirepo/24/additional_local_ili_files"
        )
        cls.ilirepo_usabilityhub_additional_local_ili_files = testdata_path(
            "ilirepo/usabilityhub/additional_local_ili_files"
        )
        cls.not_modeldir = testdata_path("xtf")

    def test_parse_subdirs_in_parent_dir(self):
        modeldirs = get_all_modeldir_in_path(self.parent_dir)  # Parent folder: testdata
        expected_dirs = [
            self.parent_dir,
            self.ilimodels,
            self.invalid_ilimodels,
            self.ciaf_ladm,
            self.hidden,
            self.not_hidden,
            self.ilirepo_24_additional_local_ili_files,
            self.ilirepo_usabilityhub_additional_local_ili_files,
        ]
        assert sorted(expected_dirs) == sorted(modeldirs.split(";"))

    def test_parse_subdirs_in_hidden_dir(self):
        modeldirs = get_all_modeldir_in_path(self.hidden)
        assert self.hidden == modeldirs

    def test_parse_subdirs_in_not_hidden_dir(self):
        modeldirs = get_all_modeldir_in_path(self.not_hidden)
        assert self.not_hidden == modeldirs

    def test_parse_mixed_dir(self):
        subparent_dir = testdata_path("ilimodels/subparent_dir")
        modeldirs = get_all_modeldir_in_path(subparent_dir)
        expected_dirs = [subparent_dir, self.hidden, self.not_hidden]
        assert sorted(expected_dirs) == sorted(modeldirs.split(";"))

    def test_parse_subdirs_in_empty_dir(self):
        modeldirs = get_all_modeldir_in_path(self.empty)
        assert self.empty == modeldirs

    def test_parse_subdirs_in_not_model_dir(self):
        modeldirs = get_all_modeldir_in_path(self.not_modeldir)
        assert self.not_modeldir == modeldirs

    def test_parse_special_strings(self):
        modeldirs = get_all_modeldir_in_path("%XTF_DIR")
        assert "%XTF_DIR" == modeldirs

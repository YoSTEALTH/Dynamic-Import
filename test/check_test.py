from dynamic_import.check import IMPORTER_CALLED, importer_called, exclude_directory

# TODO


def test_imp():
    assert isinstance(IMPORTER_CALLED, dict)

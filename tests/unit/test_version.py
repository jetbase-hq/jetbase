import os
import tempfile

from jetbase.engine.version import (
    _get_version_key_from_filename,
    get_migration_filepaths_by_version,
)


def test_get_version_key_from_filename():
    assert _get_version_key_from_filename("V1__my_description.sql") == "1"
    assert _get_version_key_from_filename("V1_1__my_description.sql") == "1.1"
    assert _get_version_key_from_filename("V1.1__my_description.sql") == "1.1"
    assert _get_version_key_from_filename("V2_1.5__another_mixed.sql") == "2.1.5"


def test_get_migration_filepaths_by_version():
    with tempfile.TemporaryDirectory() as temp_dir:
        file1 = os.path.join(temp_dir, "V1_2_0__add_feature.sql")
        file2 = os.path.join(temp_dir, "V1_0_0__initial_setup.sql")
        os.makedirs(os.path.join(temp_dir, "release2"))
        file3 = os.path.join(temp_dir, "release2", "V2_0_0__major_update.sql")
        file4 = os.path.join(temp_dir, "not_a_sql_file.txt")
        file5 = os.path.join(temp_dir, "V11__not_str_ordering.sql")

        with open(file1, "w") as f:
            f.write("-- SQL for initial setup")
        with open(file2, "w") as f:
            f.write("-- SQL for adding feature")
        with open(file3, "w") as f:
            f.write("-- SQL for major update")
        with open(file4, "w") as f:
            f.write("This is not a SQL file.")
        with open(file5, "w") as f:
            f.write("-- SQL for version 11")

        versions = get_migration_filepaths_by_version(directory=temp_dir)
        expected_versions = {
            "1.0.0": file2,
            "1.2.0": file1,
            "2.0.0": file3,
            "11": file5,
        }
        assert versions == expected_versions

        versions = get_migration_filepaths_by_version(
            directory=temp_dir, version_to_start_from="1.2.0"
        )
        expected_versions = {
            "1.2.0": file1,
            "2.0.0": file3,
            "11": file5,
        }
        assert versions == expected_versions

        versions = get_migration_filepaths_by_version(
            directory=temp_dir, end_version="1.2.0"
        )
        expected_versions = {
            "1.0.0": file2,
            "1.2.0": file1,
        }
        assert versions == expected_versions

        versions = get_migration_filepaths_by_version(
            directory=temp_dir, version_to_start_from="1.2.0", end_version="2.0.0"
        )
        expected_versions = {
            "1.2.0": file1,
            "2.0.0": file3,
        }
        assert versions == expected_versions

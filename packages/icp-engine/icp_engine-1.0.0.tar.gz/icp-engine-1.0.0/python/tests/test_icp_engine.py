import bs4
import json
import pathlib
import platform
import pytest

import icp_engine


def test_constants():
    # version
    assert isinstance(icp_engine.version_major, int)
    assert isinstance(icp_engine.version_minor, int)
    assert isinstance(icp_engine.version_patch, int)

    assert isinstance(icp_engine.icp_version, str)
    assert icp_engine.icp_version
    assert isinstance(icp_engine.icplib_version, str)
    assert icp_engine.icplib_version

    # validate icp database
    assert isinstance(icp_engine.database_path, pathlib.Path)
    assert icp_engine.database_path.exists()
    assert icp_engine.database_path.is_dir()

    # validate scan flags
    assert icp_engine._ICPFlags.Deepscan.value == icp_engine.ScanFlags.DEEP_SCAN
    assert icp_engine._ICPFlags.HeuristicScan.value == icp_engine.ScanFlags.HEURISTIC_SCAN
    assert icp_engine._ICPFlags.AlltypesScan.value == icp_engine.ScanFlags.ALL_TYPES_SCAN
    assert icp_engine._ICPFlags.RecursiveScan.value == icp_engine.ScanFlags.RECURSIVE_SCAN
    assert icp_engine._ICPFlags.Verbose.value == icp_engine.ScanFlags.VERBOSE_FLAG
    assert icp_engine._ICPFlags.ResultAsXml.value == icp_engine.ScanFlags.RESULT_AS_XML
    assert icp_engine._ICPFlags.ResultAsJson.value == icp_engine.ScanFlags.RESULT_AS_JSON
    assert icp_engine._ICPFlags.ResultAsTsv.value == icp_engine.ScanFlags.RESULT_AS_TSV
    assert icp_engine._ICPFlags.ResultAsCsv.value == icp_engine.ScanFlags.RESULT_AS_CSV
    # validate no new flag was added and not test
    assert sorted([x for x in dir(icp_engine._ICPFlags) if not x.startswith("__")]) == sorted(
        [
            "AlltypesScan",
            "Deepscan",
            "HeuristicScan",
            "RecursiveScan",
            "ResultAsCsv",
            "ResultAsJson",
            "ResultAsTsv",
            "ResultAsXml",
            "Verbose",
        ]
    )


@pytest.fixture
def target_binary():
    return (
        pathlib.Path("c:/windows/system32/winver.exe")
        if platform.system() == "Windows"
        else pathlib.Path("/bin/ls")
    )


def test_scan_memory(target_binary: pathlib.Path):
    raw_data = target_binary.read_bytes()
    res = icp_engine.scan_memory(
        bytearray(raw_data),
        icp_engine.ScanFlags.DEEP_SCAN,
    )
    assert res
    assert isinstance(res, str)

    lines = res.splitlines()
    assert len(lines)

    if platform.system() == "Windows":
        assert lines[0] == "PE64"
    elif platform.system() == "Linux":
        assert lines[0] == "ELF64"


def test_scan_basic(target_binary: pathlib.Path):
    res = icp_engine.scan_file(
        target_binary,
        icp_engine.ScanFlags.DEEP_SCAN,
    )
    assert res
    assert isinstance(res, str)

    lines = res.splitlines()
    assert len(lines)

    if platform.system() == "Windows":
        assert lines[0] == "PE64"
    elif platform.system() == "Linux":
        assert lines[0] == "ELF64"


def test_scan_export_format_json(target_binary: pathlib.Path):
    res = icp_engine.scan_file(
        target_binary,
        icp_engine.ScanFlags.DEEP_SCAN | icp_engine.ScanFlags.RESULT_AS_JSON,
    )
    assert res

    js = json.loads(res)
    assert len(js["detects"])
    if platform.system() == "Windows":
        assert js["detects"][0]["filetype"] == "PE64"
    elif platform.system() == "Linux":
        assert js["detects"][0]["filetype"] == "ELF64"


def test_scan_export_format_xml(target_binary: pathlib.Path) -> None:
    res = icp_engine.scan_file(
        target_binary,
        icp_engine.ScanFlags.DEEP_SCAN | icp_engine.ScanFlags.RESULT_AS_XML,
    )
    assert res
    xml = bs4.BeautifulSoup(res, "xml")
    assert xml.Result
    if platform.system() == "Windows":
        assert hasattr(xml.Result, "PE64")
        assert xml.Result.PE64["filetype"] == "PE64"
    elif platform.system() == "Linux":
        assert hasattr(xml.Result, "ELF64")
        assert xml.Result.ELF64["filetype"] == "ELF64"


def test_scan_export_format_csv(target_binary: pathlib.Path):
    CSV_DELIMITER = ";"
    res = icp_engine.scan_file(
        target_binary,
        icp_engine.ScanFlags.DEEP_SCAN | icp_engine.ScanFlags.RESULT_AS_CSV,
    )
    assert res
    assert len(res.splitlines()) == 1
    assert len(res.split(CSV_DELIMITER)) == 5


def test_scan_export_format_tsv(target_binary: pathlib.Path):
    res = icp_engine.scan_file(
        target_binary,
        icp_engine.ScanFlags.DEEP_SCAN | icp_engine.ScanFlags.RESULT_AS_TSV,
    )
    assert res

    lines = res.splitlines()
    assert len(lines)

    if platform.system() == "Windows":
        assert lines[0] == "PE64"
    elif platform.system() == "Linux":
        assert lines[0] == "ELF64"


def test_basic_databases():
    for db in icp_engine.databases():
        assert isinstance(db, pathlib.Path)
        assert db.exists()
        assert db.is_file()

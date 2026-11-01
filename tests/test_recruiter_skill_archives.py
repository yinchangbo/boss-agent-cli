"""验证一条命令产出两种压缩包、校验文件，以及失败时保留已有成品。"""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import pytest


@pytest.fixture
def packager():
	path = Path(__file__).resolve().parents[1] / "scripts/package_recruiter_skill.py"
	spec = importlib.util.spec_from_file_location("package_recruiter_archives", path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


@pytest.fixture
def skill(tmp_path):
	root = tmp_path / "构建 空格" / "boss-recruiter"
	root.mkdir(parents=True)
	(root / "SKILL.md").write_text("# 测试技能\n", encoding="utf-8")
	(root / "说明 & 空格.txt").write_text("不依赖系统 Python。", encoding="utf-8")
	(root / "runtime").mkdir()
	(root / "runtime/data.bin").write_bytes(bytes(range(256)) * 100)
	return root


def test_find_seven_zip_explicit_path_and_missing_path(packager, tmp_path, monkeypatch):
	executable = tmp_path / "Tools 空格/7z.exe"
	executable.parent.mkdir()
	executable.touch()
	assert packager.find_seven_zip(executable) == executable.resolve()
	monkeypatch.setattr(packager.shutil, "which", lambda name: str(executable))
	with pytest.raises(FileNotFoundError, match="指定的"):
		packager.find_seven_zip(tmp_path / "missing.exe")


def test_find_seven_zip_from_path(packager, tmp_path, monkeypatch):
	executable = tmp_path / "7zz"
	executable.touch()
	monkeypatch.setattr(packager.shutil, "which", lambda name: str(executable) if name == "7zz" else None)
	assert packager.find_seven_zip() == executable.resolve()


def test_find_seven_zip_from_program_files(packager, tmp_path, monkeypatch):
	monkeypatch.setattr(packager.shutil, "which", lambda name: None)
	for key in ("ProgramW6432", "ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
		monkeypatch.delenv(key, raising=False)
	monkeypatch.setenv("ProgramFiles", str(tmp_path))
	executable = tmp_path / "7-Zip/7z.exe"
	executable.parent.mkdir()
	executable.touch()
	assert packager.find_seven_zip() == executable.resolve()
	executable.unlink()
	with pytest.raises(FileNotFoundError, match="尚未开始构建"):
		packager.find_seven_zip()


@pytest.mark.skipif(os.name != "nt", reason="Windows 构建入口")
def test_missing_seven_zip_stops_before_download(packager, monkeypatch):
	monkeypatch.setattr(sys, "argv", ["package_recruiter_skill.py", "--seven-zip", "missing-7z.exe"])
	monkeypatch.setattr(packager, "download_python", lambda *args: pytest.fail("缺少 7-Zip 时不应下载 Python"))
	with pytest.raises(SystemExit) as error:
		packager.main()
	assert error.value.code == 2


def test_seven_zip_refuses_existing_archive(packager, skill, tmp_path):
	archive = tmp_path / "previous.7z"
	archive.write_bytes(b"previous")
	with pytest.raises(FileExistsError, match="拒绝增量更新"):
		packager.write_seven_zip(skill, archive, Path("not-used.exe"), dict(os.environ))
	assert archive.read_bytes() == b"previous"


@pytest.mark.parametrize("failed_step", ["verify_portable_zip", "write_seven_zip"])
def test_failure_preserves_all_previous_outputs(packager, skill, tmp_path, monkeypatch, failed_step):
	output = tmp_path / "output"
	output.mkdir()
	names = [
		"boss-recruiter.zip",
		"boss-recruiter.7z",
		"boss-recruiter.zip.sha256",
		"boss-recruiter.7z.sha256",
		"boss-recruiter.validation.json",
	]
	for name in names:
		(output / name).write_bytes(b"previous-good-output")

	def fake_verify(archive, report, env):
		report.write_text(json.dumps({"passed": True}), encoding="utf-8")

	def fail(*args):
		raise subprocess.CalledProcessError(2, failed_step)

	monkeypatch.setattr(packager, "verify_portable_zip", fake_verify)
	monkeypatch.setattr(packager, failed_step, fail)
	with pytest.raises(subprocess.CalledProcessError):
		packager.package_and_publish(skill, output, Path("not-used.exe"), dict(os.environ))
	assert {p.name: p.read_bytes() for p in output.iterdir()} == {name: b"previous-good-output" for name in names}


def test_real_seven_zip_roundtrip_and_output_checksums(packager, skill, tmp_path, monkeypatch):
	try:
		seven_zip = packager.find_seven_zip()
	except FileNotFoundError:
		pytest.skip("此集成测试需要本机 7-Zip")
	originals = {p.relative_to(skill).as_posix(): p.read_bytes() for p in skill.rglob("*") if p.is_file()}

	def verify_fixture_zip(archive, report, env):
		# 此测试验证压缩流水线；完整 Python/浏览器验收由专用脚本负责。
		with ZipFile(archive) as bundle:
			assert bundle.testzip() is None
			assert {n: bundle.read(n) for n in bundle.namelist()} == {
				"boss-recruiter/" + name: content for name, content in originals.items()
			}
		report.write_text(json.dumps({"passed": True, "checks": ["fixture_zip"]}), encoding="utf-8")

	monkeypatch.setattr(packager, "verify_portable_zip", verify_fixture_zip)
	output = tmp_path / "output"
	packager.package_and_publish(skill, output, seven_zip, dict(os.environ))
	assert len(list(output.iterdir())) == 5
	report = json.loads((output / "boss-recruiter.validation.json").read_text(encoding="utf-8"))
	for name in ("boss-recruiter.zip", "boss-recruiter.7z"):
		archive = output / name
		assert report["archives"][name] == {"sha256": packager.sha256(archive), "size_bytes": archive.stat().st_size}
		assert (
			archive.with_suffix(archive.suffix + ".sha256").read_text(encoding="ascii")
			== f"{packager.sha256(archive)}  {name}\n"
		)
	assert report["seven_zip_integrity_passed"] is True
	unpacked = tmp_path / "解压 空格"
	subprocess.run(
		[str(seven_zip), "x", str(output / "boss-recruiter.7z"), f"-o{unpacked}", "-y"], check=True, capture_output=True
	)
	assert {
		p.relative_to(unpacked / "boss-recruiter").as_posix(): p.read_bytes()
		for p in (unpacked / "boss-recruiter").rglob("*")
		if p.is_file()
	} == originals

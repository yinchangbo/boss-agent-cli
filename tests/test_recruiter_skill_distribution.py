"""验证 Skill 分发不携带开发环境，安装不再追溯作者的源码目录。"""

import importlib.util
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_script(path):
	spec = importlib.util.spec_from_file_location(path.stem, path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def test_archive_excludes_environment_and_business_data(tmp_path):
	packager = load_script(ROOT / "scripts/package_recruiter_skill.py")
	skill = tmp_path / "boss-recruiter"
	required = [
		"SKILL.md",
		"agents/openai.yaml",
		"references/recruiter-cli.md",
		"scripts/boss.py",
		"scripts/setup_cli.py",
		"assets/boss_agent_cli-1-py3-none-any.whl",
	]
	for name in [*required, ".venv/pyvenv.cfg", "candidates.json", "scripts/__pycache__/boss.pyc"]:
		path = skill / name
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_text("测试", encoding="utf-8")
	archive = tmp_path / "skill.zip"
	packager.write_archive(skill, skill / required[-1], archive)
	with ZipFile(archive) as zipped:
		assert set(zipped.namelist()) == {f"boss-recruiter/{name}" for name in required}


def test_setup_installs_bundled_wheel_outside_repository(tmp_path, monkeypatch):
	setup = load_script(ROOT / ".agents/skills/boss-recruiter/scripts/setup_cli.py")
	skill = tmp_path / "独立 Skill"
	wheel = skill / "assets/boss_agent_cli-1-py3-none-any.whl"
	wheel.parent.mkdir(parents=True)
	wheel.touch()
	monkeypatch.setattr(setup, "__file__", str(skill / "scripts/setup_cli.py"))
	monkeypatch.setattr(sys, "argv", ["setup_cli.py"])
	monkeypatch.setattr(setup.venv.EnvBuilder, "create", lambda *args: None)
	calls = []
	monkeypatch.setattr(setup.subprocess, "run", lambda command, **kwargs: calls.append(command))
	assert setup.main() == 0
	assert calls[0][-1] == str(wheel)
	assert "--editable" not in calls[0]


@pytest.mark.parametrize("count", [0, 2])
def test_missing_or_ambiguous_wheel_fails_before_install(tmp_path, monkeypatch, count):
	setup = load_script(ROOT / ".agents/skills/boss-recruiter/scripts/setup_cli.py")
	assets = tmp_path / "assets"
	assets.mkdir()
	for index in range(count):
		(assets / f"boss_agent_cli-{index}-py3-none-any.whl").touch()
	monkeypatch.setattr(setup, "__file__", str(tmp_path / "scripts/setup_cli.py"))
	monkeypatch.setattr(sys, "argv", ["setup_cli.py"])
	with pytest.raises(SystemExit) as error:
		setup.main()
	assert error.value.code == 2
	assert not (tmp_path / ".venv").exists()

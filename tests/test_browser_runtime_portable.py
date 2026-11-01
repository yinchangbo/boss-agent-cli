"""保证浏览器预检与 Patchright 实际使用的缓存目录一致。"""

from pathlib import Path

from boss_agent_cli.services import browser_runtime


def test_explicit_browser_path_excludes_system_caches(tmp_path, monkeypatch):
	selected = tmp_path / "便携 浏览器"
	monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(selected))
	monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "other-cache"))
	assert browser_runtime.patchright_browser_cache_dirs() == [selected.resolve()]
	assert browser_runtime.installed_patchright_chromium_dirs() == []


def test_relative_browser_path_uses_init_cwd(tmp_path, monkeypatch):
	monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", "browsers")
	monkeypatch.setenv("INIT_CWD", str(tmp_path))
	assert browser_runtime.patchright_browser_cache_dirs() == [(tmp_path / "browsers").resolve()]


def test_zero_browser_path_uses_package_local_cache(monkeypatch):
	import patchright

	monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", "0")
	expected = Path(patchright.__file__).resolve().parent / "driver/package/.local-browsers"
	assert browser_runtime.patchright_browser_cache_dirs() == [expected]


def test_wizard_expands_browser_cache_before_revision_check(tmp_path, monkeypatch):
	from boss_agent_cli.wizard.preflight import _browser_kernel_status

	monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))
	monkeypatch.setattr(browser_runtime, "patchright_chromium_revision", lambda: "1248")
	for name in ("chromium-1248", "chromium_headless_shell-1248"):
		(tmp_path / name).mkdir()
	(tmp_path / "chromium-9999").touch()
	assert len(browser_runtime.installed_patchright_chromium_dirs()) == 2
	assert _browser_kernel_status()[0] == "ok"

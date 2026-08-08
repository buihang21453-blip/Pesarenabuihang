from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent


def test_room_detail_is_orchestrator_not_monolith():
    text = (ROOT / "templates/room_detail.html").read_text(encoding="utf-8")
    assert len(text.splitlines()) < 100
    for part in (
        "room/_topbar.html", "room/_host_card.html", "room/_center_stage.html",
        "room/_guest_card.html", "room/_side_rail.html", "room/_bottom_modes_history.html",
        "room/_extra_controls.html", "room/_action_modal.html",
        "room/scripts/_room_runtime.html", "room/scripts/_room_chat.html", "room/scripts/_room_dialogs.html",
    ):
        assert part in text
        assert (ROOT / "templates" / part).exists()


def test_style_css_is_compatibility_entrypoint():
    text = (ROOT / "static/style.css").read_text(encoding="utf-8")
    assert len(text.splitlines()) < 30
    for idx in range(1, 7):
        assert f"css/legacy/0{idx}-" in text
    assert len(list((ROOT / "static/css/legacy").glob("*.css"))) == 6


def test_app_core_is_extracted_and_compiles_ast():
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    ast.parse(app_text)
    assert len(app_text.splitlines()) < 4000
    for name in (
        "achievements.py", "rank_team_service.py", "room_runtime.py", "user_repository.py",
        "match_repository.py", "social_runtime.py", "matchmaking_runtime.py",
    ):
        path = ROOT / "modules/core" / name
        assert path.exists()
        ast.parse(path.read_text(encoding="utf-8"))


def test_logging_module_and_docs_exist():
    logging_file = ROOT / "modules/observability/app_logging.py"
    text = logging_file.read_text(encoding="utf-8")
    assert "X-Request-ID" in text
    assert "slow_request" in text
    assert "uncaught_exception" in text
    assert "RotatingFileHandler" in text
    assert (ROOT / "project_docs/LOGGING_GUIDE.md").exists()

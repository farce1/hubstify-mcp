import pytest

import app.config
from app.hubstaff.errors import HubstaffAuthError
from app.mcp.context import build_context


async def test_build_context_missing_token_error_names_env_var(monkeypatch, tmp_path):
    # Exercise the real composition root: settings -> TokenManager -> client -> repo.
    monkeypatch.setattr(app.config.settings, "hubstaff_personal_access_token", "")
    monkeypatch.setattr(app.config.settings, "hubstaff_token_store", tmp_path / "tokens.json")
    context = build_context()
    with pytest.raises(HubstaffAuthError, match="HUBSTAFF_PERSONAL_ACCESS_TOKEN"):
        await context.users.get_current_user()

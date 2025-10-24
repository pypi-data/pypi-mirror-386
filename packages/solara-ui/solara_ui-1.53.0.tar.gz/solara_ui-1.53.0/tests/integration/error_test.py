from pathlib import Path

import playwright
import playwright.sync_api

app_path = Path(__file__).parent / "testapp.py"


def test_error_in_render(page_session: playwright.sync_api.Page, solara_server, solara_app, extra_include_path):
    with extra_include_path(app_path.parent), solara_app("testapp:clickboom"):
        page_session.goto(solara_server.base_url)
        page_session.locator("text=Boom").click()
        page_session.locator("text=I crash on 1").wait_for()

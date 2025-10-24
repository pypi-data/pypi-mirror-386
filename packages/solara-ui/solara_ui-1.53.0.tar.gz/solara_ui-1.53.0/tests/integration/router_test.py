import playwright
import playwright.sync_api


def test_landing(page_session: playwright.sync_api.Page, solara_server, solara_app):
    # with screenshot_on_error(page, 'tmp/test_docs_basics.png'):
    with solara_app("solara.website.pages"):
        page_session.goto(solara_server.base_url)
        page_session.get_by_role(role="heading", name="Build high-quality web applications in pure Python").wait_for()
        page_session.get_by_role("link", name="Documentation").first.click()
        page_session.locator("text=How to use our documentation").first.wait_for()
        page_session.go_back()
        page_session.get_by_role(role="heading", name="Build high-quality web applications in pure Python").wait_for()


def test_docs_basics(page_session: playwright.sync_api.Page, solara_server, solara_app):
    # with screenshot_on_error(page, 'tmp/test_docs_basics.png'):
    with solara_app("solara.website.pages"):
        page_session.goto(solara_server.base_url + "/documentation/api/routing/use_route/fruit/banana")
        page_session.locator("text=You chose banana").wait_for()
        page_session.locator('button:has-text("kiwi")').click()
        page_session.locator("text=You chose kiwi").wait_for()
        page_session.locator('button:has-text("apple")').click()
        page_session.locator("text=You chose apple").wait_for()
        # back to kiwi
        page_session.go_back()
        page_session.locator("text=You chose kiwi").wait_for()
        # back to banana
        page_session.go_back()
        page_session.locator("text=You chose banana").wait_for()

        # forward to kiwi
        page_session.go_forward()
        page_session.locator("text=You chose kiwi").wait_for()

        # go to wrong fruit
        page_session.locator('button:has-text("wrong fruit")').click()

        # and follow the fallback link
        page_session.locator("text=Fruit not found, go to banana").click()
        page_session.locator("text=You chose banana").wait_for()

        # another wrong link
        page_session.locator('button:has-text("wrong url")').click()
        page_session.locator("text=Page does not exist").wait_for()

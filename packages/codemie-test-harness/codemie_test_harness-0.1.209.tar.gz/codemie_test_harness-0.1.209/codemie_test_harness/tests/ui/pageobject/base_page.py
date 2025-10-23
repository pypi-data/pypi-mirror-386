import re
from pathlib import Path

from playwright.sync_api import expect, Locator
from reportportal_client import step

from codemie_test_harness.tests.ui.pageobject.components.menu import Menu
from codemie_test_harness.tests.ui.pageobject.components.pop_up import PopUp


class BasePage:
    """Base page object with property-based element locators and common functionality."""

    def __init__(self, page):
        self.page = page

    # Component properties using @property decorator
    @property
    def back_button(self) -> Locator:
        """Back button in header with arrow icon"""
        return (
            self.page.locator("button.button.secondary.medium").first
            or self.page.locator(
                'button:has(svg[xmlns="http://www.w3.org/2000/svg"])'
            ).first
            or self.page.locator(".mr-6 button")
        )

    @property
    def cancel_button(self) -> Locator:
        """Cancel button in header"""
        return self.page.locator("button").filter(has_text="Cancel")

    @property
    def create_button(self) -> Locator:
        """Create button in header"""
        return self.page.locator("button").filter(has_text="Create")

    @property
    def pop_up(self):
        """Pop-up component instance."""
        return PopUp(self.page)

    @property
    def menu(self):
        """Menu component instance."""
        return Menu(self.page)

    # Common page elements
    @property
    def loading_indicator(self):
        """Loading indicator element."""
        return self.page.locator(".loading, .spinner")

    @property
    def error_message(self):
        """Error message element."""
        return self.page.locator(".error-message, .alert-danger")

    @property
    def success_message(self):
        """Success message element."""
        return self.page.locator(".success-message, .alert-success")

    @property
    def page_content(self):
        """Main page content area."""
        return self.page.locator("main, .main-content")

    @property
    def pagination_block(self):
        """Pagination panel at the bottom."""
        return self.page.locator("div.text-text-secondary.text-h5").filter(
            has_text="Page: "
        )

    def pagination_page_button(self, page_number: int):
        """Pagination numbered page button."""
        return self.page.locator("span.px-2.flex.justify-center").filter(
            has_text=str(page_number)
        )

    @property
    def show_per_page_label(self):
        """Show per-page label."""
        return self.page.locator("div.text-text-secondary.text-h5").filter(
            has_text="Show:"
        )

    @property
    def show_per_page_dropdown(self):
        """Show-per-page select in pagination."""
        return self.page.locator("#per-page")

    # Navigation methods
    @step
    def go_to_workflows_page(self):
        """Navigate to workflows page using menu navigation."""
        self.menu.navigate_to_workflows()
        return self

    @step
    def go_to_assistants_page(self):
        """Navigate to assistants page using menu navigation."""
        self.menu.navigate_to_assistants()
        return self

    @step
    def go_to_chats_page(self):
        """Navigate to chats page using menu navigation."""
        self.menu.navigate_to_chats()
        return self

    @step
    def go_to_applications_page(self):
        """Navigate to applications page using menu navigation."""
        self.menu.navigate_to_applications()
        return self

    @step
    def go_to_integrations_page(self):
        """Navigate to integrations page using menu navigation."""
        self.menu.navigate_to_integrations()
        return self

    @step
    def go_to_data_sources_page(self):
        """Navigate to data sources page using menu navigation."""
        self.menu.navigate_to_data_sources()
        return self

    @step
    def go_to_help_page(self):
        """Navigate to help page using menu navigation."""
        self.menu.navigate_to_help()
        return self

    # Pop-up interaction methods
    @step
    def close_popup_if_visible(self):
        """Close pop-up if it's visible."""
        if self.pop_up.pop_up.is_visible():
            self.pop_up.close_popup()
        return self

    @step
    def accept_popup_if_visible(self):
        """Accept/submit pop-up if it's visible."""
        if self.pop_up.pop_up.is_visible():
            self.pop_up.click_submit()
        return self

    @step
    def cancel_popup_if_visible(self):
        """Cancel pop-up if it's visible."""
        if self.pop_up.pop_up.is_visible():
            self.pop_up.click_cancel()
        return self

    # Utility methods
    @step
    def wait_for_page_load(self, timeout: int = 30000):
        """Wait for page to load completely."""
        self.page.wait_for_load_state("networkidle", timeout=timeout)
        return self

    @step
    def wait_for_element_visible(self, locator: str, timeout: int = 10000):
        """Wait for a specific element to be visible."""
        self.page.locator(locator).wait_for(state="visible", timeout=timeout)
        return self

    @step
    def refresh_page(self):
        """Refresh the current page."""
        self.page.reload()
        return self

    @step
    def scroll_to_top(self):
        """Scroll to the top of the page."""
        self.page.evaluate("window.scrollTo(0, 0)")
        return self

    @step
    def scroll_to_bottom(self):
        """Scroll to the bottom of the page."""
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        return self

    @step
    def get_page_title(self) -> str:
        """Get the page title."""
        return self.page.title()

    @step
    def get_current_url(self) -> str:
        """Get the current page URL."""
        return self.page.url

    @step
    def evaluate_current_url(self) -> str:
        """Evaluate the current page URL."""
        return self.page.evaluate("() => window.location.href")

    @step
    def get_id_from_url(self, url: str) -> str:
        """Extract the ID from the URL after the last slash."""
        return Path(url).name

    # Verification methods for pop-ups
    @step
    def should_see_new_release_popup(self):
        """Verify that the new release popup is visible with expected content."""
        expect(self.pop_up.cancel).to_have_text("Got It, Thanks!")
        expect(self.pop_up.submit).to_have_text("Tell Me More")
        expect(self.pop_up.menu).to_have_text("New CodeMie Release")
        expect(self.pop_up.body).to_have_text(
            re.compile(
                r"Great news! We've rolled out new CodeMie version \d.\d.\d+ to enhance your experience. Take a moment to "
                "explore what's new and discover how these changes can benefit you! Please review Release Notes!"
            )
        )
        expect(self.pop_up.close).to_be_visible()
        return self

    @step
    def should_not_see_new_release_popup(self):
        """Verify that the new release popup is not visible."""
        expect(self.pop_up.pop_up).to_be_hidden()
        return self

    # Common verification methods
    @step
    def should_have_menu_visible(self):
        """Verify that the menu is visible."""
        self.menu.should_be_visible()
        return self

    @step
    def should_have_page_content_visible(self):
        """Verify that the main page content is visible."""
        expect(self.page_content).to_be_visible()
        return self

    @step
    def should_not_have_loading_indicator(self):
        """Verify that loading indicator is not visible."""
        expect(self.loading_indicator).to_be_hidden()
        return self

    @step
    def should_have_page_title(self, expected_title: str):
        """Verify the page title."""
        expect(self.page).to_have_title(expected_title)
        return self

    @step
    def should_have_url_containing(self, url_part: str):
        """Verify that current URL contains expected part."""
        expect(self.page).to_have_url(re.compile(re.escape(url_part)))
        return self

    @step
    def should_have_error_message(self, error_text: str = None):
        """Verify that error message is displayed."""
        expect(self.error_message).to_be_visible()
        if error_text:
            expect(self.error_message).to_contain_text(error_text)
        return self

    @step
    def should_have_success_message(self, success_text: str = None):
        """Verify that success message is displayed."""
        expect(self.success_message).to_be_visible()
        if success_text:
            expect(self.success_message).to_contain_text(success_text)
        return self

    @step
    def should_not_have_error_message(self):
        """Verify that no error message is displayed."""
        expect(self.error_message).to_be_hidden()
        return self

    @step
    def should_not_have_success_message(self):
        """Verify that no success message is displayed."""
        expect(self.success_message).to_be_hidden()
        return self

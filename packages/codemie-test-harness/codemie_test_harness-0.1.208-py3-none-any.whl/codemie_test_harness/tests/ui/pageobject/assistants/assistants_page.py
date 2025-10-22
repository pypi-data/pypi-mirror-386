from codemie_test_harness.tests.ui.pageobject.base_page import BasePage
from playwright.sync_api import expect
from reportportal_client import step


class AssistantsPage(BasePage):
    """Assistants page object with property-based element locators."""

    page_url = "#/assistants"

    def __init__(self, page):
        super().__init__(page)
        self.page.goto(self.page_url)

    # Page elements using @property decorator
    @property
    def page_title(self):
        """Main page title."""
        return self.page.locator("h1, h2").filter(has_text="Assistants")

    @property
    def page_subtitle(self):
        """Page subtitle or description."""
        return self.page.locator("text=Browse and create AI assistants")

    @property
    def create_assistant_button(self):
        """Create new assistant button."""
        return self.page.locator("button").filter(has_text="Create Assistant")

    @property
    def search_input(self):
        """Search input field."""
        return self.page.locator('input[placeholder="Search"]')

    @property
    def assistant_cards(self):
        """All assistant cards on the page."""
        return self.page.locator(".assistant-card, .bg-assistant-card-fill")

    @property
    def sidebar(self):
        """Sidebar navigation."""
        return self.page.locator("aside.bg-sidebar")

    @property
    def my_assistants_link(self):
        """My Assistants navigation link."""
        return self.page.locator('a[href="#/assistants/my"]')

    @property
    def all_assistants_link(self):
        """All Assistants navigation link."""
        return self.page.locator('a[href="#/assistants/all"]')

    @property
    def templates_link(self):
        """Templates navigation link."""
        return self.page.locator('a[href="#/assistants/templates"]')

    @property
    def loading_indicator(self):
        """Loading spinner or indicator."""
        return self.page.locator(".loading, .spinner")

    @property
    def empty_state(self):
        """Empty state message when no assistants are found."""
        return self.page.locator(".empty-state, .no-results")

    @property
    def filters_section(self):
        """Filters section."""
        return self.page.locator('span:has-text("Filters")')

    @property
    def clear_filters_button(self):
        """Clear all filters button."""
        return self.page.locator('button:has-text("Clear all")')

    @property
    def action_view_details(self):
        """Dropdown 'View Details' button."""
        return self.page.locator("button").filter(has_text="View Details")

    @property
    def action_copy_link(self):
        """Dropdown 'Copy Link' button."""
        return self.page.locator("button").filter(has_text="Copy Link")

    @property
    def action_edit(self):
        """Dropdown 'Edit' button."""
        return self.page.locator("button").filter(has_text="Edit")

    @property
    def action_clone(self):
        """Dropdown 'Clone' button."""
        return self.page.locator("button").filter(has_text="Clone")

    @property
    def action_delete(self):
        """Dropdown 'Delete' button."""
        return self.page.locator("button").filter(has_text="Delete")

    @property
    def action_publish_to_marketplace(self):
        """Dropdown 'Publish to Marketplace' button."""
        return self.page.locator("button").filter(has_text="Publish to Marketplace")

    @property
    def updating_succesful_popup(self):
        """Updating succesful popup."""
        return self.page.locator(".codemie-toast .codemie-toast-header")

    # Navigation methods
    @step
    def navigate_to(self):
        """Navigate to the assistants page."""
        self.page.goto(self.page_url)
        return self

    # Action methods
    @step
    def click_create_assistant(self):
        """Click the create assistant button."""
        self.create_assistant_button.click()
        return self

    @step
    def search_assistants(self, search_term: str):
        """Search for assistants using the search input."""
        self.search_input.fill(search_term)
        self.page.keyboard.press("Enter")
        return self

    @step
    def navigate_to_my_assistants(self):
        """Navigate to My Assistants section."""
        self.my_assistants_link.click()
        return self

    @step
    def navigate_to_all_assistants(self):
        """Navigate to All Assistants section."""
        self.all_assistants_link.click()
        return self

    @step
    def navigate_to_templates(self):
        """Navigate to Templates section."""
        self.templates_link.click()
        return self

    @step
    def clear_all_filters(self):
        """Clear all applied filters."""
        self.clear_filters_button.click()
        return self

    @step
    def get_assistant_card_by_index(self, index: int):
        """Get assistant card by its index."""
        return self.assistant_cards.nth(index)

    @step
    def get_assistant_card_by_name(self, name: str):
        """Get assistant card by its name."""
        return self.page.locator(".body.h-card").filter(has_text=name)

    @step
    def click_assistant_card(self, name: str):
        """Click on an assistant card by name."""
        self.get_assistant_card_by_name(name).click()
        return self

    @step
    def action_dropdown_panel(self, name: str):
        """Three dot menu."""
        return self.get_assistant_card_by_name(name).locator(
            "div.flex.items-center.relative"
        )

    @step
    def click_assistant_view(self, name: str):
        """Click on an assistant view by name."""
        self.action_dropdown_panel(name).click()
        self.action_view_details.click()
        return self

    @step
    def click_assistant_edit(self, name: str):
        """Click on an assistant edit by name."""
        self.action_dropdown_panel(name).click()
        self.action_edit.click()
        return self

    # Verification methods
    @step
    def should_be_on_assistants_page(self):
        """Verify that we are on the assistants page."""
        expect(self.page_title).to_be_visible()
        return self

    @step
    def should_see_create_assistant_button(self):
        """Verify that create assistant button is visible."""
        expect(self.create_assistant_button).to_be_visible()
        return self

    @step
    def should_see_search_input(self):
        """Verify that search input is visible."""
        expect(self.search_input).to_be_visible()
        return self

    @step
    def should_see_assistant_cards(self, minimum_count: int = 1):
        """Verify that assistant cards are visible."""
        expect(self.assistant_cards).to_have_count_greater_than_or_equal_to(
            minimum_count
        )
        return self

    @step
    def should_see_assistant_count(self, expected_count: int):
        """Verify the exact number of assistant cards."""
        expect(self.assistant_cards).to_have_count(expected_count)
        return self

    @step
    def should_see_empty_state(self):
        """Verify that empty state is displayed."""
        expect(self.empty_state).to_be_visible()
        return self

    @step
    def should_not_see_loading_indicator(self):
        """Verify that loading indicator is not visible."""
        expect(self.loading_indicator).to_be_hidden()
        return self

    @step
    def should_see_assistant_with_name(self, name: str):
        """Verify that an assistant with specific name is visible."""
        expect(self.get_assistant_card_by_name(name)).to_be_visible()
        return self

    @step
    def should_not_see_assistant_with_name(self, name: str):
        """Verify that an assistant with specific name is not visible."""
        expect(self.get_assistant_card_by_name(name)).to_be_hidden()
        return self

    @step
    def should_see_updating_popup(self, text: str):
        """Verify that an update popup is visible."""
        expect(self.updating_succesful_popup).to_be_visible()
        expect(self.updating_succesful_popup).to_have_text(text)
        return self

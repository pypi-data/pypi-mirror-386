import re
from playwright.sync_api import expect
from reportportal_client import step


class WorkflowCard:
    """Component representing a single workflow card on the workflows page."""

    def __init__(self, page, card_locator):
        """
        Initialize workflow card component.

        Args:
            page: Playwright page object
            card_locator: Locator for the specific workflow card container
        """
        self.page = page
        self.card = card_locator

    # Card elements using @property decorator
    @property
    def avatar(self):
        """Workflow avatar image."""
        return self.card.locator('//*[contains(@class,"avatar") or @alt="avatar"]')

    @property
    def title(self):
        """Workflow title element."""
        return self.card.locator(".whitespace-nowrap.truncate.font-semibold")

    @property
    def author(self):
        """Workflow author element."""
        return self.card.locator(".text-xs.text-text-gray-300")

    @property
    def description(self):
        """Workflow description element."""
        return self.card.locator(".flex-row p.text-xs")

    @property
    def description_tooltip(self):
        """Workflow description tooltip element."""
        return self.page.locator(
            "//div[contains(@class, 'p-tooltip') and contains(@class, 'p-component absolute')]"
        )

    @property
    def run_button(self):
        """Run workflow button."""
        return self.card.locator("button.gradient.medium")

    @property
    def menu_button(self):
        """Workflow menu button (three dots)."""
        return self.card.locator("button.button.tertiary")

    @property
    def sharing_status(self):
        """Sharing status container."""
        return self.card.locator(".flex.flex-row.ml-auto.items-center.text-xs.gap-3")

    @property
    def shared_with_project_text(self):
        """Shared with project text element."""
        return self.card.locator("text=Shared with Project")

    @property
    def shared_with_project_icon(self):
        """Shared with project icon."""
        return self.card.locator(".sharing_status svg")

    # Utility methods
    @step
    def get_title(self) -> str:
        """Get the workflow title."""
        return self.title.text_content()

    @step
    def get_author(self) -> str:
        """Get the workflow author."""
        author_text = self.author.text_content()
        return author_text.replace("by ", "") if author_text else ""

    @step
    def get_description(self) -> str:
        """Get the workflow description."""
        return self.description.text_content()

    @step
    def get_avatar_src(self) -> str:
        """Get the workflow avatar image source."""
        return self.avatar.get_attribute("src")

    @step
    def is_shared_with_project(self) -> bool:
        """Check if workflow is shared with project."""
        return self.shared_with_project_text.is_visible()

    @step
    def is_visible(self) -> bool:
        """Check if the workflow card is visible."""
        return self.card.is_visible()

    # Action methods
    @step
    def click_run(self):
        """Click the run workflow button."""
        self.run_button.click()
        return self

    @step
    def click_menu(self):
        """Click the workflow menu button (three dots)."""
        self.menu_button.click()
        return self

    @step
    def click_card(self):
        """Click anywhere on the workflow card."""
        self.card.click()
        return self

    @step
    def hover(self):
        """Hover over the workflow card."""
        self.card.hover()
        return self

    @step
    def wait_for_visible(self, timeout: int = 5000):
        """Wait for the workflow card to be visible."""
        self.card.wait_for(state="visible", timeout=timeout)
        return self

    # Verification methods using expect()
    @step
    def should_have_title(self, expected_title: str):
        """Verify the workflow has the expected title."""
        return self.get_title() == expected_title

    @step
    def should_have_author(self, expected_author: str):
        """Verify the workflow has the expected author."""
        return self.get_author() == expected_author

    @step
    def should_have_description(self, expected_description: str):
        """Verify the workflow has the expected description."""
        return self.get_description() == expected_description

    @step
    def should_be_shared_with_project(self):
        """Verify the workflow is shared with project."""
        expect(self.shared_with_project_text).to_be_visible()
        return self

    @step
    def should_not_be_shared_with_project(self):
        """Verify the workflow is not shared with project."""
        expect(self.shared_with_project_text).not_to_be_visible()
        return self

    @step
    def should_be_visible(self):
        """Verify the workflow card is visible."""
        expect(self.card).to_be_visible()
        return self

    @step
    def should_not_be_visible(self):
        """Verify the workflow card is not visible."""
        expect(self.card).not_to_be_visible()
        return self

    @step
    def should_have_avatar(self, expected_src: str = None):
        """Verify the workflow has an avatar image."""
        expect(self.avatar).to_be_visible()
        if expected_src:
            expect(self.avatar).to_have_attribute("src", expected_src)
        return self

    @step
    def should_have_run_button(self):
        """Verify the workflow has a run button."""
        expect(self.run_button).to_be_visible()
        expect(self.run_button).to_be_enabled()
        return self

    @step
    def should_have_menu_button(self):
        """Verify the workflow has a menu button."""
        expect(self.menu_button).to_be_visible()
        expect(self.menu_button).to_be_enabled()
        return self

    @step
    def should_be_hoverable(self):
        """Verify the workflow card can be hovered."""
        self.hover()
        expect(self.card).to_have_class(re.compile(r"hover:bg-opacity-30"))
        return self

    @step
    def should_have_sharing_status_visible(self):
        """Verify the sharing status section is visible."""
        expect(self.sharing_status).to_be_visible()
        return self

    @step
    def should_have_all_elements_visible(self):
        """Verify all main card elements are visible."""
        expect(self.card).to_be_visible()
        expect(self.title).to_be_visible()
        expect(self.author).to_be_visible()
        expect(self.description).to_be_visible()
        expect(self.run_button).to_be_visible()
        expect(self.menu_button).to_be_visible()
        return self

# fb_locators.py
# All Facebook UI locators in one place.
# If Facebook updates their UI, only this file needs updating.

class FBLocators:

    # ─── Post Level ───────────────────────────────────────────

    @staticmethod
    def comment_button(page):
        """The Comment button below a post"""
        return page.get_by_role('button', name='Comment').first

    @staticmethod
    def comments_filter_dropdown(page):
        """Dropdown showing Most Relevant / Newest / All Comments"""
        return page.get_by_role('button', name='Most relevant').first

    @staticmethod
    def all_comments_option(page):
        """'All comments' option inside the filter dropdown"""
        return page.get_by_role('menuitem', name='All comments').first

    @staticmethod
    def view_more_comments_button(page):
        """'View more comments' button to load more"""
        return page.get_by_role('button', name='View more comments').first

    @staticmethod
    def view_previous_comments_button(page):
        """'View previous comments' button"""
        return page.get_by_role('button', name='View previous comments').first

    # ─── Comment Level ─────────────────────────────────────────

    @staticmethod
    def all_comment_containers(page):
        """All top-level comment containers on the page"""
        return page.locator('[aria-label*="Comment by"]')

    @staticmethod
    def commenter_name(comment_element):
        """Commenter name link inside a comment element"""
        return comment_element.locator('a[role="link"] span').first

    @staticmethod
    def comment_text(comment_element):
        """Comment text content inside a comment element"""
        return comment_element.locator('div[dir="auto"]').first

    @staticmethod
    def comment_id_attribute():
        """Attribute name that holds the comment ID"""
        return 'data-commentid'

    @staticmethod
    def reply_containers(comment_element):
        """Reply elements nested inside a comment"""
        return comment_element.locator('[aria-label*="Reply by"]')

    # ─── Page Level ────────────────────────────────────────────

    @staticmethod
    def login_email(page):
        return page.locator('input[name="email"]')

    @staticmethod
    def login_password(page):
        return page.locator('input[name="pass"]')

    @staticmethod
    def login_button(page):
        return page.locator('[name=login]')
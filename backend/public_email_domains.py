"""
Single source of truth for which email domains are "public" (freemail/personal)
rather than belonging to one real organisation.

Why this matters: onboarding normally matches new users into an existing workspace by
their email domain, on the assumption that everyone @acme.com works at the same
company. That assumption is false for gmail.com, outlook.com, and similar providers —
two strangers both signing up with a gmail.com address must never land in the same
workspace just because they share a mail provider. Anyone on a public domain always
gets their own new workspace, named after whatever company they type, and other people
can only join it by invitation (see auth_service.create_invite).
"""

PUBLIC_EMAIL_DOMAINS = frozenset(
    {
        # Google
        "gmail.com",
        "googlemail.com",
        # Yahoo (regional variants)
        "yahoo.com",
        "yahoo.co.uk",
        "yahoo.co.in",
        "yahoo.co.jp",
        "yahoo.fr",
        "yahoo.de",
        "yahoo.it",
        "yahoo.es",
        "yahoo.ca",
        "yahoo.com.au",
        "yahoo.in",
        "ymail.com",
        "rocketmail.com",
        # Microsoft
        "outlook.com",
        "outlook.in",
        "outlook.co.uk",
        "outlook.fr",
        "outlook.de",
        "hotmail.com",
        "hotmail.co.uk",
        "hotmail.fr",
        "hotmail.de",
        "hotmail.it",
        "live.com",
        "live.co.uk",
        "msn.com",
        # Apple
        "icloud.com",
        "me.com",
        "mac.com",
        # Proton
        "proton.me",
        "protonmail.com",
        # India
        "rediffmail.com",
        # Other common freemail providers
        "aol.com",
        "zoho.com",
        "yandex.com",
        "mail.com",
        "gmx.com",
        "gmx.net",
        "fastmail.com",
        "tutanota.com",
        "hey.com",
    }
)


def is_public_domain(domain: str) -> bool:
    """Returns True if `domain` is a known freemail/personal provider, not a company's own."""
    return domain.strip().lower() in PUBLIC_EMAIL_DOMAINS

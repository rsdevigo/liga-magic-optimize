"""Project exception hierarchy."""


class CubeBudgetError(Exception):
    """Base exception for all project errors."""


class ConfigError(CubeBudgetError):
    """Configuration loading or validation failed."""


class DatabaseError(CubeBudgetError):
    """Database operation failed."""


class CardReadError(CubeBudgetError):
    """Failed to read or parse card list file."""


class ScraperError(CubeBudgetError):
    """Scraping operation failed."""


class CaptchaDetectedError(ScraperError):
    """Captcha detected on LigaMagic."""


class OptimizerError(CubeBudgetError):
    """Optimization failed."""


class InfeasibleError(OptimizerError):
    """No feasible solution exists for the given constraints."""


class ReportError(CubeBudgetError):
    """Report generation failed."""

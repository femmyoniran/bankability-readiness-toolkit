import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "bankability-toolkit-dev-key-change-in-production")
    DEBUG = False
    TESTING = False
    SESSION_TYPE = "filesystem"

    # Scoring weights
    TECHNOLOGY_WEIGHT = 0.20
    FINANCIAL_WEIGHT = 0.25
    CREDIT_RISK_WEIGHT = 0.20
    PROJECT_STRUCTURE_WEIGHT = 0.20
    MARKET_RESOURCE_WEIGHT = 0.15

    # Financial defaults
    DEFAULT_DISCOUNT_RATE = 0.08
    DEFAULT_INFLATION_RATE = 0.025
    DEFAULT_TAX_RATE = 0.21
    DEFAULT_DEBT_TENOR_YEARS = 20
    DEFAULT_CONSTRUCTION_PERIOD_MONTHS = 24
    DEFAULT_PROJECT_LIFE_YEARS = 30

    # DSCR thresholds
    DSCR_MINIMUM = 1.20
    DSCR_TARGET = 1.40
    DSCR_STRONG = 1.60

    # RUS and LPO configuration
    RUS_MAX_LOAN_TERM_YEARS = 35
    LPO_MAX_GUARANTEE_PERCENT = 0.80
    LPO_CREDIT_SUBSIDY_FLOOR = 0.01

    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = True


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}

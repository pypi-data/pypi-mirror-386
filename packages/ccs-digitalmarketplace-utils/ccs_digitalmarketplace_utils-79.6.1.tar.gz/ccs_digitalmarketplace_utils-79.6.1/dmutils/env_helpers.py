import os


def get_api_endpoint_from_stage(stage: str, app: str = 'api') -> str:
    """Return the full URL of given API or Search API environment.

    :param stage: environment name.
    :param app: should be either 'api' or 'search-api'
    """
    stage_domains = {
        'development': 'https://{}.development.marketplace.team'.format(app),
        'dev': 'https://{}.dev.marketplace.team'.format(app),
        'preview': 'https://{}.development.marketplace.team'.format(app),
        'nft': 'https://{}.nft.marketplace.team'.format(app),
        'pre-production': 'https://{}.pre-production.marketplace.team'.format(app),
        'preprod': 'https://{}.preprod.marketplace.team'.format(app),
        'test': 'https://{}.test.marketplace.team'.format(app),
        'uat': 'https://{}.uat.marketplace.team'.format(app),
        'integration': 'https://{}.integration.marketplace.team'.format(app),
        'production': 'https://{}.applytosupply.digitalmarketplace.service.gov.uk'.format(app),
        'sandbox': 'https://{}.sandbox.marketplace.team'.format(app),
        'clone': 'https://{}.applytosupply.crowncommercial.gov.uk'.format(app),
    }

    dev_ports = {
        "api": os.getenv("DM_API_PORT", 8000),
        "search-api": os.getenv("DM_SEARCH_API_PORT", 8009),
        "antivirus-api": os.getenv("DM_ANTIVIRUS_API_PORT", 8008),
        "tasks-api": os.getenv("DM_ANTIVIRUS_API_PORT", 8010),
    }

    if stage == 'local':
        return 'http://localhost:{}'.format(dev_ports[app])

    return stage_domains[stage]


def get_cdp_api_endpoint_from_stage(stage: str) -> str:
    """Return the full URL of given CDP API environment.

    :param stage: environment name.
    """
    stage_domains = {
        'local': 'https://data-sharing.integration.supplier-information.find-tender.service.gov.uk',
        'development': 'https://data-sharing.integration.supplier-information.find-tender.service.gov.uk',
        'preview': 'https://data-sharing.integration.supplier-information.find-tender.service.gov.uk',
        'nft': 'https://data-sharing.integration.supplier-information.find-tender.service.gov.uk',
        'pre-production': 'https://data-sharing.integration.supplier-information.find-tender.service.gov.uk',
        'production': 'https://data-sharing.supplier-information.find-tender.service.gov.uk',
    }

    return stage_domains[stage]


def get_web_url_from_stage(stage: str) -> str:
    """Return the full URL of given web environment.

    :param stage: environment name.
    """
    if stage == 'local':
        return 'http://localhost'

    stage_domains = {
        'development': 'https://www.development.marketplace.team',
        'dev': 'https://www.dev.marketplace.team',
        'preview': 'https://www.development.marketplace.team',
        'nft': 'https://www.nft.marketplace.team',
        'pre-production': 'https://www.pre-production.marketplace.team',
        'preprod': 'https://www.preprod.marketplace.team',
        'test': 'https://www.test.marketplace.team',
        'uat': 'https://www.uat.marketplace.team',
        'integration': 'https://www.integration.marketplace.team',
        'production': 'https://www.applytosupply.digitalmarketplace.service.gov.uk',
        'sandbox': 'https://www.sandbox.marketplace.team',
        'clone': 'https://www.applytosupply.crowncommercial.gov.uk',
    }
    return stage_domains[stage]


def get_assets_endpoint_from_stage(stage: str) -> str:
    if stage == 'local':
        # Static files are not served via nginx for local environments
        raise NotImplementedError()

    return get_api_endpoint_from_stage(stage, 'assets')

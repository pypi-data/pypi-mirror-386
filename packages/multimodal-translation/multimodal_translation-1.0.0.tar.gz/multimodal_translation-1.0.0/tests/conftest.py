import pytest
from argostranslate import package, translate


@pytest.fixture(scope="session", autouse=True)
def install_argos_models():

    installed = translate.get_installed_languages()
    installed_codes = [(lan.code,) for lan in installed]

    pairs = [("en", "es"), ("en", "fr"), ("en", "zh"), ("zh", "en"),]

    for from_code, to_code in pairs:
        if (from_code, to_code) in installed_codes:
            print(f"Already installed: {from_code} → {to_code}")
            continue
        available_packages = package.get_available_packages()
        for p in available_packages:
            if p.from_code == from_code and p.to_code == to_code:
                print(f"Installing {from_code} → {to_code}")
                package.install_from_path(p.download())

from setuptools import setup, find_packages

# Configuration
NAME = "io4it"
VERSION = "2.1.7.1"

INSTALL_REQUIRES = [
    "torchvision==0.23.0",
    "torchaudio==2.8.0",
    "torch==2.8.0",
    "pylatexenc",
    "docopt",
    "boto3",
    "opencv-python-headless==4.6.0.66",
    "docling==2.30.0",
    "docling-core==2.26.3", 
    "speechbrain",
    "whisper",
    "whisper-openai",
    "pyannote.audio==3.4.0",
    "pyannote-core",
    "pypandoc",
    "pypandoc-binary",
    "scikit-learn",
    "openai",
    "pip-system-certs==5.0",
    "docx2pdf",
    "doc2docx",
    "msal",
    "exchangelib",
    "CATEGORIT"
]

AUTHOR = ""
AUTHOR_EMAIL = ""
URL = ""
DESCRIPTION = ""
LICENSE = ""
KEYWORDS = ["orange3 add-on",]

PACKAGES = find_packages()
PACKAGES = [pack for pack in PACKAGES if "orangecontrib" in pack and "IO4IT" in pack]
PACKAGES.append("orangecontrib")

PACKAGE_DATA = {
    "orangecontrib.IO4IT.widgets": ["icons/*", "designer/*"],
}


ENTRY_POINTS = {
    "orange.widgets": (
        "IO4IT = orangecontrib.IO4IT.widgets",
        "AAIT - ALGORITHM = orangecontrib.ALGORITHM.widgets",
        "AAIT - API = orangecontrib.API.widgets",
        "AAIT - MODELS = orangecontrib.LLM_MODELS.widgets",
        "AAIT - LLM INTEGRATION = orangecontrib.LLM_INTEGRATION.widgets",
        "AAIT - TOOLBOX = orangecontrib.TOOLBOX.widgets",
    ),
}

NAMESPACE_PACKAGES = ["orangecontrib"]


setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    license=LICENSE,
    keywords=KEYWORDS,
    packages=PACKAGES,
    package_data=PACKAGE_DATA,
    install_requires=INSTALL_REQUIRES,
    entry_points=ENTRY_POINTS,
    namespace_packages=NAMESPACE_PACKAGES,
)

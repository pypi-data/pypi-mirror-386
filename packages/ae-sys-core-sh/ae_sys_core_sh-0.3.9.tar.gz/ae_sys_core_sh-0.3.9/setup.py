# THIS FILE IS EXCLUSIVELY MAINTAINED by the project aedev.project_tpls v0.3.59
""" setup of ae namespace module portion sys_core_sh: SiHOT PMS system core xml interface. """
# noinspection PyUnresolvedReferences
import sys
print(f"SetUp {__name__=} {sys.executable=} {sys.argv=} {sys.path=}")

# noinspection PyUnresolvedReferences
import setuptools

setup_kwargs = {
    'author': 'AndiEcker',
    'author_email': 'aecker2@gmail.com',
    'classifiers': [       'Development Status :: 3 - Alpha', 'Natural Language :: English', 'Operating System :: OS Independent',
        'Programming Language :: Python', 'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9', 'Topic :: Software Development :: Libraries :: Python Modules',
        'Typing :: Typed'],
    'description': 'ae namespace module portion sys_core_sh: SiHOT PMS system core xml interface',
    'extras_require': {       'dev': [       'aedev_project_tpls', 'ae_ae', 'anybadge', 'coverage-badge', 'aedev_project_manager', 'flake8',
                       'mypy', 'pylint', 'pytest', 'pytest-cov', 'pytest-django', 'typing', 'types-setuptools'],
        'docs': [],
        'tests': [       'anybadge', 'coverage-badge', 'aedev_project_manager', 'flake8', 'mypy', 'pylint', 'pytest',
                         'pytest-cov', 'pytest-django', 'typing', 'types-setuptools']},
    'install_requires': ['ae_base', 'ae_core', 'ae_console', 'ae_sys_core'],
    'keywords': ['configuration', 'development', 'environment', 'productivity'],
    'license': 'GPL-3.0-or-later',
    'long_description': ('<!-- THIS FILE IS EXCLUSIVELY MAINTAINED by the project ae.ae v0.3.101 -->\n'
 '<!-- THIS FILE IS EXCLUSIVELY MAINTAINED by the project aedev.namespace_root_tpls v0.3.22 -->\n'
 '# sys_core_sh 0.3.9\n'
 '\n'
 '[![GitLab develop](https://img.shields.io/gitlab/pipeline/ae-group/ae_sys_core_sh/develop?logo=python)](\n'
 '    https://gitlab.com/ae-group/ae_sys_core_sh)\n'
 '[![LatestPyPIrelease](\n'
 '    https://img.shields.io/gitlab/pipeline/ae-group/ae_sys_core_sh/release0.3.9?logo=python)](\n'
 '    https://gitlab.com/ae-group/ae_sys_core_sh/-/tree/release0.3.9)\n'
 '[![PyPIVersions](https://img.shields.io/pypi/v/ae_sys_core_sh)](\n'
 '    https://pypi.org/project/ae-sys-core-sh/#history)\n'
 '\n'
 '>ae namespace module portion sys_core_sh: SiHOT PMS system core xml interface.\n'
 '\n'
 '[![Coverage](https://ae-group.gitlab.io/ae_sys_core_sh/coverage.svg)](\n'
 '    https://ae-group.gitlab.io/ae_sys_core_sh/coverage/index.html)\n'
 '[![MyPyPrecision](https://ae-group.gitlab.io/ae_sys_core_sh/mypy.svg)](\n'
 '    https://ae-group.gitlab.io/ae_sys_core_sh/lineprecision.txt)\n'
 '[![PyLintScore](https://ae-group.gitlab.io/ae_sys_core_sh/pylint.svg)](\n'
 '    https://ae-group.gitlab.io/ae_sys_core_sh/pylint.log)\n'
 '\n'
 '[![PyPIImplementation](https://img.shields.io/pypi/implementation/ae_sys_core_sh)](\n'
 '    https://gitlab.com/ae-group/ae_sys_core_sh/)\n'
 '[![PyPIPyVersions](https://img.shields.io/pypi/pyversions/ae_sys_core_sh)](\n'
 '    https://gitlab.com/ae-group/ae_sys_core_sh/)\n'
 '[![PyPIWheel](https://img.shields.io/pypi/wheel/ae_sys_core_sh)](\n'
 '    https://gitlab.com/ae-group/ae_sys_core_sh/)\n'
 '[![PyPIFormat](https://img.shields.io/pypi/format/ae_sys_core_sh)](\n'
 '    https://pypi.org/project/ae-sys-core-sh/)\n'
 '[![PyPILicense](https://img.shields.io/pypi/l/ae_sys_core_sh)](\n'
 '    https://gitlab.com/ae-group/ae_sys_core_sh/-/blob/develop/LICENSE.md)\n'
 '[![PyPIStatus](https://img.shields.io/pypi/status/ae_sys_core_sh)](\n'
 '    https://libraries.io/pypi/ae-sys-core-sh)\n'
 '[![PyPIDownloads](https://img.shields.io/pypi/dm/ae_sys_core_sh)](\n'
 '    https://pypi.org/project/ae-sys-core-sh/#files)\n'
 '\n'
 '\n'
 '## installation\n'
 '\n'
 '\n'
 'execute the following command to install the\n'
 'ae.sys_core_sh module\n'
 'in the currently active virtual environment:\n'
 ' \n'
 '```shell script\n'
 'pip install ae-sys-core-sh\n'
 '```\n'
 '\n'
 'if you want to contribute to this portion then first fork\n'
 '[the ae_sys_core_sh repository at GitLab](\n'
 'https://gitlab.com/ae-group/ae_sys_core_sh "ae.sys_core_sh code repository").\n'
 'after that pull it to your machine and finally execute the\n'
 'following command in the root folder of this repository\n'
 '(ae_sys_core_sh):\n'
 '\n'
 '```shell script\n'
 'pip install -e .[dev]\n'
 '```\n'
 '\n'
 'the last command will install this module portion, along with the tools you need\n'
 'to develop and run tests or to extend the portion documentation. to contribute only to the unit tests or to the\n'
 'documentation of this portion, replace the setup extras key `dev` in the above command with `tests` or `docs`\n'
 'respectively.\n'
 '\n'
 'more detailed explanations on how to contribute to this project\n'
 '[are available here](\n'
 'https://gitlab.com/ae-group/ae_sys_core_sh/-/blob/develop/CONTRIBUTING.rst)\n'
 '\n'
 '\n'
 '## namespace portion documentation\n'
 '\n'
 'information on the features and usage of this portion are available at\n'
 '[ReadTheDocs](\n'
 'https://ae.readthedocs.io/en/latest/_autosummary/ae.sys_core_sh.html\n'
 '"ae_sys_core_sh documentation").\n'),
    'long_description_content_type': 'text/markdown',
    'name': 'ae_sys_core_sh',
    'package_data': {'': []},
    'packages': ['ae'],
    'project_urls': {       'Bug Tracker': 'https://gitlab.com/ae-group/ae_sys_core_sh/-/issues',
        'Documentation': 'https://ae.readthedocs.io/en/latest/_autosummary/ae.sys_core_sh.html',
        'Repository': 'https://gitlab.com/ae-group/ae_sys_core_sh',
        'Source': 'https://ae.readthedocs.io/en/latest/_modules/ae/sys_core_sh.html'},
    'python_requires': '>=3.9',
    'url': 'https://gitlab.com/ae-group/ae_sys_core_sh',
    'version': '0.3.9',
    'zip_safe': True,
}

if __name__ == "__main__":
    setuptools.setup(**setup_kwargs)
    pass

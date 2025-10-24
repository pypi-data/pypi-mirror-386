from distutils.command.build import build

from setuptools import find_packages, setup


class CustomBuild(build):
    sub_commands = [("compile_catalog", lambda x: True)] + build.sub_commands


setup(
    author='Zdeněk Böhm',
    author_email='zdenek.bohm@nic.cz',
    name='djangocms-oidc-form-fields',
    version='4.1.0',
    description='Plugin OIDC (OpenID Connect) for Aldryn form fields.',
    long_description=open('README.rst').read(),
    long_description_content_type='text/x-rst',
    url='https://github.com/CZ-NIC/djangocms-oidc-form-fields',
    license='GPL GNU License',
    platforms=['OS Independent'],
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Framework :: Django CMS :: 4.1',
        'Framework :: Django CMS :: 5.0',
    ),
    python_requires='>=3.10',
    install_requires=(
        'djangocms-oidc~=5.0',
        "djangocms-aldryn-forms[captcha]~=8.3",
    ),
    extras_require={
        'quality': ['isort', 'flake8'],
    },
    packages=find_packages(exclude=['djangocms_oidc_form_fields.tests']),
    cmdclass={"build": CustomBuild},
    setup_requires=["Babel >=2.3"],
    include_package_data=True,
    zip_safe=False
)

from setuptools import setup, find_packages

setup(
    name='aun-detection',
    version='0.1.2',  # ← bump version
    packages=find_packages(),
    install_requires=[],
    author='Jerry Katz',
    author_email='halifaxjerrykatz@gmail.com',
    description='AI mimicry detection using symbolic collapse logic (∿)',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/halifaxjerrykatz-dotcom/aun-detection',
    license='MIT',  # ← SPDX license expression
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    project_urls={
        "Documentation": "https://github.com/halifaxjerrykatz-dotcom/aun-detection",
        "Source": "https://github.com/halifaxjerrykatz-dotcom/aun-detection",
        "Tracker": "https://github.com/halifaxjerrykatz-dotcom/aun-detection/issues",
    },
)

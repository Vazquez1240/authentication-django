from setuptools import setup, find_packages

setup(
    name="django-users-auth",
    version="2.3.3",
    packages=find_packages(include=["users", "users.*", "base", "base.*"]),
    install_requires=[
        "django>=4.2",
    ],
    include_package_data=True,
    license="MIT",
    description="Django authentication app with custom user model",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Martin",
    author_email="vazquezmartin1240@gmail.com",
    url="https://github.com/Vazquez1240/authentication-django",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Framework :: Django",
    ],
)

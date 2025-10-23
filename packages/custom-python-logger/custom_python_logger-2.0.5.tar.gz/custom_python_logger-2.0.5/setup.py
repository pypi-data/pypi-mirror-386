from setuptools import find_packages, setup

package_version = "2.0.5"

package_name = "custom-python-logger"
package_description = "A custom logger with color support and additional features."

package_name_ = package_name.replace("-", "_")
package_long_description_content_type = "text/markdown"
package_url = f"https://github.com/aviz92/{package_name}"
package_python_requires = ">=3.11"
package_author = "Avi Zaguri"

with open("requirements.txt") as file:
    package_install_requires = [line.strip() for line in file.readlines() if line.strip() and not line.startswith("#")]

with open("README.md") as file:
    package_long_description = file.read()

setup(
    name=package_name,
    version=package_version,
    packages=find_packages(include=[package_name_, f"{package_name_}.*"]),
    install_requires=package_install_requires,
    author=package_author,
    author_email="",
    description=package_description,
    long_description=package_long_description,
    long_description_content_type=package_long_description_content_type,
    url=package_url,
    project_urls={
        "Repository": package_url,
    },
    python_requires=package_python_requires,
)

# module-qc-analysis-tools v2.7.0rc3

A general python tool for running ITkPixV1.1 module QC test analysis. An
overview of the steps in the module QC procedure is documented in the
[Electrical specification and QC procedures for ITkPixV1.1 modules](https://gitlab.cern.ch/atlas-itk/pixel/module/itkpix-electrical-qc/)
document and in
[this spreadsheet](https://docs.google.com/spreadsheets/d/1qGzrCl4iD9362RwKlstZASbhphV_qTXPeBC-VSttfgE/edit#gid=989740987).

---

<!-- sync the following div with docs/index.md -->
<div align="center">

<!--<img src="https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/raw/main/docs/assets/images/logo.svg" alt="mqat logo" width="500" role="img">-->

<!-- --8<-- [start:badges] -->

<!-- prettier-ignore-start -->

| | |
| --- | --- |
| CI/CD | [![CI - Test][cicd-badge]][cicd-link] |
| Docs | [![Docs - Badge][docs-badge]][docs-link] |
| Package | [![PyPI - Downloads - Total][pypi-downloads-total]][pypi-link] [![PyPI - Downloads - Per Month][pypi-downloads-dm]][pypi-link] [![PyPI - Version][pypi-version]][pypi-link] [![PyPI platforms][pypi-platforms]][pypi-link] |
| Meta | [![GitLab - Issue][gitlab-issues-badge]][gitlab-issues-link] [![License - MIT][license-badge]][license-link] |

[cicd-badge]:            https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/badges/main/pipeline.svg
[cicd-link]:             https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/commits/main
[docs-badge]:            https://img.shields.io/badge/documentation-mkdocs-brightgreen?style=for-the-badge&logo=data:image/png;base64,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
[docs-link]:                https://atlas-itk-pixel-mqat.docs.cern.ch
[gitlab-issues-badge]:      https://img.shields.io/static/v1?label=Issues&message=File&color=blue&logo=gitlab
[gitlab-issues-link]:       https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/issues
[pypi-link]:                https://pypi.org/project/module-qc-analysis-tools/
[pypi-downloads-dm]:        https://img.shields.io/pypi/dm/module-qc-analysis-tools.svg?color=blue&label=Downloads&logo=pypi&logoColor=gold
[pypi-downloads-total]:     https://pepy.tech/badge/module-qc-analysis-tools
[pypi-platforms]:           https://img.shields.io/pypi/pyversions/module-qc-analysis-tools
[pypi-version]:             https://img.shields.io/pypi/v/module-qc-analysis-tools
[license-badge]:            https://img.shields.io/badge/License-MIT-blue.svg
[license-link]:             https://spdx.org/licenses/MIT.html

<!-- prettier-ignore-end -->

<!-- --8<-- [end:badges] -->

</div>

# Konfuzio SDK

![Konfuzio Downloads](https://img.shields.io/pypi/dm/konfuzio_sdk)

The Konfuzio Software Development Kit (Konfuzio SDK) provides a
[Python API](https://dev.konfuzio.com/sdk/sourcecode.html) to interact with the
[Konfuzio Server](https://dev.konfuzio.com/index.html#konfuzio-server).

|                                                                   |                                                             |
|-------------------------------------------------------------------|-------------------------------------------------------------|
| 📒 [Docs](https://dev.konfuzio.com/sdk/index.html)                | Read the docs                                               |
| 💾 [Installation](https://dev.konfuzio.com/sdk/get_started.html)  | How to install the Konfuzio SDK                             |
| 🎓 [Tutorials](https://dev.konfuzio.com/sdk/tutorials.html)       | See what the Konfuzio SDK can do with our tutorials         |
| 💡 [Explanations](https://dev.konfuzio.com/sdk/explanations.html) | Here are links to teaching material about the Konfuzio SDK. |
| ⚙️ [API Reference](https://dev.konfuzio.com/sdk/sourcecode.html)  | Python classes, methods, and functions                      |
| 🐛 [Issue Tracker](https://konfuzio.com/support)                  | Report Konfuzio SDK issues                                  |
| 🔭 [Changelog](https://dev.konfuzio.com/sdk/)                     | Review the release notes                                    |
| 📰 MIT License                                                    | Review the license in the section below                     |

## Installation

As developer register on our [public HOST for free: https://app.konfuzio.com](https://app.konfuzio.com/accounts/signup/)

Then you can use pip to install Konfuzio SDK and run init:

    pip install konfuzio_sdk

    konfuzio_sdk init

The init will create a Token to connect to the Konfuzio Server. This will create variables `KONFUZIO_USER`,
`KONFUZIO_TOKEN` and `KONFUZIO_HOST` in an `.env` file in your working directory.

By default, the SDK is installed without the AI-related dependencies like `torch` or `transformers` and allows for using 
only the Data-related SDK concepts but not the AI models. To install the SDK with the AI components,
run the following command:
  ```
  pip install konfuzio_sdk[ai]
  ```

Find the full installation guide [here](https://dev.konfuzio.com/sdk/get_started.html#install-sdk).
To configure a PyCharm setup, follow the instructions [here](https://dev.konfuzio.com/sdk/quickstart_pycharm.html).

## CLI

We provide the basic function to create a new Project via CLI:

`konfuzio_sdk create_project YOUR_PROJECT_NAME`

You will see "Project `{YOUR_PROJECT_NAME}` (ID `{YOUR_PROJECT_ID}`) was created successfully!" printed.

And download any project via the id:

`konfuzio_sdk export_project YOUR_PROJECT_ID`

## Tutorials

You can find detailed examples about how to set up and run document AI pipelines in our 
[Tutorials](https://dev.konfuzio.com/sdk/tutorials.html), including:
- [Split a file into separate Documents](https://dev.konfuzio.com/sdk/tutorials/context-aware-file-splitting-model/index.html)
- [Document Categorization](https://dev.konfuzio.com/sdk/tutorials/document_categorization/index.html)
- [Train a Konfuzio SDK model to get insights from annual reports](https://dev.konfuzio.com/sdk/tutorials/annual-reports/index.html)

### Basics

Here we show how to use the Konfuzio SDK to retrieve data hosted on a Konfuzio Server instance.

```python
from konfuzio_sdk.data import Project, Document

# Initialize the Project
YOUR_PROJECT_ID: int
my_project = Project(id_=YOUR_PROJECT_ID)

# Get any online Document
DOCUMENT_ID_ONLINE: int
doc: Document = my_project.get_document_by_id(DOCUMENT_ID_ONLINE)

# Get the Annotations in a Document
doc.annotations()

# Filter Annotations by Label
MY_OWN_LABEL_NAME: str
label = my_project.get_label_by_name(MY_OWN_LABEL_NAME)
doc.annotations(label=label)

# Or get all Annotations that belong to one Category
YOUR_CATEGORY_ID: int
category = my_project.get_category_by_id(YOUR_CATEGORY_ID)
label.annotations(categories=[category])

# Force a Project update. To save time Documents will only be updated if they have changed.
my_project.get(update=True)
```

## License

MIT License

Copyright (c) 2025 Helm & Nagel GmbH
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

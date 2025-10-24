The **seeq** Python module is used to interface with Seeq Server API ([https://www.seeq.com](https://www.seeq.com)).

Documentation can be found at
[https://python-docs.seeq.com](https://python-docs.seeq.com/).

**IMPORTANT:**

This module mirrors the versioning of Seeq Server, such that the version of this module reflects the version
of the Seeq Server from which the Seeq SDK was generated.

For Seeq Server version R60 and later, the SPy module
[is in its own namespace package](https://pypi.org/project/seeq-spy/) called `seeq-spy` with its own versioning
scheme. (Prior to R60, the SPy module was bundled into this main `seeq` module.)

# Upgrade Considerations

## When using Seeq Data lab:

If you are using **Seeq Data Lab**, you should not upgrade or otherwise affect the pre-installed version of the
`seeq` module, as the pre-installed version correctly matches the version of Seeq Server that Data Lab is tied
to.

### Older than R60

However, in older versions of Seeq Server, you must follow the (more complex) instructions on the corresponding PyPI
pages for that version:

https://pypi.org/project/seeq/55.4.9.183.34/
https://pypi.org/project/seeq/56.1.9.184.21/
https://pypi.org/project/seeq/57.2.7.184.22/
https://pypi.org/project/seeq/58.1.3.184.22/
https://pypi.org/project/seeq/59.0.1.184.25/

## When NOT using Seeq Data Lab:

If you are _not_ using **Seeq Data Lab**, you should install the version of the `seeq` module that corresponds
to the first two numbers in the version of Seeq you are interfacing with. This version can be found at the top
of the Seeq Server *API Reference* page.
E.G.: `pip install -U seeq~=65.1`. You should then upgrade SPy separately via `pip install -U seeq-spy`.

# seeq.spy

The SPy module is the recommended programming interface for interacting with the Seeq Server.
See [https://pypi.org/project/seeq-spy/](https://pypi.org/project/seeq-spy/) for more information on the SPy module.

For more advanced tasks than what the SPy module can provide, you may with to use the SDK module described below.

# seeq.sdk

The Seeq **SDK** module is a set of Python bindings for the Seeq Server REST API. You can experiment with the REST API
by selecting the *API Reference* menu item in the upper-right "hamburger" menu of Seeq Workbench.

**The SDK module supports both Python 2.x and Python 3.x, but it is strongly recommended that you use Python 3.x
(or later) as Python 2.x is end-of-life.**

Login is accomplished with the following pattern:

```
import seeq
import getpass

api_client = seeq.sdk.ApiClient('http://localhost:34216/api')

# Change this to False if you're getting errors related to SSL
seeq.sdk.Configuration().verify_ssl = True

auth_api = seeq.sdk.AuthApi(api_client)
auth_input = seeq.sdk.AuthInputV1()

# Use raw_input() instead of input() if you're using Python 2
auth_input.username = input('Username:').rstrip().lower()
auth_input.password = getpass.getpass()
auth_input.auth_provider_class = "Auth"
auth_input.auth_provider_id = "Seeq"
auth_api.login(body=auth_input)
```

The `api_client` object is then used as the argument to construct any API object you need, such as
`seeq.sdk.ItemsApi`. Each of the root endpoints that you see in the *API Reference* webpage corresponds to
a `seeq.sdk.XxxxxApi` class.

----------

In case you are looking for the Gencove package, it is available here: https://pypi.org/project/gencove/
The **seeq-spy** Python module is the recommended programming interface for interacting with the Seeq Server.

Use of this module requires a
[Seeq Data Lab license](https://support.seeq.com/space/KB/113723667/Requesting+and+Installing+a+License+File).

Documentation can be found at
[https://python-docs.seeq.com](https://python-docs.seeq.com/).

The Seeq **SPy** module is a friendly set of functions that are optimized for use with
[Jupyter](https://jupyter.org), [Pandas](https://pandas.pydata.org/) and [NumPy](https://www.numpy.org/).

The SPy module is the best choice if you're trying to do any of the following:

- Search for signals, conditions, scalars, assets
- Pull data out of Seeq
- Import data in a programmatic way (when Seeq Workbench's *CSV Import* capability won't cut it)
- Calculate new data in Python and push it into Seeq
- Create an asset model
- Programmatically create and manipulate Workbench Analyses or Organizer Topics

**Use of the SPy module requires Python 3.8 or later.**

**SPy version 187 and higher is compatible with Pandas 2.x.**

To start exploring the SPy module, execute the following lines of code in Jupyter:

```
from seeq import spy
spy.docs.copy()
```

Your Jupyter folder will now contain a `SPy Documentation` folder that has a *Tutorial* and *Command Reference*
notebook that will walk you through common activities.

For more advanced tasks, you may need to use the `seeq.sdk` module directly as described at
[https://pypi.org/project/seeq](https://pypi.org/project/seeq).

# Upgrade Considerations

The `seeq-spy` module can/should be upgraded separately from the main `seeq` module by doing `pip install -U
seeq-spy`. It is written to be compatible with Seeq Server version R60 and later.

Read the [Installation](https://python-docs.seeq.com/upgrade-considerations.html) page in the SPy documentation 
for further instructions on how to install and upgrade the `seeq-spy` module.
Check the [Change Log](https://python-docs.seeq.com/changelog.html) and 
[Version Considerations](https://python-docs.seeq.com/user_guide/Version%20Considerations.html) pages for more details.

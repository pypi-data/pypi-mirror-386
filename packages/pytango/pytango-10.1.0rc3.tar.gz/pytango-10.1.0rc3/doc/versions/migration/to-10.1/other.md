(to10.1-other)=

# Other changes

(to10.1-write_methods)=

## Attribute write methods

To make code consistent we have renamed the parameters for all write attribute methods of
`DeviceProxy`, `AttributeProxy` and `Group` to be either `attr` (for single attribute write methods)
or `attr_values`  (for multple attributes write methods):

| Method                                | Old parameter name | New parameter name |
|---------------------------------------|--------------------|--------------------|
| `DeviceProxy.write_attribute`         | attr_name          | attr               |
| `DeviceProxy.write_attributes`        | name_val           | attr_values        |
| `DeviceProxy.write_read_attribute`    | attr_name          | attr               |
| `DeviceProxy.write_read_attributes`   | name_val           | attr_values        |
| `DeviceProxy.write_attribute_asynch`  | attr_name          | attr               |
| `DeviceProxy.write_attributes_asynch` | attr_values        | attr_values        |
| `AttributeProxy.write`                | attr_name          | attr               |
| `AttributeProxy.write_read`           | attr_name          | attr               |
| `AttributeProxy.write_asynch`         | attr_name          | attr               |
| `Group.write_attribute_asynch`        | attr_name          | attr               |


And for the all methods now there is a "fast" overload, where instead of attribute name
you can give an AttributeInfoEx object (that overload existed before for
`DeviceProxy.write_attribute` and `AttributeProxy.write` methods). Due to actual attribute write being done by
cppTango, PyTango must know to which c++ data type to cast each python value. In case if only attribute name
is provided it must fetch attribute info for this attribute from server by additional synchronous IO.
But in case if AttributeInfoEx is given by user - this IO  can be skiped. Note, that for multiple
attribute write AttributeInfoEx must be provided for each pair of values.  In case if at least for one pair
just name is given - PyTango must do additional IO.

(to10.1-other-attribute-event-definition)=

## Defining attributes that push events

If a device pushes events for attributes programmatically, the standard way to indicate this was to call a
method like `set_change_event`, `set_archive_event`, etc. from the device's `init_device` method.  This is
still possible, however, there is a new alternative that makes the attribute definition self-contained.

Instead of this:

```python
from tango.server import Device, attribute

class MyDevice(Device):
    def init_device(self):
        self.set_change_event("voltage", implemented=True, detect=False)

    @attribute
    def voltage(self) -> float:
        return 1.23

    ...
```

You can now do this:

```python
from tango.server import Device, attribute

class MyDevice(Device):

    @attribute(change_event_implemented=True, change_event_detect=False)
    def voltage(self) -> float:
        return 1.23

    ...
```

These are the new keyword arguments available for {meth}`~tango.server.attribute` (they all default to `False`):
- `alarm_event_implemented`
- `alarm_event_detect`
- `archive_event_implemented`
- `archive_event_detect`
- `change_event_implemented`
- `change_event_detect`
- `data_ready_event_implemented`

(to10.1-other-command-docstrings)=

## Support setting command doc_in and doc_out from docstrings

Instead of providing documentation via the `doc_in` and `doc_out` kwargs for your commands, this can
now be taken from the doctring.


Instead of:

```python
from tango.server import Device, command

class MyDevice(Device):
    @command(
        doc_in="val_in (int): The input integer value.",
        doc_out="returns (int): An integer result after processing.",
    )
    def example(self, val_in: int) -> int:
        return val_in
```

You can do this:

```python
from tango.server import Device, command

class MyDevice(Device):
        @command
        def example(self, val_in: int) -> int:
            """
            Example command, using Google docstring syntax

            Args:
                val_in (int): The input integer value.

            Returns:
                int: An integer result after processing.
            """
            return val_in
```

You can also use ReST, Numpydoc-style, or Epydoc docstrings.
See the [docstring_parser](https://github.com/rr-/docstring_parser) library.

:::{note}
Text outside the input and return types is ignored.  E.g., the summary of the command won't be included.
The keyword arguments take priority over the docstring.
:::

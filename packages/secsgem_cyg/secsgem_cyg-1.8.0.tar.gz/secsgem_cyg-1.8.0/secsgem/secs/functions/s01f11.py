"""Class for stream 01 function 11."""

from secsgem.secs.data_items import SVID
from secsgem.secs.functions.base import SecsStreamFunction


class SecsS01F11(SecsStreamFunction):
    """status variable namelist - request.

    Args:
        value: parameters for this function (see example)

    Examples:
        >>> import secsgem.secs
        >>> secsgem.secs.functions.SecsS01F11
        [
            SVID: U1/U2/U4/U8/I1/I2/I4/I8/A
            ...
        ]

        >>> import secsgem.secs
        >>> secsgem.secs.functions.SecsS01F11([1, 1337])
        S1F11 W
          <L [2]
            <U1 1 >
            <U2 1337 >
          > .

    Data Items:
        - :class:`SVID <secsgem.secs.data_items.SVID>`

    An empty list will return all available status variables.

    """

    _stream = 1
    _function = 11

    _data_format = [SVID]

    _to_host = False
    _to_equipment = True

    _has_reply = True
    _is_reply_required = True

    _is_multi_block = False

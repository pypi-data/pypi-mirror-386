"""Class for stream 01 function 03."""

from secsgem.secs.data_items import SVID
from secsgem.secs.functions.base import SecsStreamFunction


class SecsS01F03(SecsStreamFunction):
    """Selected equipment status - request.

    Args:
        value: parameters for this function (see example)

    Examples:
        >>> import secsgem.secs
        >>> secsgem.secs.functions.SecsS01F03
        [
            SVID: U1/U2/U4/U8/I1/I2/I4/I8/A
            ...
        ]

        >>> import secsgem.secs
        >>> secsgem.secs.functions.SecsS01F03([1, "1337", 12])
        S1F3 W
          <L [3]
            <U1 1 >
            <A "1337">
            <U1 12 >
          > .

    Data Items:
        - :class:`SVID <secsgem.secs.data_items.SVID>`

    """

    _stream = 1
    _function = 3

    _data_format = [SVID]

    _to_host = False
    _to_equipment = True

    _has_reply = True
    _is_reply_required = True

    _is_multi_block = False

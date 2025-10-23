from typing import Union, TypedDict, Any, Dict, List, Required


class _Root(TypedDict, total=False):
    """ Error message from Relay """

    type: Required[str]
    """ Required property """

    payload: Required[Union[str, Union[int, float], Dict[str, Any], List[Any], bool, None]]
    """
    bytes

    Required property
    """

    event_id: Required[str]
    """ Required property """

    project_id: Required[int]
    """ Required property """

    start_time: Required[int]
    """ Required property """


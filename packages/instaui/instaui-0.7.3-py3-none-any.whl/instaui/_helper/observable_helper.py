import typing
from instaui.vars.mixin_types.observable import ObservableMixin
from instaui.vars.mixin_types.py_binding import CanInputMixin, CanOutputMixin
from instaui.ui_functions.input_slient_data import InputSilentData

from instaui.vars.mixin_types.common_type import TObservableInput


def analyze_observable_inputs(
    inputs: list[TObservableInput],
) -> typing.Tuple[list[ObservableMixin], list[int], list[int]]:
    """
    Returns:
        inputs, slients, datas
    """

    slients: list[int] = [0] * len(inputs)
    datas: list[int] = [0] * len(inputs)
    result_inputs = []

    for idx, input in enumerate(inputs):
        if isinstance(input, ObservableMixin):
            result_inputs.append(input)
            continue

        if isinstance(input, CanInputMixin):
            slients[idx] = 1
            result_inputs.append(input)

            if isinstance(input, InputSilentData) and input.is_const_value():
                datas[idx] = 1

        else:
            datas[idx] = 1
            result_inputs.append(input)

    return result_inputs, slients, datas


def auto_made_inputs_to_slient(
    inputs: typing.Optional[typing.Sequence[TObservableInput]],
    outputs: typing.Optional[typing.Sequence[CanOutputMixin]],
):
    if inputs is None or outputs is None:
        return inputs

    return [InputSilentData(input) if input in outputs else input for input in inputs]

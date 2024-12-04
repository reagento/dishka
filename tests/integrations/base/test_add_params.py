from inspect import Parameter, Signature, signature

import pytest

from dishka.integrations.base import _add_params


def func(
    pos_only,
    /,
    pos_keyword,
    *,
    keyword_only,
) -> None: ...


def func_expected(
    pos_only,
    add_pos_only,
    /,
    pos_keyword,
    add_pos_keyword,
    *add_var_pos,
    keyword_only,
    add_keyword_only,
    **add_var_keyword,
) -> None: ...


def func_with_args_kwargs(*args, **kwargs): ...


def test_add_all_params():
    additional_params = [
        Parameter("add_pos_only", Parameter.POSITIONAL_ONLY),
        Parameter("add_pos_keyword", Parameter.POSITIONAL_OR_KEYWORD),
        Parameter("add_var_pos", Parameter.VAR_POSITIONAL),
        Parameter("add_keyword_only", Parameter.KEYWORD_ONLY),
        Parameter("add_var_keyword", Parameter.VAR_KEYWORD),
    ]
    func_signature = signature(func)
    func_params = list(func_signature.parameters.values())

    result_params = _add_params(func_params, additional_params)
    new_signature = Signature(
        parameters=result_params,
        return_annotation=func_signature.return_annotation,
    )

    assert new_signature == signature(func_expected)


def test_fail_add_second_args():
    additional_params = [
        Parameter("add_var_pos", Parameter.VAR_POSITIONAL),
    ]

    func_signature = signature(func_with_args_kwargs)
    func_params = list(func_signature.parameters.values())

    with pytest.raises(
        ValueError, match="more than one var positional parameter",
    ):
        _add_params(func_params, additional_params)


def test_fail_add_second_kwargs():
    additional_params = [
        Parameter("add_var_keyword", Parameter.VAR_KEYWORD),
    ]

    func_signature = signature(func_with_args_kwargs)
    func_params = list(func_signature.parameters.values())

    with pytest.raises(
        ValueError, match="more than one var keyword parameter",
    ):
        _add_params(func_params, additional_params)

from frformat import Canton, Options

PROPORTION = 0.9
_options = Options(
    ignore_case=True,
    ignore_accents=True,
    replace_non_alphanumeric_with_space=True,
    ignore_extra_whitespace=True
)
_canton = Canton(_options)


def _is(val):
    '''Match avec le nom des cantons'''

    return _canton.is_valid(val)

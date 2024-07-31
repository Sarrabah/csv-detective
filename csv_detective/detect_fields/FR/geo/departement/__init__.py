from frformat import Departement, Options

PROPORTION = 0.9

_options = Options(
    ignore_case=True,
    ignore_accents=True,
    replace_non_alphanumeric_with_space=True,
    ignore_extra_whitespace=True
)
_departement = Departement(_options)


def _is(val):
    '''Match avec le nom des departements'''

    return _departement.is_valid(val)

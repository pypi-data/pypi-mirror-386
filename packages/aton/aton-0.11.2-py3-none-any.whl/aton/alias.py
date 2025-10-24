"""
# Description

This module contains common dictionaries to normalise and correct user inputs.
All values can be found in lowercase, to allow comparison with the `string.lower()` method.
Inverse of an unit X, as in 1/X or X$^{-1}$, is expressed as `X1`.
See all available options with `dict.keys()`.


# Index

`units`  
`spatial`  
`experiments`  
`files`  
`boolean`  
`math`  


# Examples

```python
unit = 'Electronvolts'
if unit.lower() in aton.alias.units['eV']:
    ... do stuff ...
```

---
"""


units: dict = {
    'mol'  : ['mol', 'mols', 'mole', 'moles'],
    'g'    : ['g', 'gram', 'grams'],
    'kg'   : ['kg', 'kilogram', 'kilograms'],
    'amu'  : ['amu', 'atomicmassunit', 'atomicmassunits'],
    'eV'   : ['eV', 'ev', 'electronvolt', 'electronvolts'],
    'meV'  : ['meV', 'mev', 'millielectronvolt', 'millielectronvolts'],
    'ueV'  : ['ueV', 'uev', 'microelectronvolts', 'mueV', 'muev'],
    'J'    : ['J', 'j', 'joule', 'joules'],
    'cal'  : ['cal', 'calorie', 'calories'],
    'kcal' : ['kcal', 'kilocalorie', 'kilocalories'],
    'Ry'   : ['Ry', 'ry', 'rydberg', 'rydbergs'],
    'cm'   : ['cm', 'centimeter', 'centimeters'],
    'cm1'  : ['cm^{-1}', 'cm1', 'cm-1', 'cm^-1'],
    'AA'   : ['A', 'AA', 'a', 'aa', 'angstrom', 'angstroms', 'armstrong', 'armstrongs'],
    'AA1'  : ['AA1', 'A1', 'AA-1', 'A-1', 'aa1', 'a1', 'aa-1', 'a-1'],
    'bohr' : ['bohr', 'bohrs', 'bohrradii'],
    'm'    : ['m', 'meter', 'meters'],
    'deg'  : ['deg', 'degree', 'degrees'],
    'rad'  : ['rad', 'radian', 'radians'],
    'bar'  : ['bar', 'bars'],
    'kbar' : ['kbar', 'kilobar', 'kilobars'],
    'Pa'   : ['Pa', 'pa', 'pascal', 'pascals'],
    'GPa'  : ['GPa', 'gpa', 'gigapascal', 'gigapascals'],
    's'    : ['s', 'second', 'seconds'],
    'H'    : ['H', 'h', 'hour', 'hours'],
}
"""Dict with unit names."""


spatial: dict = {
    'height' : ['height', 'h'],
    'area'   : ['area', 'a'],
    'volume' : ['volume', 'vol'],
    'x'      : ['x', 'horizontal', 'h'],
    'y'      : ['y', 'vertical', 'v'],
    'z'      : ['z'],
}
"""Dict with different spatial parameters. Values must be compared to `string.lower()`."""


chemical: dict = {
    'CH3' : ['ch', 'CH', 'ch3', 'CH3', 'methyl'],
    'NH3' : ['nh', 'NH', 'nh3', 'NH3', 'amine'],
    'CD3' : ['cd', 'CD', 'cd3', 'CD3', 'deuterated methyl'],
    'ND3' : ['nd', 'ND', 'nd3', 'ND3', 'deuterated amine'],
}
"""Dict with chemical groups."""


experiments: dict = {
    'ins'   : ['ins', 'inelasticneutronscattering', 'inelastic neutron scattering'],
    'atr'   : ['atr', 'ftir', 'attenuatedtotalreflection', 'attenuated total reflection'],
    'raman' : ['raman'],
    'qens'  : ['qens', 'quasielasticneutronscattering', 'quasielastic neutron scattering', 'quasi elastic neutron scattering'],
}
"""Dictionary with the available experiment types. Values must be compared to `string.lower()`."""


files: dict = {
    'file'  : ['file', 'files', 'f', 'filepath', 'file path', 'filename', 'file name'],
    'dir'   : ['dir', 'directory', 'd', 'folder'],
    'error' : ['error', 'errors', 'e', 'err'],
    }
"""Strings related to files. Values must be compared to `string.lower()`."""


boolean: dict = {
    True  : ['yes', 'YES', 'Yes', 'Y', 'y', 'T', 'True', 'TRUE', 't', 'true', 'Si', 'SI', 'si', 'S', 's'],
    False : ['no', 'NO', 'No', 'N', 'n', 'F', 'False', 'FALSE', 'f', 'false'],
}
"""Strings with booleans such as 'yes' / 'no'."""


math: dict = {
    'sin'  : ['sin', 'sen', 'sine', 'seno'],
    'cos'  : ['cos', 'cosine', 'coseno'],
    'tg'   : ['tg', 'tangent', 'tangente'],
    '0' : ['zero', 'cero', '0'],
}
"""Math-related strings."""


# funx

[![PyPI version](https://badge.fury.io/py/funx.svg)](https://badge.fury.io/py/funx)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The main reason why this library was created is to :

### use

```python
from funx import isinstances


def add(num1: int, num2: int) -> int:
    if isinstances(num1, num2, datatype=int):  # 41 char
        return num1 + num2
    raise TypeError("invalid arguments types")


print(add(3, 7))
```

### in place of

```python
def add(num1: int, num2: int) -> int:
    if isinstance(num1, int) and isinstance(num2, int):  # 51 char
        return num1 + num2
    raise TypeError("invalid arguments types")


print(add(3, 7))
```

### and

```python
from funx import isinstances


def fun(name: str, age: int) -> None:
    if isinstances(name, age, datatype=(str, int)):  # 47 char
        print(f"your name is {name} and your age is {age}")
        return
    raise TypeError("invalid arguments types")


fun("mohamed", 23)
```

### in place of

```python
def fun(name: str, age: int) -> None:
    if isinstance(name, str) and isinstance(age, int):  # 50 char
        print(f"your name is {name} and your age is {age}")
        return
    raise TypeError("invalid arguments types")


fun("mohamed", 23)
```

but not just this there is other funcs and with a very advanced usage you can see the source code and check all the tests in the main fun

## Installation

You can install `funx` via pip:

```bash
pip install funx
```

## License

This project is licensed under the MIT LICENSE - see the [LICENSE](https://opensource.org/licenses/MIT) for more details.

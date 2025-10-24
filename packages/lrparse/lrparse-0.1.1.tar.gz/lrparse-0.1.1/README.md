# lrparse

**lrparse** is a tiny, fast Python library written in C for extracting substrings between *left* and *right* delimiters.

It provides two functions:
- `lr()`  – returns the **first** substring between delimiters.  
- `lrr()` – returns **all** substrings between delimiters.

---

##  Installation

```bash
pip install lrparse
```

##  Usage

```python
import lrparse

# lr() → first match between delimiters
print(lrparse.lr("pre[mid]post", "[", "]"))
# ['mid']

# lrr() → all matches between delimiters
print(lrparse.lrr("<a><b>c", "<", ">"))
# ['a', 'b']

# If delimiters don't exist, you get an empty list
print(lrparse.lr("hello world", "{", "}"))
# []

# If both delimiters are empty, the whole string is returned
print(lrparse.lr("abc", "", ""))
# ['abc']
```
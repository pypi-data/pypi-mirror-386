# listele Fonksiyonu

---

```python
def listele(li:list|dict, kolon:int, ljustmz:int=30, *, find:str="")
```
```python
# Usage example:

from listele import listele

import sysconfig
li = dir(sysconfig)  # list type object
di = sysconfig.get_paths()  # dict type object

print("Output1:")
listele(li, 4)

print("\n\nOutput2:")
listele(li, 4, find="path")

print("\n\nOutput3:")
listele(di, 2, 70)

print("\n\nOutput4:")
listele(di, 1, find="include")

```

---

## Kullanım

li kısmına bir iterable verirsiniz (mesela bir dir() ifadesi).
Terminalinizde kaç kolon halinde gözükmesini istediğinizi belirtirsiniz.
Ve eğer isterseniz yazılan değerler arasındaki uzaklığı değiştirebilirsiniz.

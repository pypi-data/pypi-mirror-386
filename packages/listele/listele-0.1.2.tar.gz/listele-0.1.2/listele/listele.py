# Bir listenin elemanlarını kolonlar halinde sıralayan fonksiyon:

import sys

def listele(li:list|dict, kolon:int, ljustmz:int=30, *, find:str=""):
    """ listele(li:list|dict, kolon:int, ljustmz:int=30, *, find:str="")

    Usage example:

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
    """

    try:
        iter(li)
    except TypeError:
        print("E: Non-iterable argument was given.", file= sys.stderr)
        return


    if isinstance(li, dict):
        li = [f"{key}: {item}" for key, item in li.items()]


    if find:
        find = find.lower()
        li = [i for i in li if find in i.lower()]


    if (
        not isinstance(kolon, int)
        or not isinstance(ljustmz, int)
        or 1 >= kolon > len(li)
        or ljustmz < 0
    ):
        print("E: Incorrect arguments.", file= sys.stderr)
        return


    for i in range(0, (len(li) - kolon+1), kolon):
        for j in range(kolon):
            st = str(li[i + j]).ljust(ljustmz)
            print(st, end="")
        print()


    remainder = len(li) % kolon
    if remainder:
        for i in range(remainder, 0, -1):
            st = str(li[-i]).ljust(ljustmz)
            print(st, end="")
    print()


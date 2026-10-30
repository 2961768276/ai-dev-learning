def good(lst=None):
    if lst is None:
        lst=[]
    lst.append(1)
    return lst

print(good())
print(good())

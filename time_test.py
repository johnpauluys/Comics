from datetime import datetime
from random import randint

i = 5000


time = datetime.now()
l = [i for i in range(1, i + 1)]
print("[list]", datetime.now() - time)

time = datetime.now()
l = [i for i in range(i)]
print("[list]", datetime.now() - time)


time = datetime.now()
l = [i + 1 for i in range(i)]
print("[list]", datetime.now() - time)


time = datetime.now()
r = list(range(i))
print("list()", datetime.now() - time)


time = datetime.now()
r = list(range(1, i + 1))
print("list()", datetime.now() - time)


mylist = [randint(1, 1000) for i in range(10000)]

count_list_function = 0
count_list_custom = 0
count_list_preset = 0

time = datetime.now()
for i in mylist:
    if i in [j for j in range(1, 1001)]:
        pass
print("[list]", datetime.now() - time)

time = datetime.now()
for i in mylist:
    if i in list(range(1, 1001)):
        pass
print("list()", datetime.now() - time)


time = datetime.now()
check = list(range(1, 1001))
for i in mylist:
    if i in check:
        pass
print("preset", datetime.now() - time)





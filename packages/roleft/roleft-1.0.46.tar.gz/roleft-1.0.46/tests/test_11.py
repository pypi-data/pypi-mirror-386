from typing import Iterable, TypeVar

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


from roleft.Fuck.Student_defs import Student

from Utilities.AU import AU
from Utilities.CU import CU

from roleft import Entities


from Extentions.xstr_defs import xstr
import Extentions

print(roleft.Extentions.__file__)


stu = Student("jack", 34)

hehe = xstr("abcdeft")
print(hehe.x_is_email)
print(hehe.x_is_ipv4)
print(hehe.x_to_base64)
print(hehe.x_from_base64)
print(hehe.x_sub_string(2))
print(hehe.x_sub_string(2, 3))
print(hehe.x_reverse)
print(hehe)
pass

import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

sys.stdout.reconfigure(encoding='utf-8')

from tools import search_rentals

print(search_rentals('Hai Bà Trưng, Hà Nội', 6000000, 'homestay'))

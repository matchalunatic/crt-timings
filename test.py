import logging
from crttimings import crttimings


logging.basicConfig(level=logging.DEBUG)

a = crttimings.new_detailed_resolution()
a.set_timing(4)
a.set_h_active(600)
a.set_v_active(240)
a.set_v_rate(60.0)
a.set_interlaced(True)

a.set_timing(0)
a.set_v_rate(600.0)

print(a)

#a.set_timing(0)
#a.set_h_front(10)
#a.set_h_sync(10)
#a.set_h_back(10)
#
#a.set_v_front(3)
#a.set_v_sync(3)
#a.set_v_back(3)



#print(a)

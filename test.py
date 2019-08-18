import logging
from crttimings import crttimings, opere


logging.basicConfig(level=logging.DEBUG)

a = crttimings.new_detailed_resolution()
a.set_timing(4)
a.set_h_active(600)
a.set_v_active(240)
a.set_v_rate(60000)

a.set_timing(0)
a.set_v_rate(60000)

old_a = str(a)

a.set_timing(0)
opera = opere.OpereTVResolution(pixel_clock=1920)
opera.call(a)

new_a = str(a)

print("*** OLD ***")
print(old_a)
print("*** NEW ***")
print(new_a)
print("*** DER ***")
print(opera.goals_values)
print(opera.goals_derivatives)

#a.set_timing(0)
#a.set_h_front(10)
#a.set_h_sync(10)
#a.set_h_back(10)
#
#a.set_v_front(3)
#a.set_v_sync(3)
#a.set_v_back(3)



#print(a)

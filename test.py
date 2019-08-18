from crttimings import crttimings

a = crttimings.DetailedResolution()

a.set_v_active(480)
a.set_h_active(600)
a.set_v_rate(50)
a.set_interlaced(True)


print(a)

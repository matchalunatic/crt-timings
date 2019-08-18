"""crttimings: compute good resolution timings for a given resolution on
   CRT displays.
   
   By no means a perfect utility, built to serve my own purpose but might
   be useful and could maybe be improved to support more stuff.

   Equations and computations come from ToastyX's Custom Resolution Utility.
   More inspiration:
   - http://www.geocities.ws/podernixie/htpc/modes-en.html#escpal
   - http://www.epanorama.net/faq/vga2rgb/calc.html

   Usage:
     crttimings --hres=<hres> --vres=<vres> --pixel-clock=<hertz>... [--interlace|--no-interlace]

"""
import functools
import json
import logging

from .constants import Constants, Constants2

logger = logging.getLogger(__name__)


class DetailedResolutionInterface(object):
    def connect(self, detres):
        self.detailed_resolution = detres

    def refresh(self):
        self.refreshing = True




def inrange(value, min_v, max_v):
    if value == Constants.BLANK:
        return min_v
    elif value <= min_v:
        return min_v
    elif value >= max_v:
        return max_v
    return value




def requires_hvr(method=None, when_not_met=False, raise_exception=None):
    if method is None:
        return functools.partial(requires_hvr, when_not_met=when_not_met, raise_exception=raise_exception)
    @functools.wraps(method)
    def f(self, *args, **kwargs):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            if raise_exception is not None:
                raise raise_exception
            logger.debug("requires_hvr: conditions not met:\n\tHActive: %s\n\tVActive: %s\n\tVRate: %s", self.is_supported_h_active(), self.is_supported_v_active(), self.is_supported_v_rate())
            return when_not_met
        return method(self, *args, **kwargs)
    return f

def new_detailed_resolution():
    a = DetailedResolution(int(True))
    a.v_active = 1080
    a.h_active = 1920
    a.v_rate = 600
    a.set_timing(4)
    a.start()
    return a

class DetailedResolution(object):
    """This is mostly a port of DetailedResolutionClass.cpp from ToastyX's CRU
       
       Computations are naively ported and the states change the same as in
       that class.

       Todo:
        port the properties set_xxx to proper @property (maybe in a wrapper class)
        make a nice text interface
        work usability
        operational research
    """
    def __init__(self, newtype):
        self.type = newtype
        self.timing = 0
        self.last = 0
        self.h_active = Constants.BLANK
        self.h_front = Constants.BLANK
        self.h_sync = Constants.BLANK
        self.h_back = Constants.BLANK
        self.h_blank = Constants.BLANK
        self.h_total = Constants.BLANK
        
        self.h_polarity = False
        
        self.v_active = Constants.BLANK
        self.v_front = Constants.BLANK
        self.v_sync = Constants.BLANK
        self.v_back = Constants.BLANK
        self.v_blank = Constants.BLANK
        self.v_total = Constants.BLANK
        
        self.v_polarity = False
        
        self.stereo = 0
        self.last_rate = 0
        
        self.v_rate = Constants.BLANK
        self.actual_v_rate = Constants.BLANK
        self.h_rate = Constants.BLANK
        self.actual_h_rate = Constants.BLANK
        
        self.p_clock = Constants.BLANK
        
        self.interlaced = False
        self.native = False
        
        self.v_active_i  = Constants.BLANK
        self.v_front_i   = Constants.BLANK
        self.v_sync_i    = Constants.BLANK
        self.v_back_i    = Constants.BLANK
        self.v_blank_i   = Constants.BLANK
        self.v_total_i   = Constants.BLANK
        self.v_rate_i    = Constants.BLANK

        self.reset_available = False
        self.reset_h_active = Constants.BLANK
        self.reset_h_front = Constants.BLANK
        self.reset_h_sync = Constants.BLANK
        self.reset_h_blank = Constants.BLANK
        self.reset_h_polarity = False
        self.reset_v_active = Constants.BLANK
        self.reset_v_front = Constants.BLANK
        self.reset_v_sync = Constants.BLANK
        self.reset_v_blank = Constants.BLANK
        self.reset_v_polarity = False
        self.reset_stereo = False
        self.reset_p_clock = Constants.BLANK
        self.reset_interlaced = False
        self.reset_native = False


    def start(self):
        self.calculate_h_back()
        self.calculate_h_total()
        self.calculate_v_back()
        self.calculate_v_total()
        self.calculate_actual_v_rate()
        self.calculate_actual_h_rate()
        self.v_rate = (self.actual_v_rate + 500) // 1000 * 1000
        self.h_rate = self.actual_h_rate
        old_p_clock = self.p_clock
        self.calculate_p_clock_from_v_rate()
        if self.p_clock != old_p_clock:
            if self.v_rate % 24000 == 0 or self.v_rate % 30000 == 0:
                self.v_rate = self.v_rate * 1000 // 1001
                self.calculate_p_clock_from_v_rate()

        if self.p_clock != old_p_clock:
            self.v_rate = (self.actual_v_rate + 50) // 100 * 100
            self.calculate_p_clock_from_v_rate()

        if self.p_clock != old_p_clock:
            self.v_rate = self.actual_v_rate
            self.p_clock = old_p_clock

        self.update_interlaced()
        self.update_interlaced_rate()
        return True


    def _as_dict(self):
        return dict(
        h_active=self.h_active,
        h_front=self.h_front,
        h_sync=self.h_sync,
        h_back=self.h_back,
        h_blank=self.h_blank,
        h_total=self.h_total,
        h_polarity=self.h_polarity,
        v_active=self.v_active,
        v_front=self.v_front,
        v_sync=self.v_sync,
        v_back=self.v_back,
        v_blank=self.v_blank,
        v_total=self.v_total,
        v_polarity=self.v_polarity,
        stereo=self.stereo,
        last_rate=self.last_rate,
        v_rate=self.v_rate,
        actual_v_rate=self.actual_v_rate,
        h_rate=self.h_rate,
        actual_h_rate=self.actual_h_rate,
        p_clock=self.p_clock,
        interlaced=self.interlaced,
        native=self.native,
        v_active_i=self.v_active_i,
        v_front_i=self.v_front_i,
        v_sync_i=self.v_sync_i,
        v_back_i=self.v_back_i,
        v_blank_i=self.v_blank_i,
        v_total_i=self.v_total_i,
        v_rate_i=self.v_rate_i
        )
        
    def __str__(self):
        fs = ("Parameters\n"
              "\tHorizontal\tVertical\n"
              "Active:    \t{a.h_active}\t{a.v_active}\n"
              "Front porch:\t{a.h_front}\t{a.v_front}\n"
              "Sync width:\t{a.h_sync}\t{a.v_sync}\n"
              "Back porch:\t{a.h_back}\t{a.v_back}\n"
              "Blanking:\t{a.h_blank}\t{a.v_blank}\n"
              "Total:\t\t{a.h_total}\t{a.v_total}\n"
              "Sync polarity:\t{h_pol}\t{v_pol}\n"
              "\n"
              "\n"
              "Frequency:\n"
              "Refresh rate:\t{a.v_rate}\tActual: {a.actual_v_rate}\n"
              "Horizontal:\t{a.h_rate}\tActual: {a.actual_h_rate}\n"
              "Pixclock: \t{a.p_clock}\tInterlaced: {a.interlaced}")
        
        return fs.format(a=self,
                         h_pol="+" if self.h_polarity else "-",
                         v_pol="+" if self.v_polarity else "-")
        return json.dumps(self._as_dict(), indent=4, sort_keys=True)
        



    def is_last_rate(self, value):
        return value == self.last_rate

    def get_actual_v_rate_text(self):
        if self.actual_v_rate != Constants.BLANK:
            return '{i}.{d} kHz'.format(i=self.actual_v_rate / 1000, d=self.actual_v_rate % 1000)
        else:
            return '- kHz'
    
    def get_actual_h_rate_text(self):
        if self.actual_h_rate != Constants.BLANK:
            return '{i}.{d} kHz'.format(i=self.actual_h_rate / 1000, d=self.actual_h_rate % 1000)
        else:
            return '- kHz'

    def get_timing_text(self, timing):
        if not Constants.MIN_TIMING <= timing <= Constants.MAX_TIMING:
            return None
        return self.timing_texts[timing]

    def get_timing(self):
        if not self.is_valid_timing():
            return -1
        return self.timing

    def set_timing(self, value):
        self.timing = value
        self.update()
        self.update_interlaced()
        self.update_interlaced_rate()
        return True
    
    def set_last(self, value):
        self.last = value
        self.timing = 0
        self.update_interlaced()
        return True

    def set_h_active(self, value):
        self.h_active = int(value)
        self.update()
        self.update_interlaced()
        return True

    def set_h_front(self, value):
        self.h_front = value
        self.timing = 0
        self.update()
        self.update_interlaced()
        return True

    def set_h_sync(self, value):
        self.h_sync = value
        self.timing = 0
        self.update()
        self.update_interlaced()
        return True

    def set_h_back(self, value):
        self.h_back = value
        self.timing = 0
        self.last = 0
        self.update()
        self.update_interlaced()
        return True

    def set_h_blank(self, value):
        self.h_blank = value
        self.timing = 0
        self.last = 1
        self.update()
        self.update_interlaced()
        return True

    def set_h_total(self, value):
        self.h_total = value
        self.timing = 0
        self.last = 2
        self.update()
        self.update_interlaced()
        return True

    def set_h_polarity(self, value):
        self.h_polarity = value
        self.timing = 0
        return True

    def set_h_polarity(self, value):
        self.h_polarity = value
        self.timing = 0
        return True

    def set_v_active(self, value):
        self.v_active = int(value)
        self.update()
        self.update_interlaced()
        return True

    def set_v_front(self, value):
        self.v_front = value
        self.timing = 0
        self.update()
        self.update_interlaced()
        return True

    def set_v_sync(self, value):
        self.v_sync = value
        self.timing = 0
        self.update()
        self.update_interlaced()
        return True

    def set_v_back(self, value):
        self.v_back = value
        self.timing = 0
        self.last = 0
        self.update()
        self.update_interlaced()
        return True

    def set_v_blank(self, value):
        self.v_blank = value
        self.timing = 0
        self.last = 1
        self.update()
        self.update_interlaced()
        return True

    def set_v_total(self, value):
        self.v_total = value
        self.timing = 0
        self.last = 2
        self.update()
        self.update_interlaced()
        return True

    def set_v_polarity(self, value):
        self.v_polarity = value
        self.timing = 0
        return True

    def set_last_rate(self, value):
        self.last_rate = value
        self.timing = 0
        self.update_interlaced_rate()
        return True

    def set_v_rate(self, value):
        """Indicate VRate in 1/1000 Hz (60000 = 60Hz)"""
        self.v_rate = value
        if self.timing == 0:
            self.last_rate = 0
        self.update()
        self.update_interlaced_rate()
        return True

    def set_h_rate(self, value):
        """Indicate HRate in 1/1000 Hz (15000000 = 15000 Hz = 15 kHz)"""
        self.h_rate = value
        self.last_rate = 1
        self.update()
        self.update_interlaced_rate()
        return True

    def set_p_clock(self, value):
        """Indicate PClock in 10 kHz steps (960 = 9.6 MHz)"""
        self.p_clock = value
        self.last_rate = 2
        self.update()
        self.update_interlaced_rate()
        return True


    def interlaced_possible(self):
        return Constants.INTERLACED_AVAILABLE[self.type]

    def get_interlaced(self):
        return self.interlaced

    def set_interlaced(self, value):
        # the original code uses xor swaps. let's be more conservative
        # as this is not supported in python and harms portability
        self.interlaced = bool(value)
        n = self.v_active
        self.v_active = self.v_active_i
        self.v_active_i = n

        n = self.v_front
        self.v_front = self.v_front_i
        self.v_front_i = n

        n = self.v_sync
        self.v_sync = self.v_sync_i
        self.v_sync_i = n

        n = self.v_back
        self.v_back = self.v_back_i
        self.v_back_i = n

        n = self.v_blank
        self.v_blank = self.v_blank_i
        self.v_blank_i = n

        n = self.v_total
        self.v_total = self.v_total_i
        self.v_total_i = n

        n = self.v_rate
        self.v_rate = self.v_rate_i
        self.v_rate_i = n

        return self.update()

    def native_possible(self):
        return Constants.NATIVE_AVAILABLE[self.type]

    def get_native(self):
        return self.native

    def set_native(self, value):
        self.native = value
        return True

    @property
    def interlaced_i(self):
        if self.interlaced:
            return 1
        else:
            return 0

    def recompute_blanking_and_clock(self):
        self.calculate_h_blank()
        self.calculate_h_total()
        self.calculate_v_blank()
        self.calculate_v_total()
        self.calculate_p_clock_from_v_rate()


    @property
    def timing_functions(self):
        return (
            None,
            self.calculate_lcd_standard,
            self.calculate_lcd_native,
            self.calculate_lcd_reduced,
            self.calculate_crt_standard,
            self.calculate_old_standard,
        )
    
    @property
    def timing_texts(self):
        return (
            'Manual',
            'Automatic - LCD standard',
            'Automatic - LCD native',
            'Automatic - LCD reduced',
            'Automatic - CRT standard',
            'Automatic - Old standard',
                )
    

    def reset(self):
        if not self.reset_available:
            return False
        self.timing = 0
        self.h_active = self.reset_h_active
        self.h_front = self.reset_h_front
        self.h_sync = self.reset_h_sync
        self.h_blank = self.reset_h_blank
        self.h_polarity = self.reset_h_polarity
        self.v_active = self.reset_v_active
        self.v_front = self.reset_v_front
        self.v_sync = self.reset_v_sync
        self.v_blank = self.reset_v_blank
        self.v_polarity = self.reset_v_polarity
        self.stereo = self.reset_stereo
        self.p_clock = self.reset_p_clock
        self.interlaced = self.reset_interlaced
        self.native = self.reset_native
        self.start()
        return True

    def update_reset(self):
        self.reset_available = True
        self.reset_h_active = self.h_active
        self.reset_h_front = self.h_front
        self.reset_h_sync = self.h_sync
        self.reset_h_blank = self.h_blank
        self.reset_h_polarity = self.h_polarity
        self.reset_v_active = self.v_active
        self.reset_v_front = self.v_front
        self.reset_v_sync = self.v_sync
        self.reset_v_blank = self.v_blank
        self.reset_v_polarity = self.v_polarity
        self.reset_stereo = self.stereo
        self.reset_p_clock = self.p_clock
        self.reset_interlaced = self.interlaced
        self.reset_native = self.native
        return True


    def update(self):
        ok = True
        if self.timing:
            if not (self.is_valid_timing() and self.timing_functions[self.timing] is not None):
                logger.debug("Invalid timing")
                ok = False
            if ok:
                func = self.timing_functions[self.timing]
                logger.debug("Timing function is %s", str(func.__name__))
                ok = func()
            if not ok:
                logger.debug("Timing function failed.")
                self.h_front = self.h_sync = self.h_back = self.h_total = Constants.BLANK
                self.v_front = self.v_sync = self.v_back = self.v_total = Constants.BLANK
                self.p_clock = self.actual_v_rate = self.actual_h_rate = self.h_rate = Constants.BLANK
                return False
            logger.debug("Timing function succeeded")
            return True

        logger.debug("Computing timings")
        if self.last == 0:
            logger.debug("0: computing H/V blank and total")
            self.calculate_h_blank()
            self.calculate_h_total()
            self.calculate_v_blank()
            self.calculate_v_total()
        elif self.last == 1:
            logger.debug("1: computing H/V back and total")
            self.calculate_h_back()
            self.calculate_h_total()
            self.calculate_v_back()
            self.calculate_v_total()
        elif self.last == 2:
            logger.debug("2: computing H/V back and blank")
            self.calculate_h_back_from_h_total()
            self.calculate_h_blank()
            self.calculate_v_back_from_v_total()
            self.calculate_v_blank()

        if self.last_rate == 0:
            logger.debug("0: computing PClock, setting h_rate")
            self.calculate_p_clock_from_v_rate()
            self.calculate_actual_v_rate()
            self.calculate_actual_h_rate()
            self.h_rate = self.actual_h_rate
        elif self.last_rate == 1:
            logger.debug("1: computing PClock, setting v_rate")
            self.calculate_p_clock_from_h_rate()
            self.calculate_actual_v_rate()
            self.calculate_actual_h_rate()
            self.v_rate = self.actual_v_rate
        elif self.last_rate == 2:
            logger.debug("2: setting v_rate and h_rate")
            self.calculate_actual_v_rate()
            self.calculate_actual_h_rate()
            self.v_rate = self.actual_v_rate
            self.h_rate = self.actual_h_rate

        return True

    def update_interlaced(self):
        logger.debug("update_interlaced")
        self.v_active_i = self.v_active
        self.v_front_i = self.v_front
        self.v_sync_i = self.v_sync
        self.v_back_i = self.v_back

        if self.is_supported_v_active() and self.interlaced:
            if self.v_active == 540 and self.v_front == 2 and self.v_sync == 5 and self.v_back == 15:
                logger.debug("interlaced: qHD")
                self.v_active_i = 1080
                self.v_front_i = 4
                self.v_sync_i = 5
                self.v_back_i = 36
            elif self.v_active < Constants.MAX_V_ACTIVE[self.type] // 2:
                self.v_active_i = self.v_active * 2
        elif self.is_supported_v_active() and self.v_active % 2 == 0:
            if self.v_active == 1080 and self.v_front == 4 and self.v_sync == 5 and self.v_back == 36:
                self.v_active_i = 540
                self.v_front_i = 2
                self.v_sync_i = 5
                self.v_back_i = 15
            elif self.is_supported_h_active():
                if (self.v_active * 125 > self.h_active * 51 or self.h_active in (1440, 2880)) and (472 <= self.v_active <= 488 or 566 <= self.v_active <= 586):
                    self.v_active_i = int(self.v_active // 2)
            else:
                if 472 <= self.v_active <= 488 or self.v_active >= 566:
                    self.v_active_i = self.v_active // 2
        
        self.v_blank_i = self.v_front_i + self.v_sync_i + self.v_back_i
        self.v_total_i = self.v_active_i + self.v_blank_i
        return True


    def update_interlaced_rate(self):
        self.v_rate_i = self.v_rate
        if self.is_supported_v_rate() and not self.interlaced and self.v_rate < 45000:
            self.v_rate_i = self.v_rate * 2
        return True

    @requires_hvr
    def calculate_native(self, digital):
        searched = None
        for index, item in enumerate(Constants.LCD_NATIVE):
            h, v, i = item[0:3]
            if self.h_active == h and self.v_active == v and self.interlaced == i and vrmn <= self.v_rate <= vrmx:
                searched = item
                break
        
        if searched is not None:
            self.v_rate = searched[3]
            self.h_front = searched[4]
            self.h_sync = searched[5]
            self.h_back = searched[6]
            self.v_front = searched[7]
            self.v_sync = searched[8]
            self.v_back = searched[9]
            self.h_polarity = searched[10]
            self.v_polarity = searched[11]
            self.recompute_blanking_and_clock()
        else:
            self.v_rate = 60000
            if digital or self.h_sync <= 48:
                self.calculate_lcd_standard()
            else:
                self.calculate_crt_standard()
            self.p_clock = self.p_clock // 25 * 25
        self.stereo = 0
        self.calculate_actual_v_rate()
        self.calculate_actual_h_rate()
        self.v_rate = self.actual_v_rate
        self.h_rate = self.actual_h_rate
        self.update_interlaced()
        self.update_interlaced_rate()
        self.update_reset()
        return True

    @requires_hvr
    def calculate_lcd_standard(self):
        self.h_polarity = True
        self.v_polarity = False

        searched = None
        for index, item in enumerate(Constants.LCD_STANDARD):
            h, v, i, vrmn, vrmx = item[0:5]
            if self.h_active == h and self.v_active == v and self.interlaced == i and vrmn <= self.v_rate <= vrmx:
                searched = item
                break
        if searched is not None:
            self.h_front = searched[5]
            self.h_sync = searched[6]
            self.h_back = searched[7]
            self.v_front = searched[8]
            self.v_sync = searched[9]
            self.v_back = searched[10]
            self.h_polarity = searched[11]
            self.v_polarity = searched[12]
            self.recompute_blanking_and_clock()
        else:
            old_v_rate = self.v_rate
            self.calculate_cvtrb()
            self.calculate_p_clock_from_v_rate()
            self.calculate_actual_v_rate()
            self.v_rate = self.actual_v_rate
            self.calculate_cvtrb()
            self.calculate_p_clock_from_v_rate()
            self.v_rate= old_v_rate
        self.calculate_actual_v_rate()
        self.calculate_actual_h_rate()
        self.h_rate = self.actual_h_rate
        return self.is_valid_rate()

    @requires_hvr
    def calculate_lcd_native(self):
        self.h_polarity = True
        self.v_polarity = False

        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return False

        searched = None
        for index, item in enumerate(Constants.LCD_NATIVE):
            h, v, i = item[0:3]
            if self.h_active == h and self.v_active == v and self.interlaced == i:
                searched = item
                break
        if searched is not None:
            self.h_front = searched[4]
            self.h_sync = searched[5]
            self.h_back = searched[6]
            self.v_front = searched[7]
            self.v_sync = searched[8]
            self.v_back = searched[9]
            self.h_polarity = searched[10]
            self.v_polarity = searched[11]
            self.recompute_blanking_and_clock()
        else:
            old_v_rate = self.v_rate
            self.v_rate = 60000
            self.calculate_cvtrb()
            self.calculate_p_clock_from_v_rate()
            self.calculate_actual_v_rate()
            self.v_rate = self.actual_v_rate
            self.calculate_cvtrb()
            self.v_rate = old_v_rate
            self.calculate_p_clock_from_v_rate()

        self.calculate_actual_v_rate()
        self.calculate_actual_h_rate()
        self.h_rate = self.actual_h_rate
        return self.is_valid_rate()

    @requires_hvr
    def calculate_lcd_reduced(self):
        """needs review and has been factorized"""
        self.h_polarity = True
        self.v_polarity = False

        searched = None
        for index, item in enumerate(Constants.LCD_REDUCED):
            h, v, i, vrmn, vrmx = item[0:5]
            if self.h_active == h and self.v_active == v and self.interlaced == i and vrmn <= self.v_rate <= vrmx:
                searched = item
                break

        if searched is not None:
            self.h_front = searched[5]
            self.h_sync = searched[6]
            self.h_back = searched[7]
            self.v_front = searched[8]
            self.v_sync = searched[9]
            self.v_back = searched[10]
            self.h_polarity = searched[11]
            self.v_polarity = searched[12]
            self.recompute_blanking_and_clock()
        else:
            old_v_rate = self.v_rate
            self.calculate_cvtrb()
            self.calculate_p_clock_from_v_rate()
            self.calculate_actual_v_rate()
            self.v_rate = self.actual_v_rate
            self.calculate_cvtrb()
            self.calculate_p_clock_from_v_rate()
            self.v_rate = old_v_rate
            self.fix_lcd_reduced_v_rate()
        self.calculate_actual_v_rate()
        self.calculate_actual_h_rate()
        self.h_rate = self.actual_h_rate
        return self.is_valid_rate()

    def fix_lcd_reduced_v_rate(self):
        """Magic brute-force function to find nice LCD timings that will work
        
           Apparently for v_front, v_sync, v_back, minimal acceptable value would
           be 3
        """
        if self.v_rate > 60500 and self.h_active * self.v_active > 2457600:
            while self.p_clock > 33000:
                # make one parameter vary
                if self.v_blank > 15:
                    self.v_back -= 1
                elif self.h_back > 48:
                    self.h_back -= 8
                    self.v_back = self.get_v_back_for_cvtrb()
                elif self.v_front >= self.v_sync and self.v_front >= self.v_back - 1 and self.v_front > 3:
                    self.v_front -= 1
                elif self.v_sync >= self.v_front and self.v_sync >= self.v_back and self.v_sync > 3:
                    self.v_sync -= 1 
                elif self.v_back >= self.v_front and self.v_back >= self.v_sync and self.v_back > 3:
                    self.v_back -= 3
                else:
                    # can't optimize further
                    break
                # recompute timings
                self.recompute_blanking_and_clock()
            # enter here if previous optimization failed
            if p_clock > 33000:
                old_v_rate = self.v_rate
                self.calculate_cvtrb()
                self.calculate_p_clock_from_v_rate()
                self.calculate_actual_v_rate()
                self.v_rate = self.actual_v_rate
                self.calculate_cvtrb()
                self.calculate_p_clock_from_v_rate()
                self.v_rate = old_v_rate
            # start over an optimization cycle with target p_clock > 40000
            while self.p_clock > 40000:
                if self.v_blank > 21:
                    self.v_back -= 1
                elif self.h_back > 56:
                    self.h_back -= 8
                    self.v_back = self.get_v_back_for_cvtrb()
                else:
                    break
                self.recompute_blanking_and_clock()
            # enter here if unsuccessful
            if p_clock > 40000:
                old_v_rate = self.v_rate
                self.calculate_cvtrb()
                self.calculate_p_clock_from_v_rate()
                self.calculate_actual_v_rate()
                self.v_rate = self.actual_v_rate
                self.calculate_cvtrb()
                self.calculate_p_clock_from_v_rate()
                self.v_rate = old_v_rate
            # third optimization cycle, target: p_clock > 40400
            while self.p_clock > 40400:
                if self.v_blank > 21:
                    self.v_back -= 1
                elif self.h_back > 56:
                    self.h_back -= 8
                    self.v_back = self.get_v_back_for_cvtrb()
                else:
                    break
                self.recompute_blanking_and_clock()
            # are we beyond WQHD?
            if self.h_active * self.v_active > 3686400 and self.p_clock > 40400:
                self.h_front = 48
                self.h_sync = 32
                self.h_back = 48
                self.v_front = 3
                self.v_sync = 3
                self.v_back = 3
                self.recompute_blanking_and_clock()
            # WQHD with faster pixel clock
            if self.h_active * self.v_active > 3686400 and self.p_clock > 54000:
                self.h_front = 16
                self.h_sync = 24
                self.h_back = 24
                self.v_front = 3
                self.v_sync = 3
                self.v_back = 3
                self.h_polarity = True
                self.v_polarity = True
                self.recompute_blanking_and_clock()

            # WQHD or less
            if self.h_active * self.v_active <= 3686400 and self.p_clock > 40400:
                self.h_front = 48
                self.h_sync = 32
                self.h_back = 64
                self.v_front = 2
                self.v_sync = 2
                self.v_back = 2
                self.recompute_blanking_and_clock()
            # test for faster pixel clock
            if self.h_active * self.v_active <= 3686400 and self.p_clock > 54000:
                self.h_front = 4
                self.h_sync = 16
                self.h_back = 2
                self.v_front = 1
                self.v_sync = 1
                self.v_back = 7
                self.h_polarity = True
                self.v_polarity = True
                self.recompute_blanking_and_clock()
        elif self.v_rate > 60500 and self.p_clock > 16500:
            # HD test
            if self.h_active == 1920 and self.v_active == 1080:
                self.h_polarity = True
                self.v_polarity = True
            self.h_front = 32
            self.h_sync = 40
            self.h_back = 48
            self.v_front = self.get_v_front_for_cvt()
            self.v_sync = self.get_v_sync_for_cvt()
            self.v_back = self.get_v_back_for_cvt()
            self.recompute_blanking_and_clock()
            while self.p_clock > 16500:
                # change one parameter (the bigger one) without setting h parameters less than 1 (px)
                # and v parameters less than 3 (lines)
                if self.h_front >= self.h_sync and self.h_front >= self.h_back and self.h_front > 8:
                    self.h_front -= 8
                elif self.h_sync >= self.h_front and self.h_sync >= self.h_back and self.h_sync > 8:
                    self.h_sync -= 8
                elif self.h_back >= self.h_front and self.h_back >= self.h_sync and self.h_back > 8:
                    self.h_back -= 8
                elif self.v_front >= self.v_sync and self.v_front >= self.v_back and self.v_front > 3:
                    self.v_front -= 1
                elif self.v_sync >= self.v_front and self.v_sync >= self.v_back and self.v_sync > 3:
                    self.v_sync -= 1
                elif self.v_back >= self.v_front and self.v_back >= self.v_sync and self.v_back > 3:
                    self.v_back -= 1
                else:
                    # no further optimization possible
                    break
                self.recompute_blanking_and_clock()
            if self.p_clock > 16500:
                # set known fixed working parameters
                self.h_front = 24
                self.h_sync = 32
                self.h_back = 32
                self.v_front = self.get_v_front_for_cvt()
                self.v_sync = self.get_v_sync_for_cvt()
                self.v_back = self.get_v_back_for_cvt()
                self.recompute_blanking_and_clock()


    @requires_hvr
    def calculate_crt_standard(self):
        self.h_polarity = False
        self.v_polarity = True

        searched = None
        for index, item in enumerate(Constants.CRT_STANDARD):
            h, v, i, vrmn, vrmx = item[0:5]
            if self.h_active == h and self.v_active == v and self.interlaced == i and vrmn <= self.v_rate <= vrmx:
                searched = item
                break

        if searched is not None:
            self.h_front = searched[5]
            self.h_sync = searched[6]
            self.h_back = searched[7]
            self.v_front = searched[8]
            self.v_sync = searched[9]
            self.v_back = searched[10]
            self.h_polarity = searched[11]
            self.v_polarity = searched[12]
            self.calculate_h_blank()
            self.calculate_h_total()
            self.calculate_v_blank()
            self.calculate_v_total()
            self.calculate_p_clock_from_v_rate()
        else:
            old_v_rate = self.v_rate
            self.calculate_cvt()
            self.calculate_p_clock_from_v_rate()
            self.calculate_actual_v_rate()
            self.v_rate = self.actual_v_rate
            self.calculate_cvt()
            self.calculate_p_clock_from_v_rate()
            self.v_rate = old_v_rate

        self.calculate_actual_v_rate()
        self.calculate_actual_h_rate()
        self.h_rate = self.actual_h_rate
        logger.debug("calculate CRT Standard:\n\tVRate: %s\n\tHRate: %s\n\tPClock: %s\n\t",self.v_rate, self.h_rate, self.p_clock)
        return self.is_valid_rate()



    @requires_hvr
    def calculate_old_standard(self):
        self.h_polarity = False
        self.v_polarity = True

        searched = None
        for index, item in enumerate(Constants.OLD_STANDARD):
            h, v, i, vrmn, vrmx = item[0:5]
            if self.h_active == h and self.v_active == v and self.interlaced == i and vrmn <= self.v_rate <= vrmx:
                searched = item
                break
        if searched is not None:
            self.h_front = searched[5]
            self.h_sync = searched[6]
            self.h_back = searched[7]
            self.v_front = searched[8]
            self.v_sync = searched[9]
            self.v_back = searched[10]
            self.h_polarity = searched[11]
            self.v_polarity = searched[12]
            self.calculate_h_blank()
            self.calculate_h_total()
            self.calculate_v_blank()
            self.calculate_v_total()
            self.calculate_p_clock_from_v_rate()
        else:
            old_v_rate = self.v_rate
            self.calculate_gtf()
            self.calculate_p_clock_from_v_rate()
            self.calculate_actual_v_rate()
            self.v_rate = sef.actual_v_rate
            self.calculate_gtf()
            self.calculate_p_clock_from_v_rate()
            self.v_rate = old_v_rate

        self.calculate_actual_v_rate()
        self.calculate_actual_h_rate()
        self.h_rate = self.actual_h_rate
        return self.is_valid_rate()


    @requires_hvr
    def calculate_cvt(self):
        self.h_polarity = False
        self.v_polarity = True

        self.h_front = self.get_h_front_for_cvt()
        self.h_sync = self.get_h_sync_for_cvt()
        self.h_back = self.get_h_back_for_cvt()
        self.v_front = self.get_v_front_for_cvt()
        self.v_sync = self.get_v_sync_for_cvt()
        self.v_back = self.get_v_back_for_cvt()
        self.calculate_h_blank()
        self.calculate_h_total()
        self.calculate_v_blank()
        self.calculate_v_total()
        self.calculate_p_clock_for_cvtrb()
        self.calculate_actual_v_rate()
        self.calculate_actual_h_rate()
        self.h_rate = self.actual_h_rate
        return self.is_valid_rate()



    @requires_hvr
    def calculate_cvtrb(self):
        self.h_polarity = True
        self.v_polarity = False

        self.h_front = 48
        self.h_sync = 32
        self.h_back = 80
        self.v_front = self.get_v_front_for_cvt()
        self.v_sync = self.get_v_sync_for_cvt()
        self.v_back = self.get_v_back_for_cvtrb()
        self.calculate_h_blank()
        self.calculate_h_total()
        self.calculate_v_blank()
        self.calculate_v_total()
        self.calculate_p_clock_for_cvtrb()
        self.calculate_actual_v_rate()
        self.calculate_actual_h_rate()
        self.h_rate = self.actual_h_rate
        return self.is_valid_rate()

    @requires_hvr
    def calculate_gtf(self):
        self.h_polarity = False
        self.v_polarity = True

        self.h_front = self.get_h_front_for_gtf()
        self.h_sync = self.get_h_sync_for_gtf()
        self.h_back = self.get_h_back_for_gtf()
        self.v_front = self.get_v_front_for_gtf()
        self.v_back = self.get_v_back_for_gtf()
        self.calculate_h_blank()
        self.calculate_v_blank()
        self.calculate_v_total()
        self.calculate_p_clock_for_gtf()
        self.calculate_actual_v_rate()
        self.calculate_actual_h_rate()
        self.h_rate = self.actual_h_rate
        return self.is_valid_rate()


    @requires_hvr(when_not_met=Constants.BLANK)
    def get_h_period_for_cvt(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        return (1000000000000000000 * 2 // self.v_rate - 550000000000 * 2) // (self.v_active * 2 + self.get_v_front_for_cvt() * 2 + self.interlaced_i);



    @requires_hvr(when_not_met=Constants.BLANK)
    def get_h_period_for_cvtrb(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        return (1000000000000000000 * 2 // self.v_rate - 460000000000 * 2) // (self.v_active * 2)

    @requires_hvr(when_not_met=Constants.BLANK)
    def get_h_period_for_gtf(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        return (1000000000000000000 * 2 // self.v_rate - 550000000000 * 2) // (self.v_active * 2 + self.get_v_front_for_gtf() * 2 + self.interlaced_i)


    @requires_hvr(when_not_met=Constants.BLANK)
    def get_h_front_for_cvt(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        return self.get_h_back_for_cvt() - self.get_h_sync_for_cvt()

    @requires_hvr(when_not_met=Constants.BLANK)
    def get_h_front_for_gtf(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        return self.get_h_back_for_gtf() - self.get_h_sync_for_gtf()

    @requires_hvr(when_not_met=Constants.BLANK)
    def get_h_sync_for_cvt(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        return (self.h_active + self.get_h_blank_for_cvt()) // 100 * 8

    @requires_hvr(when_not_met=Constants.BLANK)
    def get_h_sync_for_gtf(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        return (self.h_active + self.get_h_blank_for_gtf() + 50) // 100 * 8


    @requires_hvr(when_not_met=Constants.BLANK)
    def get_h_back_for_cvt(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        return self.get_h_blank_for_cvt() // 2

    @requires_hvr(when_not_met=Constants.BLANK)
    def get_h_back_for_gtf(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        return self.get_h_blank_for_gtf() // 2

    @requires_hvr(when_not_met=Constants.BLANK)
    def get_h_blank_for_cvt(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK

        ideal_duty_cycle = Constants2.C_PRIME * 1000000000000 - Constants2.M_PRIME * self.get_h_period_for_cvt()

        if ideal_duty_cycle < 20000000000000:
            ideal_duty_cycle = 20000000000000

        return self.h_active * ideal_duty_cycle // (100000000000000 - ideal_duty_cycle) // 16 * 16
    
    @requires_hvr(when_not_met=Constants.BLANK)
    def get_h_blank_for_gtf(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK

        ideal_duty_cycle = Constants2.C_PRIME * 1000000000000 - Constants2.M_PRIME * self.get_h_period_for_gtf()

        return (self.h_active * ideal_duty_cycle // (100000000000000 - ideal_duty_cycle) + 8) // 16 * 16


    @requires_hvr(when_not_met=Constants.BLANK)
    def get_v_front_for_cvt(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        return 3

    @requires_hvr(when_not_met=Constants.BLANK)
    def get_v_front_for_gtf(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        return 1


    @requires_hvr(when_not_met=Constants.BLANK)
    def get_v_sync_for_cvt(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        if self.interlaced:
            aspect = self.v_active * 8000 // self.h_active
        else:
            aspect = self.v_active * 4000 // self.h_active
        for mn, mx, vl in Constants.ASPECT_V_SYNC:
            if aspect >= mn and aspect <= mx:
                return vl
        return 10


    @requires_hvr(when_not_met=Constants.BLANK)
    def get_v_sync_for_gtf(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        return 3


    @requires_hvr(when_not_met=Constants.BLANK)
    def get_v_back_for_cvt(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        vsyncvback = 5500000000000 // self.get_h_period_for_cvt() + 1
        vback = vsyncvback - self.get_v_sync_for_cvt()

        if vback < 6:
            vback = 6
        return vback


    @requires_hvr(when_not_met=Constants.BLANK)
    def get_v_back_for_cvtrb(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        
        v_blank = 460000000000 // self.get_period_for_cvtrb() + 1
        v_back = v_blank - self.get_v_front_for_cvt() - self.get_v_sync_for_cvt()
        if v_back < 6:
            v_back = 6
        return v_back

    @requires_hvr(when_not_met=Constants.BLANK)
    def get_v_back_for_gtf(self):
        if not (self.is_supported_h_active() and self.is_supported_v_active() and self.is_supported_v_rate()):
            return Constants.BLANK
        vsyncvback = (5500000000000 // self.get_h_period_for_gtf() + 5) // 10
        vback = vsyncvback - self.get_v_sync_for_gtf()
        return vback

    def calculate_h_back(self):
        if not (self.is_supported_h_total() and self.is_supported_h_active() and self.is_supported_h_front() and self.is_supported_h_sync()):
            self.h_back = Constants.BLANK
            return False
        self.h_back = self.h_total - self.h_active - self.h_front - self.h_sync

        if not self.is_supported_h_back():
            self.h_back = Constants.BLANK
            return False
        return True

    def calculate_h_back_from_h_total(self):
        if not (self.is_supported_h_total() and self.is_supported_h_active() and self.is_supported_h_front() and self.is_supported_h_sync()):
            self.h_back = Constants.BLANK
            return False
        self.h_back = self.h_total - self.h_active - self.h_front - self.h_sync

        if not self.is_supported_h_back():
            self.h_back = Constants.BLANK
            return False
        return True

    def calculate_h_blank(self):
        if not (self.is_supported_h_front() and self.is_supported_h_sync() and self.is_supported_h_back()):
            self.h_blank = Constants.BLANK
            return False
        self.h_blank = self.h_front + self.h_sync + self.h_back

        if not self.is_supported_h_blank():
            self.h_blank = Constants.BLANK
            return False
        return True

    def calculate_h_total(self):
        if not (self.is_supported_h_active() and self.is_supported_h_front() and self.is_supported_h_sync() and self.is_supported_h_back()):
            self.h_total = Constants.BLANK
            return False
        self.h_total = self.h_active + self.h_front + self.h_sync + self.h_back

        if not self.is_supported_h_total():
            self.h_total = Constants.BLANK
            return False
        return True

    def calculate_v_back(self):
        if not (self.is_supported_v_blank() and self.is_supported_v_front() and self.is_supported_v_sync()):
            self.v_back = Constants.BLANK
            return False
        self.v_back = self.v_blank - self.v_front - self.v_sync

        if not self.is_supported_v_back():
            self.v_back = Constants.BLANK
            return False
        return True

    def calculate_v_back_from_v_total(self):
        if not (self.is_supported_v_total() and self.is_supported_v_active() and self.is_supported_v_front() and self.is_supported_v_sync()):
            self.v_back = Constants.BLANK
            return False
        self.v_back = self.v_total - self.v_active - self.v_front - self.v_sync

        if not self.is_supported_v_back():
            self.v_back = Constants.BLANK
            return False
        return True

    def calculate_v_blank(self):
        if not (self.is_supported_v_front() and self.is_supported_v_sync() and self.is_supported_v_back()):
            self.v_blank = Constants.BLANK
            return False
        self.v_blank = self.v_front + self.v_sync + self.v_back

        if not self.is_supported_v_blank():
            self.v_blank = False
            return False
        return True
    
    def calculate_v_total(self):
        if not (self.is_supported_v_active() and self.is_supported_v_front() and self.is_supported_v_sync() and self.is_supported_v_back()):
            self.v_total = Constants.BLANK
            return False
        self.v_total = self.v_active + self.v_front + self.v_sync + self.v_back

        if not self.is_supported_v_total():
            self.v_total = Constants.BLANK
            return False
        return True
        
    def calculate_p_clock_for_cvt(self):
        if not(self.is_supported_v_rate() and self.is_supported_h_total() and self.is_supported_v_total()):
            self.p_clock = Constants.BLANK
            return False
        self.p_clock = self.h_total * 100000000000 // self.get_h_period_for_cvt() // 25 * 25
        if not self.is_supported_p_clock():
            self.p_clock = Constants.BLANK
            return False
        return True

    def calculate_p_clock_for_cvtrb(self):
        if not(self.is_supported_v_rate() and self.is_supported_h_total() and self.is_supported_v_total()):
            self.p_clock = Constants.BLANK
            return False
        self.p_clock = self.v_rate * self.h_total * (self.v_total * 2 + self.interlaced_i) // 20000000 // 25 * 25
        if not self.is_supported_p_clock():
            self.p_clock = Constants.BLANK
            return False
        return True

    def calculate_p_clock_for_gtf(self):
        if not(self.is_supported_v_rate() and self.is_supported_h_total() and self.is_supported_v_total()):
            self.p_clock = Constants.BLANK
            return False
        self.p_clock = (self.v_rate * self.h_total * (self.v_total * 2 + self.interlaced_i) + 10000000) // 2000000
        if not self.is_supported_p_clock():
            self.p_clock = Constants.BLANK
            return False
        return True

    def calculate_p_clock_from_v_rate(self):
        if not(self.is_supported_v_rate() and self.is_supported_h_total() and self.is_supported_v_total()):
            self.p_clock = Constants.BLANK
            return False
        self.p_clock = (self.v_rate * self.h_total * (self.v_total * 2 + self.interlaced_i) + 19999999) // 20000000

        if not self.is_supported_p_clock():
            self.p_clock = Constants.BLANK
            return False
        return True

    def calculate_p_clock_from_h_rate(self):
        if not(self.is_supported_h_total() and self.is_supported_h_rate()):
            self.p_clock = Constants.BLANK
            return False
        self.p_clock = (self.h_rate * self.h_total + 9999) // 10000

        if not self.is_supported_p_clock():
            self.p_clock = Constants.BLANK
            return False
        return True

    def calculate_actual_v_rate(self):
        if not(self.is_supported_p_clock() and self.is_supported_h_total() and self.is_supported_v_total()):
            self.actual_v_rate = Constants.BLANK
            return False
        self.actual_v_rate = self.p_clock * 20000000 // self.h_total // (self.v_total * 2 + self.interlaced_i)
        if not self.is_supported_actual_v_rate():
            self.actual_v_rate = Constants.BLANK
            return False
        return True

    def calculate_actual_h_rate(self):
        if not(self.is_supported_p_clock() and self.is_supported_h_total()):
            self.actual_h_rate = Constants.BLANK
            return False
        self.actual_h_rate = self.p_clock * 10000 // self.h_total
        if not self.is_supported_actual_h_rate():
            self.actual_h_rate = Constants.BLANK
            return False
        return True

    def is_supported(self):
        return (
                self.is_supported_h_active() and self.is_supported_h_front() and
                self.is_supported_h_sync() and self.is_supported_h_back() and
                self.is_supported_h_blank() and self.is_supported_h_total() and
                self.is_supported_v_active() and self.is_active_v_sync() and
                self.is_active_v_front() and self.is_active_v_back() and
                self.is_supported_v_blank() and self.is_supported_v_total() and
                self.is_supported_v_rate() and self.is_supported_h_rate() and
                self.is_supported_p_clock() and self.is_supported_actual_h_rate() and
                self.is_supported_actual_v_rate()
                )
               

    def is_valid(self):
        return (
                self.is_valid_h_active() and self.is_valid_h_front() and
                self.is_valid_h_sync() and self.is_valid_h_back() and
                self.is_valid_h_blank() and self.is_valid_h_total() and
                self.is_valid_v_active() and self.is_active_v_sync() and
                self.is_active_v_front() and self.is_active_v_back() and
                self.is_valid_v_blank() and self.is_valid_v_total() and
                self.is_valid_v_rate() and self.is_valid_h_rate() and
                self.is_valid_p_clock() and self.is_valid_actual_h_rate() and
                self.is_valid_actual_v_rate()
                )
               

    def is_valid_timing(self):
        return Constants.MIN_TIMING <= self.timing <= Constants.MAX_TIMING
        pass

    def is_valid_h_active(self):
        return Constants.MIN_H_ACTIVE[self.type] <= self.h_active <= Constants.MAX_H_ACTIVE[self.type]

    def is_valid_h_front(self):
        return Constants.MIN_H_FRONT[self.type] <= self.h_front <= Constants.MAX_H_FRONT[self.type]

    def is_valid_h_sync(self):
        return Constants.MIN_H_SYNC[self.type] <= self.h_sync <= Constants.MAX_H_SYNC[self.type]

    def is_valid_h_back(self):
        return Constants.MIN_H_BACK[self.type] <= self.h_back <= Constants.MAX_H_BACK[self.type]

    def is_valid_h_total(self):
        return Constants.MIN_H_TOTAL[self.type] <= self.h_total <= Constants.MAX_H_TOTAL[self.type]

    def is_valid_v_active(self):
        return Constants.MIN_V_ACTIVE[self.type] <= self.v_active <= Constants.MAX_V_ACTIVE[self.type]
        pass

    def is_valid_v_front(self):
        return Constants.MIN_V_FRONT[self.type] <= self.v_front <= Constants.MAX_V_FRONT[self.type]

    def is_valid_v_back(self):
        return self.get_min_v_back(self.type) <= self.v_back <= self.get_max_v_back(self.type)

    def is_valid_v_blank(self):
        return self.get_min_v_blank(self.type) <= self.v_blank <= self.get_max_v_blank(self.type)

    def is_valid_v_total(self):
        return self.get_min_v_total(self.type) <= self.v_total <= self.get_max_v_total(self.type)

    def is_valid_rate(self):
        if (self.timing == 0 and self.last_rate == 0):
            if not (self.is_valid_h_total() and self.is_valid_v_total()):
                return self.is_valid_v_rate()
        elif (self.v_rate == 0 and self.last_rate == 1):
            if not self.is_valid_h_total():
                return self.is_valid_h_rate()
        elif (self.v_rate == 0 and self.last_rate == 2):
            if not (self.is_valid_h_total() and self.is_valid_v_total()):
                return self.is_valid_p_clock()
        elif (self.timing != 0):
            if not (self.is_valid_h_active() and self.is_valid_v_active()):
                return self.is_valid_v_rate()
        return self.is_valid_v_rate() and self.is_valid_h_rate() and self.is_valid_p_clock() and self.is_valid_actual_v_rate() and self.is_valid_actual_h_rate()

    def is_valid_v_rate(self):
        return Constants.MIN_V_TOTAL[self.type] <= self.v_total <= Constants.MAX_V_TOTAL[self.type]
        pass

    def is_valid_h_rate(self):
        return Constants.MIN_H_RATE[self.type] <= self.h_rate <= Constants.MAX_H_RATE[self.type]

    def is_valid_p_clock(self):
        return Constants.MIN_P_CLOCK[self.type] <= self.p_clock <= Constants.MAX_P_CLOCK[self.type]

    def is_valid_actual_v_rate(self):
        return Constants.MIN_V_RATE[self.type] <= self.actual_v_rate <= Constants.MAX_V_RATE[self.type]
        pass

    def is_valid_actual_h_rate(self):
        return Constants.MIN_H_RATE[self.type] <= self.actual_h_rate <= Constants.MAX_H_RATE[self.type]
        pass

    def is_supported_h_active(self):
        return Constants.MIN_H_ACTIVE[1] <= self.h_active <= Constants.MAX_H_ACTIVE[1]

    def is_supported_h_front(self):
        return Constants.MIN_H_FRONT[1] <= self.h_front <= Constants.MAX_H_FRONT[1]
 
    def is_supported_h_sync(self):
        return Constants.MIN_H_SYNC[1] <= self.h_sync <= Constants.MAX_H_SYNC[1]

    def is_supported_h_back(self):
        return self.get_min_h_back(1) <= self.h_back <= self.get_max_h_back(1)
 
    def is_supported_h_blank(self):
        return self.get_min_h_blank(1) <= self.h_blank <= self.get_max_h_blank(1)
 
    def is_supported_h_total(self):
        return self.get_min_h_total(1) <= self.h_total <= self.get_max_h_total(1)
 
    def is_supported_v_active(self):
        return Constants.MIN_V_ACTIVE[1] <= self.v_active <= Constants.MAX_V_ACTIVE[1]

    def is_supported_v_front(self):
        return Constants.MIN_V_FRONT[1] <= self.v_front <= Constants.MAX_V_FRONT[1]
 
    def is_supported_v_sync(self):
        return Constants.MIN_V_SYNC[1] <= self.v_sync <= Constants.MAX_V_SYNC[1]

    def is_supported_v_back(self):
        return self.get_min_v_back(1) <= self.v_back <= self.get_max_v_back(1)
 
    def is_supported_v_blank(self):
        return self.get_min_v_blank(1) <= self.v_blank <= self.get_max_v_blank(1)
 
    def is_supported_v_total(self):
        return self.get_min_v_total(1) <= self.v_total <= self.get_max_v_total(1)

    def is_supported_v_rate(self):
        return Constants.MIN_V_RATE[1] <= self.v_rate <= Constants.MAX_V_RATE[1]
 
    def is_supported_h_rate(self):
        return Constants.MIN_H_RATE[1] <= self.h_rate <= Constants.MAX_H_RATE[1]
 
    def is_supported_p_clock(self):
        return Constants.MIN_P_CLOCK[1] <= self.p_clock <= Constants.MAX_P_CLOCK[1]

    def is_supported_actual_v_rate(self):
        return Constants.MIN_V_RATE[1] <= self.actual_v_rate <= Constants.MAX_V_RATE[1]

    def is_supported_actual_h_rate(self):
        return Constants.MIN_H_RATE[1] <= self.actual_h_rate <= Constants.MAX_H_RATE[1]

    def get_min_h_back(self, type):
        return Constants.MIN_H_BACK[type]

    def get_max_h_back(self, type):
        inrangehfront = inrange(self.h_front, Constants.MIN_H_FRONT[type], Constants.MAX_H_FRONT[type])
        inrangehsync = inrange(self.h_sync, Constants.MIN_H_SYNC[type], Constants.MAX_H_SYNC[type])
        return min(Constants.MAX_H_BACK[type], Constants.MAX_H_BLANK[type] - inrangehfront - inrangehsync)

    def get_min_h_blank(self, type):
        inrangehfront = inrange(self.h_front, Constants.MIN_H_FRONT[type], Constants.MAX_H_FRONT[type])
        inrangehsync = inrange(self.h_sync, Constants.MIN_H_SYNC[type], Constants.MAX_H_SYNC[type])
        return max(Constants.MIN_H_BLANK[type], inrangehfront + inrangehsync + Constants.MIN_H_BACK[type])
    
    def get_max_h_blank(self, type):
        return Constants.MAX_H_BLANK[type]

    def get_min_h_total(self, type):
        inrangehactive = inrange(self.h_active, Constants.MIN_H_ACTIVE[type], Constants.MAX_H_ACTIVE[type])
        inrangehfront = inrange(self.h_front, Constants.MIN_H_FRONT[type], Constants.MAX_H_FRONT[type])
        inrangehsync = inrange(self.h_sync, Constants.MIN_H_SYNC[type], Constants.MAX_H_SYNC[type])
        return max(Constants.MIN_H_TOTAL[type], inrangehactive + inrangehfront + inrangehsync + Constants.MIN_H_BACK[type])

    def get_max_h_total(self, type):
        if self.h_active < Constants.MIN_H_ACTIVE[type] or self.h_active > Constants.MAX_H_ACTIVE[type]:
            return Constants.MAX_H_TOTAL[type]
        inrangehactive = inrange(self.h_active, Constants.MIN_H_ACTIVE[type], Constants.MAX_H_ACTIVE[type])
        return min(Constants.MAX_H_TOTAL[type], inrangehactive + Constants.MAX_H_BLANK[type])
        

    def get_min_v_back(self, type):
        return Constants.MIN_V_BACK[type]

    def get_max_v_back(self, type):
        inrangevfront = inrange(self.v_front, Constants.MIN_V_FRONT[type], Constants.MAX_V_FRONT[type])
        inrangevsync = inrange(self.v_sync, Constants.MIN_V_SYNC[type], Constants.MAX_V_SYNC[type])
        return min(Constants.MAX_V_BACK[type], Constants.MAX_V_BLANK[type] - inrangevfront - inrangevsync)

    def get_min_v_blank(self, type):
        inrangevfront = inrange(self.v_front, Constants.MIN_V_FRONT[type], Constants.MAX_V_FRONT[type])
        inrangevsync = inrange(self.v_sync, Constants.MIN_V_SYNC[type], Constants.MAX_V_SYNC[type])
        return max(Constants.MIN_V_BLANK[type], inrangevfront + inrangevsync + Constants.MIN_V_BACK[type])

    def get_max_v_blank(self, type):
        return Constants.MAX_V_BLANK[type]

    def get_min_v_total(self, type):
        inrangevactive = inrange(self.v_active, Constants.MIN_V_ACTIVE[type], Constants.MAX_V_ACTIVE[type])
        inrangevfront = inrange(self.v_front, Constants.MIN_V_FRONT[type], Constants.MAX_V_FRONT[type])
        inrangevsync = inrange(self.v_sync, Constants.MIN_V_SYNC[type], Constants.MAX_V_SYNC[type])
        return max(Constants.MIN_V_TOTAL[type], inrangevactive + inrangevfront + inrangevsync + Constants.MIN_V_BACK[type])

    def get_max_v_total(self, type):
        if self.v_active < Constants.MIN_V_ACTIVE[type] or self.v_active > Constants.MAX_V_ACTIVE[type]:
            return Constants.MAX_V_TOTAL[type]
        inrangevactive = inrange(self.v_active, Constants.MIN_V_ACTIVE[type], Constants.MAX_V_ACTIVE[type])
        return min(Constants.MAX_V_TOTAL[type], inrangevactive + Constants.MAX_V_BLANK[type])



__all__ = ['DetailedResolution', 'new_detailed_resolution']

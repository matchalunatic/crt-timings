import functools
"""crttimings: compute good resolution timings for a given resolution on
   CRT displays.
   
   By no means a perfect utility, built to serve my own purpose but migh_t
   be useful and could maybe be improved to support more stuff.

   Equations and computations come from ToastyX's Custom Resolution Utility.
   More inspiration:
   - h_ttp://www.geocities.ws/podernixie/h_tpc/modes-en.h_tml#escpal
   - h_ttp://www.epanorama.net/faq/vga2rgb/calc.h_tml

   Usage:
     crttimings --hres=<hres> --vres=<vres> --pixel-clock=<hertz>... [--interlace|--no-interlace]

"""

class Constants(object):
    BLANK = int(-2147483647)

    MIN_TIMING = 0
    MAX_TIMING = 0

    MIN_H_ACTIVE = 1
    MAX_H_ACTIVE = 65536
    MIN_H_FRONT = 1
    MAX_H_FRONT = 32768
    MIN_H_SYNC = 1
    MAX_H_SYNC = 65536
    MIN_H_BACK = 0
    MAX_H_BACK = 65534
    MIN_H_BLANK = 2
    MAX_H_BLANK = 65536
    MIN_H_TOTAL = 3
    MAX_H_TOTAL = 131072
    
    MIN_V_ACTIVE = 1
    MAX_V_ACTIVE = 65536
    MIN_V_FRONT = 1
    MAX_V_FRONT = 63
    MIN_V_SYNC = 1
    MAX_V_SYNC = 63
    MIN_V_BACK = 0
    MAX_V_BACK = 65534
    MIN_V_BLANK = 2
    MAX_V_BLANK = 65536
    MIN_V_TOTAL = 3
    MAX_V_TOTAL = 131072

    MIN_V_RATE = 1
    MAX_V_RATE = 10000000
    MIN_H_RATE = 1
    MAX_H_RATE = 10000000
    MIN_P_CLOCK = 1
    MAX_P_CLOCK = 16777216
    
    ASPECT_V_SYNC = (
      (2205, 2295, 5), # 2250 (16:9)
      (2352, 2448, 7), # 2400 (15:9)
      (2450, 2550, 6), # 2500 (16:10)
      (2940, 3060, 4), # 3000 (4:3)
      (3136, 3264, 7), # 3200 (5:4)

    )

    C = 40
    J = 20
    K = 128
    M = 600

    LCD_STANDARD = (
            (3840, 2160, 0, 59500, 60500, 176,  88, 296,  8, 10, 72, 1, 1), # 3840x2160 @ 60 Hz
            (3840, 2160, 0, 29500, 30500, 176,  88, 296,  8, 10, 72, 1, 1), # 3840x2160 @ 30 Hz
            (1920, 1080, 0, 59500, 60500,  88,  44, 148,  4,  5, 36, 1, 1), # 1920x1080 @ 60 Hz
            (1920, 1080, 0, 47500, 50500, 528,  44, 148,  4,  5, 36, 1, 1), # 1920x1080 @ 50 Hz
            #	(1920, 1080, 0, 47500, 48500, 638,  44, 148,  4,  5, 36, 1, 1), # 1920x1080 @ 48 Hz (non-standard)
            (1920, 1080, 0, 29500, 30500,  88,  44, 148,  4,  5, 36, 1, 1), # 1920x1080 @ 30 Hz
            (1920, 1080, 0, 24500, 25500, 528,  44, 148,  4,  5, 36, 1, 1), # 1920x1080 @ 25 Hz
            (1920, 1080, 0, 23500, 24500, 638,  44, 148,  4,  5, 36, 1, 1), # 1920x1080 @ 24 Hz
            (1920,  540, 1, 59500, 60500,  88,  44, 148,  2,  5, 15, 1, 1), # 1920x1080i @ 60 Hz
            (1920,  540, 1, 47500, 50500, 528,  44, 148,  2,  5, 15, 1, 1), # 1920x1080i @ 50 Hz
            #	(1920,  540, 1, 47500, 48500, 638,  44, 148,  2,  5, 15, 1, 1), # 1920x1080i @ 48 Hz (non-standard)
            (1440,  288, 1, 47500, 50500,  24, 126, 138,  2,  3, 19, 0, 0), # 1440x576i @ 50 Hz
            (1440,  240, 1, 59500, 60500,  38, 124, 114,  4,  3, 15, 0, 0), # 1440x480i @ 60 Hz
            (1366,  768, 0, 59500, 60500,  70, 143, 213,  3,  3, 24, 1, 1), # 1366x768 @ 60 Hz
            (1360,  768, 0, 59500, 60500,  64, 112, 256,  3,  6, 18, 1, 1), # 1360x768 @ 60 Hz
            (1280,  720, 0, 59500, 60500, 110,  40, 220,  5,  5, 20, 1, 1), # 1280x720 @ 60 Hz
            (1280,  720, 0, 47500, 50500, 440,  40, 220,  5,  5, 20, 1, 1), # 1280x720 @ 50 Hz
            #	(1280,  720, 0, 47500, 48500, 110,  40, 220,  5,  5, 20, 1, 1), # 1280x720 @ 48 Hz (non-standard)
            ( 720,  576, 0, 47500, 50500,  12,  64,  68,  5,  5, 39, 0, 0), # 720x576 @ 50 Hz
            ( 720,  480, 0, 59500, 60500,  16,  62,  60,  9,  6, 30, 0, 0), # 720x480 @ 60 Hz
            ( 640,  480, 0, 59500, 63500,  16,  96,  48, 10,  2, 33, 0, 0), # 640x480 @ 60 Hz
            )

    LCD_NATIVE = (
          (3840, 2160, 0, 60000, 176,  88, 296,  8, 10, 72, 1, 1), # 3840x2160 @ 60 Hz
          (1920, 1080, 0, 60000,  88,  44, 148,  4,  5, 36, 1, 1), # 1920x1080 @ 60 Hz
          (1920,  540, 1, 60000,  88,  44, 148,  2,  5, 15, 1, 1), # 1920x1080i @ 60 Hz
          (1440,  288, 1, 50000,  24, 126, 138,  2,  3, 19, 0, 0), # 1440x576i @ 50 Hz
          (1440,  240, 1, 59940,  38, 124, 114,  4,  3, 15, 0, 0), # 1440x480i @ 60 Hz
          (1366,  768, 0, 59789,  70, 143, 213,  3,  3, 24, 1, 1), # 1366x768 @ 60 Hz
          (1360,  768, 0, 60015,  64, 112, 256,  3,  6, 18, 1, 1), # 1360x768 @ 60 Hz
          (1280,  720, 0, 60000, 110,  40, 220,  5,  5, 20, 1, 1), # 1280x720 @ 60 Hz
          ( 720,  576, 0, 50000,  12,  64,  68,  5,  5, 39, 0, 0), # 720x576 @ 50 Hz
          ( 720,  480, 0, 59940,  16,  62,  60,  9,  6, 30, 0, 0), # 720x480 @ 60 Hz
          ( 640,  480, 0, 60000,  16,  96,  48, 10,  2, 33, 0, 0), # 640x480 @ 60 Hz


    )

    LCD_REDUCED = ()
    CRT_STANDARD = ()
    OLD_STANDARD = ()
class Constants2(object):
    """More constants, derivatives of primary constants (avoids using
       properties and metaclasses
    """
    C_PRIME = (Constants.C - Constants.J) * Constants.K / 256 + Constants.J
    M_PRIME = Constants.M * Constants.K / 256

from gpiozero import LED, TonalBuzzer, Button, LEDCharDisplay, LEDMultiCharDisplay
from time import sleep, time
from threading import Thread
from subprocess import check_call

green_duration = 30
yellow_duration = 1
pause_duration = 5

display = LEDCharDisplay(13, 6, 21, 7, 1, 5, 8)
displays = LEDMultiCharDisplay(display, 23, 24,18, 15)
displays.plex_delay=0.001

# Initialize LEDs for traffic lights
green_light_1 = LED(4)
yellow_light_1 = LED(0)
red_light_1 = LED(26)
pedestrian_red_1 = LED(9)
green_light_2 = LED(14)
yellow_light_2 = LED(12)
red_light_2 = LED(20)
pedestrian_red_2 = LED(25)

# Initialize buzzers
buzzer_1 = TonalBuzzer(19)
buzzer_2 = TonalBuzzer(16)

# Initialize buttons
button_1 = Button(10, hold_time=5)
button_2 = Button(27, hold_time=5)

# Global variables to keep track of end times
green_end_time_2 = None
green_end_time_1 = None
display_1_time = None
display_2_time = None

def adjust_green_light_time(light_number):
    global green_end_time_1, green_end_time_2
    current_time = time()
    if light_number == 1 and green_end_time_2 and current_time + 10 < green_end_time_2:
        green_end_time_2 = current_time + 10
        set_display_2_time(current_time + 10)
        set_display_1_time(current_time + 10 + 2 * yellow_duration + pause_duration)
    elif light_number == 2 and green_end_time_1 and current_time + 10 < green_end_time_1:
        green_end_time_1 = current_time + 10
        set_display_1_time(current_time + 10)
        set_display_2_time(current_time + 10 + 2 * yellow_duration + pause_duration)

def buzzer_beep(buzzer, get_end_time_func):
    while time() < get_end_time_func():
        buzzer.play(600.0)
        sleep(0.1)
        buzzer.stop()
        sleep(0.1)

def update_displays(get_semaphore_time_1_func, get_semaphore_time_2_func):
    while True:
        remaining_1 = int(max(0,get_semaphore_time_1_func() - time()))
        remaining_2 = int(max(0,get_semaphore_time_2_func() - time()))
        remaining = remaining_2*100+remaining_1
        formatted_remaining = f"{remaining:04d}"
        displays.value=str(formatted_remaining)
        sleep(1)

def get_end_time_1():
    return green_end_time_1

def get_end_time_2():
    return green_end_time_2

def get_display_1_time():
    return display_1_time

def get_display_2_time():
    return display_2_time

def traffic_light_sequence(light_set, pedestrian_light, buzzer, get_end_time_func, set_end_time_var, set_display_time):
    global green_end_time_1, green_end_time_2

    light_set[1].on()
    sleep(yellow_duration)

    # Set initial green end time
    set_end_time_var(time() + green_duration)
    set_display_time(time() + green_duration)

    light_set[2].off()
    light_set[1].off()
    light_set[0].on()
    pedestrian_light.off()
    buzzer_thread = Thread(target=buzzer_beep, args=(buzzer, get_end_time_func))
    buzzer_thread.start()
    while time() < get_end_time_func():
        remaining = get_end_time_func() - time()
        print(f"Green light countdown: {int(remaining)} seconds")
        sleep(1)

    light_set[0].off()
    light_set[1].on()
    pedestrian_light.on()
    set_display_time(time() + green_duration + 4 * yellow_duration + 2 * pause_duration)
    sleep(yellow_duration)
    light_set[1].off()
    light_set[2].on()

    # Ensure buzzer thread is stopped
    if buzzer_thread.is_alive():
        buzzer_thread.join()

    sleep(pause_duration)

# Set end time functions
def set_end_time_1(time):
    global green_end_time_1
    green_end_time_1 = time

def set_end_time_2(time):
    global green_end_time_2
    green_end_time_2 = time

def set_display_1_time(time):
    global display_1_time
    display_1_time = time

def set_display_2_time(time):
    global display_2_time
    display_2_time = time

def shutdown():
    check_call(['sudo', 'shutdown','-h','now'])


# Button press handlers
button_1.when_pressed = lambda: adjust_green_light_time(1)
button_2.when_pressed = lambda: adjust_green_light_time(2)
button_1.when_held = shutdown
button_2.when_held = shutdown


try:
    green_light_1.off()
    yellow_light_1.off()
    red_light_1.on()
    green_light_2.off()
    yellow_light_2.off()
    red_light_2.on()
    pedestrian_red_1.on()
    pedestrian_red_2.on()
    set_display_2_time(time() + green_duration + 2 * pause_duration + 3 * yellow_duration)
    set_display_1_time(time() + pause_duration + yellow_duration)
    display_thread = Thread(target=update_displays,args=(get_display_1_time,get_display_2_time,))
    display_thread.start()
    sleep(pause_duration)
    while True:
        traffic_light_sequence([green_light_1, yellow_light_1, red_light_1], pedestrian_red_1, buzzer_1, get_end_time_1, set_end_time_1, set_display_1_time)
        traffic_light_sequence([green_light_2, yellow_light_2, red_light_2], pedestrian_red_2, buzzer_2, get_end_time_2, set_end_time_2,set_display_2_time)
except KeyboardInterrupt:
    print("Program stopped")

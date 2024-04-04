from gpiozero import LED, TonalBuzzer, Button, LEDCharDisplay, LEDMultiCharDisplay
from time import sleep, time
from threading import Thread
from subprocess import check_call

# Initialize duration of lights and pause between lights change
green_duration = 30
yellow_duration = 1
pause_duration = 5

# 7 segment displays initialization
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

# Function that will be called when button is pressed
def adjust_green_light_time(light_number):
    current_time = time()
    # If button on semaphore 1 is pressed, and there is more than 10 seconds left on green light
    # 1. Set remaining time of green light to 10
    # 2. Set display time to 10
    # 3. Set time on other display so it counts until switch
    if light_number == 1 and get_end_time_2() and current_time + 10 < get_end_time_2():
        set_end_time_2(current_time + 10)
        set_display_2_time(current_time + 10)
        set_display_1_time(current_time + 10 + 2 * yellow_duration + pause_duration)
    # Same as 1 but reversed
    elif light_number == 2 and get_end_time_1() and current_time + 10 < get_end_time_1():
        set_end_time_1(current_time + 10)
        set_display_1_time(current_time + 10)
        set_display_2_time(current_time + 10 + 2 * yellow_duration + pause_duration)

# Function for buzzer beep, it will beep the buzzer each 0.1 seconds in while loop
def buzzer_beep(buzzer, get_end_time_func):
    while time() < get_end_time_func():
        buzzer.play(600.0)
        sleep(0.1)
        buzzer.stop()
        sleep(0.1)

# Function for setting display values, it uses 4 digits(first two representing semaphore 1 and last 2 for semaphore 2)
# It uses mutliplexing for displaying correct values
def update_displays(get_semaphore_time_1_func, get_semaphore_time_2_func):
    while True:
        remaining_1 = int(max(0,get_semaphore_time_1_func() - time()))
        remaining_2 = int(max(0,get_semaphore_time_2_func() - time()))
        # Set remaining value for correct formatting
        remaining = remaining_2*100+remaining_1
        #Turn to string but always contain 4 digits
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

# Function for controlling traffic lights
def traffic_light_sequence(light_set, pedestrian_light, buzzer, get_end_time_func, set_end_time_var, set_display_time):

    # Turn on yellow
    light_set[1].on()
    sleep(yellow_duration)

    # Set initial green end time
    set_end_time_var(time() + green_duration)
    set_display_time(time() + green_duration)

    # Turn off yellow and red and turn on green
    light_set[2].off()
    light_set[1].off()
    light_set[0].on()
    # Turn off pedestrian red light connected to this semaphore
    pedestrian_light.off()
    # Start the buzzer thread function while green is on
    buzzer_thread = Thread(target=buzzer_beep, args=(buzzer, get_end_time_func))
    buzzer_thread.start()
    # While loop until green light time passes(takes in count if someone pressed the button to shorten it)
    # Logging green countdown for debugging purposes
    while time() < get_end_time_func():
        remaining = get_end_time_func() - time()
        print(f"Green light countdown: {int(remaining)} seconds")
        sleep(1)

    # After while loop turn off green light and turn on yellow, also turn red light for pedestrians connected to this semaphore
    light_set[0].off()
    light_set[1].on()
    pedestrian_light.on()
    # Set display time for this semaphore until next green light
    set_display_time(time() + green_duration + 4 * yellow_duration + 2 * pause_duration)
    sleep(yellow_duration)
    # Turn off yellow and turn on red
    light_set[1].off()
    light_set[2].on()

    # Ensure buzzer thread is stopped and nothing is buzzing
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

# Function for shutting down the pi
def shutdown():
    check_call(['sudo', 'shutdown','-h','now'])


# Button press handlers
button_1.when_pressed = lambda: adjust_green_light_time(1)
button_2.when_pressed = lambda: adjust_green_light_time(2)
# If button is held for 5 seconds pi will be shut down
button_1.when_held = shutdown
button_2.when_held = shutdown


try:
    #Init all to red
    green_light_1.off()
    yellow_light_1.off()
    red_light_1.on()
    green_light_2.off()
    yellow_light_2.off()
    red_light_2.on()
    pedestrian_red_1.on()
    pedestrian_red_2.on()
    # Sety initial display times
    set_display_2_time(time() + green_duration + 2 * pause_duration + 3 * yellow_duration)
    set_display_1_time(time() + pause_duration + yellow_duration)
    # Start thread for updating displays
    display_thread = Thread(target=update_displays,args=(get_display_1_time,get_display_2_time,))
    display_thread.start()
    sleep(pause_duration)
    # Change one green light sequences in while loop so every direction has a green light
    while True:
        traffic_light_sequence([green_light_1, yellow_light_1, red_light_1], pedestrian_red_1, buzzer_1, get_end_time_1, set_end_time_1, set_display_1_time)
        traffic_light_sequence([green_light_2, yellow_light_2, red_light_2], pedestrian_red_2, buzzer_2, get_end_time_2, set_end_time_2,set_display_2_time)
except KeyboardInterrupt:
    print("Program stopped")

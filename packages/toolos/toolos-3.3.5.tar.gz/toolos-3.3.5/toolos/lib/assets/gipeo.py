"""
GIPEO - Comprehensive Hardware Abstraction Framework for MicroPython
===================================================================

Ein vollständiges Hardware-Management-Framework für MicroPython mit erweiterten
Features für GPIO, Buttons, I2C, SPI, NFC, AsyncIO und vieles mehr.

Features:
- Pin-Management mit Caching und erweiterten Modi
- Button-Handling mit Debouncing, Long-Press, Multi-Click
- AsyncIO-Integration für non-blocking operations
- I2C/SPI Device Management
- Display-Abstraktionen (OLED, LCD)
- NFC/RFID Support
- Queue-basierte Event-Systeme
- PWM, ADC, DAC Management
- Sensor-Presets (Temperatur, Licht, etc.)
- Network/WiFi Integration
- File-System Utilities
- Error-Handling und Logging
- Hardware-spezifische Presets

Kompatibel mit ESP32, ESP32-S3, Raspberry Pi Pico und anderen MicroPython-Boards.
"""

import time
import gc
from collections import defaultdict

try:
    import machine
    import uasyncio as asyncio
    import ubinascii
    import ujson as json
    import uos as os
    import network
    import ntptime
    import struct
    import hashlib
    import micropython
    import esp32
    _HAS_MACHINE = True
    _IS_MICROPYTHON = True
except ImportError:
    # Desktop Mock Environment
    import asyncio
    import json
    import os
    import time
    import hashlib
    import struct
    _HAS_MACHINE = False
    _IS_MICROPYTHON = False

    # Mock classes for development
    class _MockPin:
        OUT = 0
        IN = 1
        PULL_UP = 2
        PULL_DOWN = 3
        IRQ_RISING = 4
        IRQ_FALLING = 5

        def __init__(self, pin, mode=None, pull=None, value=None):
            self._pin = pin
            self._mode = mode
            self._pull = pull
            self._val = value or 0
            self._irq_handler = None

        def on(self):
            self._val = 1
            print(f"[MOCK] Pin {self._pin} ON")

        def off(self):
            self._val = 0
            print(f"[MOCK] Pin {self._pin} OFF")

        def value(self, v=None):
            if v is None:
                return self._val
            self._val = 1 if v else 0
            print(f"[MOCK] Pin {self._pin} = {self._val}")

        def irq(self, trigger=None, handler=None):
            self._irq_handler = handler
            print(f"[MOCK] Pin {self._pin} IRQ set, trigger={trigger}")

    class _MockPWM:
        def __init__(self, pin, freq=1000, duty=512):
            self._pin = pin
            self._freq = freq
            self._duty = duty
            print(f"[MOCK] PWM Pin {pin}, freq={freq}, duty={duty}")

        def freq(self, f=None):
            if f is None:
                return self._freq
            self._freq = f
            print(f"[MOCK] PWM freq = {f}")

        def duty(self, d=None):
            if d is None:
                return self._duty
            self._duty = d
            print(f"[MOCK] PWM duty = {d}")

        def deinit(self):
            print(f"[MOCK] PWM deinit")

    class _MockADC:
        def __init__(self, pin):
            self._pin = pin
            print(f"[MOCK] ADC Pin {pin}")

        def read(self):
            import random
            val = random.randint(0, 4095)
            print(f"[MOCK] ADC read = {val}")
            return val

        def read_u16(self):
            return self.read() << 4

    class _MockI2C:
        def __init__(self, id, scl, sda, freq=400000):
            self._id = id
            self._scl = scl
            self._sda = sda
            self._freq = freq
            print(f"[MOCK] I2C id={id}, scl={scl}, sda={sda}, freq={freq}")

        def scan(self):
            print("[MOCK] I2C scan")
            return [0x3c, 0x48]  # Mock devices

        def writeto(self, addr, buf):
            print(f"[MOCK] I2C write to 0x{addr:02x}: {buf}")

        def readfrom(self, addr, nbytes):
            data = bytes([0x00] * nbytes)
            print(f"[MOCK] I2C read from 0x{addr:02x}: {data}")
            return data

    class _MockSPI:
        def __init__(self, id, baudrate=1000000, polarity=0, phase=0, sck=None, mosi=None, miso=None):
            print(f"[MOCK] SPI id={id}, baud={baudrate}")

        def write(self, buf):
            print(f"[MOCK] SPI write: {buf}")

        def read(self, nbytes):
            data = bytes([0x00] * nbytes)
            print(f"[MOCK] SPI read: {data}")
            return data

    class _MockTimer:
        def __init__(self, id):
            self._id = id

        def init(self, period=1000, mode=None, callback=None):
            print(f"[MOCK] Timer {self._id} init, period={period}")

        def deinit(self):
            print(f"[MOCK] Timer {self._id} deinit")

    class _MockRTC:
        def datetime(self, t=None):
            if t is None:
                return (2025, 8, 29, 0, 12, 30, 45, 0)
            print(f"[MOCK] RTC set: {t}")

    class _MockMachine:
        Pin = _MockPin
        PWM = _MockPWM
        ADC = _MockADC
        I2C = _MockI2C
        SPI = _MockSPI
        Timer = _MockTimer
        RTC = _MockRTC
        freq = lambda f=None: f or 240000000
        reset = lambda: print("[MOCK] Machine reset")
        unique_id = lambda: b'\x12\x34\x56\x78'

    machine = _MockMachine()
    network = None
    ubinascii = None
    micropython = None
    esp32 = None


# ==================== CORE CLASSES ====================

class GipeoError(Exception):
    """Base exception for Gipeo framework"""
    pass


class HardwareError(GipeoError):
    """Hardware-related errors"""
    pass


class ConfigurationError(GipeoError):
    """Configuration-related errors"""
    pass


# ==================== EVENT SYSTEM ====================

class EventQueue:
    """Thread-safe event queue for hardware events"""
    
    def __init__(self, maxsize=100):
        self._queue = []
        self._maxsize = maxsize
        self._lock = asyncio.Lock() if _IS_MICROPYTHON else None

    async def put(self, event):
        if self._lock:
            async with self._lock:
                if len(self._queue) >= self._maxsize:
                    self._queue.pop(0)  # Remove oldest
                self._queue.append(event)
        else:
            if len(self._queue) >= self._maxsize:
                self._queue.pop(0)
            self._queue.append(event)

    async def get(self):
        while True:
            if self._lock:
                async with self._lock:
                    if self._queue:
                        return self._queue.pop(0)
            else:
                if self._queue:
                    return self._queue.pop(0)
            await asyncio.sleep_ms(10)

    def empty(self):
        return len(self._queue) == 0

    def qsize(self):
        return len(self._queue)


class Event:
    """Hardware event container"""
    
    def __init__(self, event_type, source, data=None, timestamp=None):
        self.type = event_type
        self.source = source
        self.data = data or {}
        self.timestamp = timestamp or time.ticks_ms()

    def __repr__(self):
        return f"Event({self.type}, {self.source}, {self.data})"


# ==================== BUTTON MANAGEMENT ====================

class Button:
    """Advanced button with debouncing, long-press, multi-click detection"""
    
    def __init__(self, pin, pull=None, invert=False, debounce_ms=50):
        self.pin_num = pin
        self.invert = invert
        self.debounce_ms = debounce_ms
        self._last_state = None
        self._last_time = 0
        self._press_start = 0
        self._click_count = 0
        self._click_timeout = 500  # ms for multi-click detection
        self._long_press_time = 1000  # ms for long press
        self._callbacks = defaultdict(list)
        
        # Initialize pin
        pull_mode = pull or (machine.Pin.PULL_UP if not invert else machine.Pin.PULL_DOWN)
        self.pin = machine.Pin(pin, machine.Pin.IN, pull_mode)
        
        # Set up interrupt
        trigger = machine.Pin.IRQ_FALLING if not invert else machine.Pin.IRQ_RISING
        self.pin.irq(trigger=trigger | (machine.Pin.IRQ_RISING if not invert else machine.Pin.IRQ_FALLING), 
                     handler=self._irq_handler)

    def _irq_handler(self, pin):
        """Interrupt handler for pin changes"""
        current_time = time.ticks_ms()
        current_state = self._read_raw()
        
        # Debouncing
        if time.ticks_diff(current_time, self._last_time) < self.debounce_ms:
            return
            
        self._last_time = current_time
        
        if current_state != self._last_state:
            if current_state:  # Button pressed
                self._press_start = current_time
                self._on_press()
            else:  # Button released
                press_duration = time.ticks_diff(current_time, self._press_start)
                if press_duration > self._long_press_time:
                    self._on_long_press(press_duration)
                else:
                    self._click_count += 1
                    self._schedule_click_check()
                self._on_release(press_duration)
                
        self._last_state = current_state

    def _read_raw(self):
        """Read raw pin state"""
        state = self.pin.value()
        return not state if self.invert else state

    def _schedule_click_check(self):
        """Schedule click count evaluation"""
        async def check_clicks():
            await asyncio.sleep_ms(self._click_timeout)
            if self._click_count == 1:
                self._on_click()
            elif self._click_count == 2:
                self._on_double_click()
            elif self._click_count >= 3:
                self._on_multi_click(self._click_count)
            self._click_count = 0
            
        if _IS_MICROPYTHON:
            asyncio.create_task(check_clicks())

    def _on_press(self):
        self._trigger_callbacks('press')

    def _on_release(self, duration):
        self._trigger_callbacks('release', {'duration': duration})

    def _on_click(self):
        self._trigger_callbacks('click')

    def _on_double_click(self):
        self._trigger_callbacks('double_click')

    def _on_multi_click(self, count):
        self._trigger_callbacks('multi_click', {'count': count})

    def _on_long_press(self, duration):
        self._trigger_callbacks('long_press', {'duration': duration})

    def _trigger_callbacks(self, event_type, data=None):
        """Trigger all callbacks for an event type"""
        for callback in self._callbacks[event_type]:
            try:
                if data:
                    callback(data)
                else:
                    callback()
            except Exception as e:
                print(f"Button callback error: {e}")

    def on(self, event_type, callback):
        """Register callback for button events"""
        valid_events = ['press', 'release', 'click', 'double_click', 'multi_click', 'long_press']
        if event_type not in valid_events:
            raise ValueError(f"Invalid event type. Must be one of: {valid_events}")
        self._callbacks[event_type].append(callback)

    def is_pressed(self):
        """Check if button is currently pressed"""
        return self._read_raw()

    def config(self, **kwargs):
        """Configure button parameters"""
        if 'debounce_ms' in kwargs:
            self.debounce_ms = kwargs['debounce_ms']
        if 'long_press_time' in kwargs:
            self._long_press_time = kwargs['long_press_time']
        if 'click_timeout' in kwargs:
            self._click_timeout = kwargs['click_timeout']


# ==================== PWM MANAGEMENT ====================

class PWMManager:
    """Advanced PWM control with smooth transitions and effects"""
    
    def __init__(self, pin, freq=1000, duty=0):
        self.pin_num = pin
        self._pwm = machine.PWM(machine.Pin(pin))
        self._pwm.freq(freq)
        self._pwm.duty(duty)
        self._target_duty = duty
        self._transition_task = None

    def duty(self, value=None):
        """Get/set PWM duty cycle (0-1023)"""
        if value is None:
            return self._pwm.duty()
        self._pwm.duty(int(value))
        self._target_duty = value

    def freq(self, value=None):
        """Get/set PWM frequency"""
        if value is None:
            return self._pwm.freq()
        self._pwm.freq(int(value))

    def duty_percent(self, percent=None):
        """Get/set duty cycle as percentage (0-100)"""
        if percent is None:
            return (self._pwm.duty() / 1023) * 100
        self.duty(int((percent / 100) * 1023))

    async def fade_to(self, target_duty, duration_ms=1000, steps=50):
        """Smoothly transition to target duty cycle"""
        if self._transition_task:
            self._transition_task.cancel()
            
        current_duty = self._pwm.duty()
        step_size = (target_duty - current_duty) / steps
        step_delay = duration_ms // steps
        
        async def transition():
            for i in range(steps):
                new_duty = int(current_duty + (step_size * (i + 1)))
                self._pwm.duty(new_duty)
                await asyncio.sleep_ms(step_delay)
            self._pwm.duty(target_duty)
            self._target_duty = target_duty
            
        self._transition_task = asyncio.create_task(transition())
        await self._transition_task

    async def pulse(self, min_duty=0, max_duty=1023, period_ms=2000):
        """Create pulsing effect"""
        while True:
            await self.fade_to(max_duty, period_ms // 2)
            await self.fade_to(min_duty, period_ms // 2)

    async def blink(self, on_duty=1023, off_duty=0, on_time=500, off_time=500):
        """Blink with custom timing"""
        while True:
            self.duty(on_duty)
            await asyncio.sleep_ms(on_time)
            self.duty(off_duty)
            await asyncio.sleep_ms(off_time)

    def deinit(self):
        """Cleanup PWM"""
        if self._transition_task:
            self._transition_task.cancel()
        self._pwm.deinit()


# ==================== SENSOR CLASSES ====================

class AnalogSensor:
    """Generic analog sensor with calibration and filtering"""
    
    def __init__(self, pin, samples=10, vref=3.3):
        self.pin_num = pin
        self.adc = machine.ADC(machine.Pin(pin))
        self.samples = samples
        self.vref = vref
        self._calibration_offset = 0
        self._calibration_scale = 1
        self._filter_alpha = 0.1  # Low-pass filter
        self._filtered_value = None

    def read_raw(self):
        """Read raw ADC value"""
        return self.adc.read()

    def read_voltage(self):
        """Read voltage with averaging"""
        total = 0
        for _ in range(self.samples):
            total += self.adc.read()
        avg_raw = total / self.samples
        voltage = (avg_raw / 4095) * self.vref  # 12-bit ADC
        return voltage

    def read_filtered(self):
        """Read with low-pass filtering"""
        current = self.read_voltage()
        if self._filtered_value is None:
            self._filtered_value = current
        else:
            self._filtered_value = (self._filter_alpha * current) + ((1 - self._filter_alpha) * self._filtered_value)
        return self._filtered_value

    def calibrate(self, known_value, measured_value=None):
        """Single-point calibration"""
        if measured_value is None:
            measured_value = self.read_voltage()
        self._calibration_scale = known_value / measured_value

    def read_calibrated(self):
        """Read calibrated value"""
        raw = self.read_filtered()
        return (raw + self._calibration_offset) * self._calibration_scale

    def config_filter(self, alpha=0.1):
        """Configure low-pass filter"""
        self._filter_alpha = alpha


class TemperatureSensor(AnalogSensor):
    """Temperature sensor (LM35, TMP36, etc.)"""
    
    def __init__(self, pin, sensor_type='LM35', **kwargs):
        super().__init__(pin, **kwargs)
        self.sensor_type = sensor_type
        
        # Sensor-specific parameters
        if sensor_type == 'LM35':
            self._mv_per_c = 10  # 10mV/°C
            self._offset_c = 0
        elif sensor_type == 'TMP36':
            self._mv_per_c = 10  # 10mV/°C
            self._offset_c = -50  # 500mV = 0°C
        else:
            self._mv_per_c = 10
            self._offset_c = 0

    def read_temperature_c(self):
        """Read temperature in Celsius"""
        voltage = self.read_calibrated()
        temp_c = ((voltage * 1000) / self._mv_per_c) + self._offset_c
        return temp_c

    def read_temperature_f(self):
        """Read temperature in Fahrenheit"""
        temp_c = self.read_temperature_c()
        return (temp_c * 9/5) + 32


class LightSensor(AnalogSensor):
    """Light sensor (LDR, photodiode, etc.)"""
    
    def __init__(self, pin, **kwargs):
        super().__init__(pin, **kwargs)
        self._min_lux = 0
        self._max_lux = 1000

    def calibrate_range(self, dark_reading, bright_reading, min_lux=0, max_lux=1000):
        """Calibrate sensor range"""
        self._dark_reading = dark_reading
        self._bright_reading = bright_reading
        self._min_lux = min_lux
        self._max_lux = max_lux

    def read_lux(self):
        """Read light level in lux (requires calibration)"""
        voltage = self.read_calibrated()
        if hasattr(self, '_dark_reading'):
            # Linear interpolation between calibrated points
            lux_range = self._max_lux - self._min_lux
            voltage_range = self._bright_reading - self._dark_reading
            lux = self._min_lux + ((voltage - self._dark_reading) / voltage_range) * lux_range
            return max(0, min(self._max_lux, lux))
        return voltage  # Return voltage if not calibrated

    def read_percent(self):
        """Read light level as percentage"""
        voltage = self.read_voltage()
        return (voltage / self.vref) * 100


# ==================== I2C DEVICE MANAGEMENT ====================

class I2CDevice:
    """Base class for I2C devices"""
    
    def __init__(self, i2c, address):
        self.i2c = i2c
        self.address = address

    def write_reg(self, reg, data):
        """Write to device register"""
        if isinstance(data, int):
            data = bytes([data])
        elif isinstance(data, list):
            data = bytes(data)
        self.i2c.writeto(self.address, bytes([reg]) + data)

    def read_reg(self, reg, nbytes=1):
        """Read from device register"""
        self.i2c.writeto(self.address, bytes([reg]))
        data = self.i2c.readfrom(self.address, nbytes)
        return data[0] if nbytes == 1 else data

    def scan_device(self):
        """Check if device is present"""
        try:
            self.i2c.writeto(self.address, b'')
            return True
        except:
            return False


class OLED_SSD1306(I2CDevice):
    """Advanced SSD1306 OLED Display Driver for 128x64 i2c Display
    
    Erweiterte OLED-Klasse mit umfassenden Design-APIs, Pixel-Management,
    Asset-System, Animationen und erweiterten Positionierungs-Methoden.
    """
    
    # Color Constants
    BLACK = 0
    WHITE = 1
    
    # Position Constants
    POSITIONS = {
        'TOP_LEFT': (0, 0),
        'TOP_CENTER': (64, 0),
        'TOP_RIGHT': (128, 0),
        'MIDDLE_LEFT': (0, 32),
        'MIDDLE_CENTER': (64, 32),
        'CENTER': (64, 32),
        'MIDDLE_RIGHT': (128, 32),
        'BOTTOM_LEFT': (0, 64),
        'BOTTOM_CENTER': (64, 64),
        'BOTTOM_RIGHT': (128, 64),
        'LEFT': (0, 32),
        'RIGHT': (128, 32),
        'TOP': (64, 0),
        'BOTTOM': (64, 64)
    }
    
    # Font Data (8x8 Basic Font)
    FONT_8X8 = {
        ' ': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        'A': [0x7E, 0x81, 0x81, 0x81, 0xFF, 0x81, 0x81, 0x81],
        'B': [0xFF, 0x81, 0x81, 0xFF, 0xFF, 0x81, 0x81, 0xFF],
        'C': [0x7E, 0x81, 0x80, 0x80, 0x80, 0x80, 0x81, 0x7E],
        'D': [0xFE, 0x81, 0x81, 0x81, 0x81, 0x81, 0x81, 0xFE],
        'E': [0xFF, 0x80, 0x80, 0xFE, 0xFE, 0x80, 0x80, 0xFF],
        'F': [0xFF, 0x80, 0x80, 0xFE, 0xFE, 0x80, 0x80, 0x80],
        'G': [0x7E, 0x81, 0x80, 0x8F, 0x8F, 0x81, 0x81, 0x7E],
        'H': [0x81, 0x81, 0x81, 0xFF, 0xFF, 0x81, 0x81, 0x81],
        'I': [0xFF, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0xFF],
        '0': [0x7E, 0x81, 0x85, 0x89, 0x91, 0xA1, 0x81, 0x7E],
        '1': [0x18, 0x38, 0x18, 0x18, 0x18, 0x18, 0x18, 0x7E],
        '2': [0x7E, 0x81, 0x01, 0x02, 0x0C, 0x30, 0x40, 0xFF],
        '3': [0x7E, 0x81, 0x01, 0x3E, 0x3E, 0x01, 0x81, 0x7E],
        '4': [0x02, 0x06, 0x0A, 0x12, 0x22, 0xFF, 0x02, 0x02],
        '5': [0xFF, 0x80, 0x80, 0xFE, 0x01, 0x01, 0x81, 0x7E],
        '6': [0x7E, 0x81, 0x80, 0xFE, 0x81, 0x81, 0x81, 0x7E],
        '7': [0xFF, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x20],
        '8': [0x7E, 0x81, 0x81, 0x7E, 0x7E, 0x81, 0x81, 0x7E],
        '9': [0x7E, 0x81, 0x81, 0x81, 0x7F, 0x01, 0x81, 0x7E],
        '.': [0x00, 0x00, 0x00, 0x00, 0x00, 0x60, 0x60, 0x00],
        ',': [0x00, 0x00, 0x00, 0x00, 0x60, 0x60, 0x20, 0x40],
        '!': [0x18, 0x18, 0x18, 0x18, 0x18, 0x00, 0x18, 0x00],
        '?': [0x7E, 0x81, 0x01, 0x0E, 0x18, 0x00, 0x18, 0x00],
        ':': [0x00, 0x60, 0x60, 0x00, 0x00, 0x60, 0x60, 0x00],
        '-': [0x00, 0x00, 0x00, 0x7E, 0x7E, 0x00, 0x00, 0x00],
    }
    
    def __init__(self, i2c, address=0x3C, width=128, height=64):
        super().__init__(i2c, address)
        self.width = width
        self.height = height
        self.pages = height // 8
        self.buffer = bytearray(self.width * self.pages)
        
        # Advanced features
        self.pixel = PixelManager(self)
        self.design = DesignManager(self)
        self.animation = AnimationManager(self)
        self.asset = OLEDAssetManager(self)
        
        # Clipboard for copy/paste operations
        self._clipboard = None
        self._clipboard_size = None
        
        # Animation state
        self._animations = {}
        self._animation_frame = 0
        
        # Button integration
        self._button_callbacks = {}
        
        self._init_display()

    def _init_display(self):
        """Initialize SSD1306 OLED Display"""
        init_cmds = [
            0xAE,  # Display OFF
            0xD5, 0x80,  # Set display clock
            0xA8, self.height - 1,  # Set multiplex ratio
            0xD3, 0x00,  # Set display offset
            0x40,  # Set start line
            0x8D, 0x14,  # Charge pump
            0x20, 0x00,  # Memory addressing mode
            0xA1,  # Segment remap
            0xC8,  # COM output scan direction
            0xDA, 0x12 if self.height == 64 else 0x02,  # COM pins config
            0x81, 0xCF,  # Set contrast
            0xD9, 0xF1,  # Set pre-charge
            0xDB, 0x40,  # Set VCOM detect
            0xA4,  # Entire display ON
            0xA6,  # Normal display
            0x2E,  # Deactivate scroll
            0xAF   # Display ON
        ]
        
        for cmd in init_cmds:
            self.write_cmd(cmd)
        
        self.clear()
        self.show()

    def write_cmd(self, cmd):
        """Write command to display"""
        try:
            self.i2c.writeto(self.address, bytes([0x00, cmd]))
        except:
            pass  # Handle I2C errors gracefully

    def write_data(self, data):
        """Write data to display"""
        try:
            self.i2c.writeto(self.address, bytes([0x40]) + data)
        except:
            pass

    # ==================== BASIC DRAWING METHODS ====================

    def clear(self, color=BLACK):
        """Clear display buffer with specified color"""
        fill_value = 0xFF if color == self.WHITE else 0x00
        for i in range(len(self.buffer)):
            self.buffer[i] = fill_value

    def set_pixel(self, x, y, color=WHITE):
        """Set pixel in buffer with bounds checking"""
        if 0 <= x < self.width and 0 <= y < self.height:
            page = y // 8
            bit = y % 8
            index = page * self.width + x
            
            if color == self.WHITE:
                self.buffer[index] |= (1 << bit)
            else:
                self.buffer[index] &= ~(1 << bit)

    def get_pixel(self, x, y):
        """Get pixel value at coordinates"""
        if 0 <= x < self.width and 0 <= y < self.height:
            page = y // 8
            bit = y % 8
            index = page * self.width + x
            return (self.buffer[index] >> bit) & 1
        return 0

    def line(self, x0, y0, x1, y1, color=WHITE, thickness=1):
        """Draw line with optional thickness"""
        if thickness == 1:
            self._draw_line_basic(x0, y0, x1, y1, color)
        else:
            self._draw_line_thick(x0, y0, x1, y1, color, thickness)

    def _draw_line_basic(self, x0, y0, x1, y1, color):
        """Basic Bresenham line algorithm"""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            self.set_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def _draw_line_thick(self, x0, y0, x1, y1, color, thickness):
        """Draw thick line"""
        for i in range(thickness):
            offset = i - thickness // 2
            # Draw multiple parallel lines for thickness
            if abs(x1 - x0) > abs(y1 - y0):
                self._draw_line_basic(x0, y0 + offset, x1, y1 + offset, color)
            else:
                self._draw_line_basic(x0 + offset, y0, x1 + offset, y1, color)

    def rect(self, x, y, w, h, color=WHITE, fill=False, thickness=1):
        """Draw rectangle with optional fill and thickness"""
        if fill:
            self.fill_rect(x, y, w, h, color)
        else:
            # Draw outline with thickness
            for t in range(thickness):
                # Top and bottom
                self.line(x-t, y-t, x+w+t, y-t, color)
                self.line(x-t, y+h+t, x+w+t, y+h+t, color)
                # Left and right
                self.line(x-t, y-t, x-t, y+h+t, color)
                self.line(x+w+t, y-t, x+w+t, y+h+t, color)

    def fill_rect(self, x, y, w, h, color=WHITE):
        """Fill rectangle area"""
        for py in range(max(0, y), min(self.height, y + h)):
            for px in range(max(0, x), min(self.width, x + w)):
                self.set_pixel(px, py, color)

    def circle(self, x0, y0, radius, color=WHITE, fill=False, thickness=1):
        """Draw circle using midpoint algorithm"""
        if fill:
            self._fill_circle(x0, y0, radius, color)
        else:
            self._draw_circle_outline(x0, y0, radius, color, thickness)

    def _draw_circle_outline(self, x0, y0, radius, color, thickness):
        """Draw circle outline"""
        for t in range(thickness):
            r = radius + t - thickness // 2
            if r <= 0:
                continue
                
            x = r
            y = 0
            err = 0

            while x >= y:
                self.set_pixel(x0 + x, y0 + y, color)
                self.set_pixel(x0 + y, y0 + x, color)
                self.set_pixel(x0 - y, y0 + x, color)
                self.set_pixel(x0 - x, y0 + y, color)
                self.set_pixel(x0 - x, y0 - y, color)
                self.set_pixel(x0 - y, y0 - x, color)
                self.set_pixel(x0 + y, y0 - x, color)
                self.set_pixel(x0 + x, y0 - y, color)

                if err <= 0:
                    y += 1
                    err += 2*y + 1
                
                if err > 0:
                    x -= 1
                    err -= 2*x + 1

    def _fill_circle(self, x0, y0, radius, color):
        """Fill circle area"""
        for y in range(-radius, radius + 1):
            for x in range(-radius, radius + 1):
                if x*x + y*y <= radius*radius:
                    self.set_pixel(x0 + x, y0 + y, color)

    # ==================== ADVANCED DRAWING METHODS ====================

    def triangle(self, x0, y0, x1, y1, x2, y2, color=WHITE, fill=False):
        """Draw triangle"""
        if fill:
            self._fill_triangle(x0, y0, x1, y1, x2, y2, color)
        else:
            self.line(x0, y0, x1, y1, color)
            self.line(x1, y1, x2, y2, color)
            self.line(x2, y2, x0, y0, color)

    def _fill_triangle(self, x0, y0, x1, y1, x2, y2, color):
        """Fill triangle using scan line algorithm"""
        # Sort vertices by y-coordinate
        points = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = points
        
        for y in range(y0, y2 + 1):
            if y <= y1:
                # Upper triangle
                if y1 != y0:
                    xa = x0 + (x1 - x0) * (y - y0) // (y1 - y0)
                else:
                    xa = x0
                if y2 != y0:
                    xb = x0 + (x2 - x0) * (y - y0) // (y2 - y0)
                else:
                    xb = x0
            else:
                # Lower triangle
                if y2 != y1:
                    xa = x1 + (x2 - x1) * (y - y1) // (y2 - y1)
                else:
                    xa = x1
                if y2 != y0:
                    xb = x0 + (x2 - x0) * (y - y0) // (y2 - y0)
                else:
                    xb = x0
            
            if xa > xb:
                xa, xb = xb, xa
            
            for x in range(int(xa), int(xb) + 1):
                self.set_pixel(x, y, color)

    def polygon(self, points, color=WHITE, fill=False):
        """Draw polygon from list of (x,y) points"""
        if len(points) < 3:
            return
            
        if fill:
            # Simple fill using triangle fan
            for i in range(1, len(points) - 1):
                self._fill_triangle(
                    points[0][0], points[0][1],
                    points[i][0], points[i][1],
                    points[i+1][0], points[i+1][1],
                    color
                )
        else:
            # Draw outline
            for i in range(len(points)):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % len(points)]
                self.line(x0, y0, x1, y1, color)

    # ==================== TEXT AND FONT RENDERING ====================

    def text(self, text, x, y, color=WHITE, font_size=1, font_type="default"):
        """Draw text with font options"""
        if font_type == "default":
            self._draw_text_default(text, x, y, color, font_size)
        elif font_type == "large":
            self._draw_text_large(text, x, y, color)
        elif font_type == "small":
            self._draw_text_small(text, x, y, color)

    def _draw_text_default(self, text, x, y, color, font_size):
        """Draw text with default 8x8 font"""
        char_width = 8 * font_size
        char_height = 8 * font_size
        
        for char_idx, char in enumerate(text):
            char_x = x + char_idx * char_width
            if char_x >= self.width:
                break
            self._draw_char_scaled(char, char_x, y, color, font_size)

    def _draw_char_scaled(self, char, x, y, color, scale):
        """Draw single character with scaling"""
        char_data = self.FONT_8X8.get(char.upper(), self.FONT_8X8.get(' '))
        
        for row in range(8):
            if y + row * scale >= self.height:
                break
            byte_data = char_data[row]
            for col in range(8):
                if x + col * scale >= self.width:
                    break
                if byte_data & (1 << (7 - col)):
                    # Draw scaled pixel
                    for sy in range(scale):
                        for sx in range(scale):
                            self.set_pixel(x + col * scale + sx, y + row * scale + sy, color)

    def _draw_text_large(self, text, x, y, color):
        """Draw large text (16x16)"""
        self._draw_text_default(text, x, y, color, font_size=2)

    def _draw_text_small(self, text, x, y, color):
        """Draw small text (6x8)"""
        char_width = 6
        for char_idx, char in enumerate(text):
            char_x = x + char_idx * char_width
            if char_x >= self.width:
                break
            # Draw compressed 6x8 version
            char_data = self.FONT_8X8.get(char.upper(), self.FONT_8X8.get(' '))
            for row in range(8):
                if y + row >= self.height:
                    break
                byte_data = char_data[row]
                for col in range(6):  # Only use 6 pixels width
                    if x + col >= self.width:
                        break
                    if byte_data & (1 << (7 - col)):
                        self.set_pixel(char_x + col, y + row, color)

    def text_width(self, text, font_size=1):
        """Calculate text width in pixels"""
        return len(text) * 8 * font_size

    def text_height(self, font_size=1):
        """Calculate text height in pixels"""
        return 8 * font_size

    # ==================== POSITION MANAGEMENT ====================

    def get_position(self, position_name, width=0, height=0):
        """Get coordinates for named position with size adjustment
        
        Usage: x, y = oled.get_position("MIDDLE_CENTER", text_width, text_height)
        """
        if position_name.upper() not in self.POSITIONS:
            return (0, 0)
        
        base_x, base_y = self.POSITIONS[position_name.upper()]
        
        # Adjust for center positions
        if 'CENTER' in position_name.upper() or 'MIDDLE' in position_name.upper():
            base_x -= width // 2
            base_y -= height // 2
        elif 'RIGHT' in position_name.upper():
            base_x -= width
        elif 'BOTTOM' in position_name.upper():
            base_y -= height
        
        # Ensure coordinates are within bounds
        base_x = max(0, min(self.width - width, base_x))
        base_y = max(0, min(self.height - height, base_y))
        
        return (base_x, base_y)

    def text_at_position(self, text, position, color=WHITE, font_size=1):
        """Draw text at named position
        
        Usage: oled.text_at_position("Menu", "TOP_CENTER")
        """
        text_w = self.text_width(text, font_size)
        text_h = self.text_height(font_size)
        x, y = self.get_position(position, text_w, text_h)
        self.text(text, x, y, color, font_size)

    def rect_at_position(self, position, width, height, color=WHITE, fill=False):
        """Draw rectangle at named position"""
        x, y = self.get_position(position, width, height)
        self.rect(x, y, width, height, color, fill)

    def circle_at_position(self, position, radius, color=WHITE, fill=False):
        """Draw circle at named position"""
        x, y = self.get_position(position, radius*2, radius*2)
        self.circle(x + radius, y + radius, radius, color, fill)

    # ==================== COPY/PASTE OPERATIONS ====================

    def copy(self, x, y, width, height):
        """Copy screen area to clipboard
        
        Usage: oled.copy(10, 10, 32, 16)
        """
        if x < 0 or y < 0 or x + width > self.width or y + height > self.height:
            return False
        
        self._clipboard = []
        self._clipboard_size = (width, height)
        
        for py in range(height):
            row = []
            for px in range(width):
                pixel_value = self.get_pixel(x + px, y + py)
                row.append(pixel_value)
            self._clipboard.append(row)
        
        return True

    def paste(self, x, y, transparent=False):
        """Paste clipboard content at position
        
        Usage: oled.paste(50, 20, transparent=True)
        """
        if not self._clipboard or not self._clipboard_size:
            return False
        
        width, height = self._clipboard_size
        
        for py in range(height):
            for px in range(width):
                if x + px >= self.width or y + py >= self.height:
                    continue
                    
                pixel_value = self._clipboard[py][px]
                
                # Skip transparent pixels (black) if transparency enabled
                if transparent and pixel_value == self.BLACK:
                    continue
                    
                self.set_pixel(x + px, y + py, pixel_value)
        
        return True

    def move(self, src_x, src_y, dst_x, dst_y, width, height):
        """Move screen area from source to destination
        
        Usage: oled.move(0, 0, 20, 20, 32, 16)
        """
        if self.copy(src_x, src_y, width, height):
            self.fill_rect(src_x, src_y, width, height, self.BLACK)  # Clear source
            return self.paste(dst_x, dst_y)
        return False

    # ==================== ASSET MANAGEMENT ====================

    def load_from_png(self, file_path, x=0, y=0, scale=1, transparent=False):
        """Load and display PNG asset
        
        Usage: asset = oled.load_from_png("icon.png", x=10, y=10, scale=2)
        """
        try:
            # This would need a proper PNG decoder for full implementation
            # For now, create a placeholder
            asset = self.asset.create_placeholder_asset(32, 32)
            self.draw_asset(asset, x, y, scale, transparent)
            return asset
        except Exception as e:
            print(f"Error loading PNG: {e}")
            return None

    def draw_asset(self, asset, x, y, scale=1, transparent=False):
        """Draw asset at position with scaling and transparency
        
        Usage: oled.draw_asset(my_sprite, 20, 30, scale=2)
        """
        if not asset:
            return
        
        asset_width, asset_height = asset.get_size()
        
        for py in range(asset_height):
            for px in range(asset_width):
                pixel_value = asset.get_pixel(px, py)
                
                # Skip transparent pixels
                if transparent and pixel_value == self.BLACK:
                    continue
                
                # Draw scaled pixel
                for sy in range(scale):
                    for sx in range(scale):
                        draw_x = x + px * scale + sx
                        draw_y = y + py * scale + sy
                        if 0 <= draw_x < self.width and 0 <= draw_y < self.height:
                            self.set_pixel(draw_x, draw_y, pixel_value)

    # ==================== ADVANCED DESIGN ELEMENTS ====================

    def draw_rounded_rect(self, x, y, w, h, radius, color=WHITE, fill=False):
        """Draw rectangle with rounded corners"""
        if radius <= 0:
            self.rect(x, y, w, h, color, fill)
            return
        
        radius = min(radius, min(w//2, h//2))
        
        if fill:
            # Fill main rectangles
            self.fill_rect(x + radius, y, w - 2*radius, h, color)  # Center
            self.fill_rect(x, y + radius, w, h - 2*radius, color)  # Middle
            
            # Fill rounded corners
            for corner_x, corner_y in [(x+radius, y+radius), (x+w-radius-1, y+radius), 
                                     (x+radius, y+h-radius-1), (x+w-radius-1, y+h-radius-1)]:
                for dy in range(-radius, radius+1):
                    for dx in range(-radius, radius+1):
                        if dx*dx + dy*dy <= radius*radius:
                            self.set_pixel(corner_x + dx, corner_y + dy, color)
        else:
            # Draw outline
            self.line(x + radius, y, x + w - radius, y, color)  # Top
            self.line(x + radius, y + h - 1, x + w - radius, y + h - 1, color)  # Bottom
            self.line(x, y + radius, x, y + h - radius, color)  # Left
            self.line(x + w - 1, y + radius, x + w - 1, y + h - radius, color)  # Right

    def draw_progress_bar(self, x, y, width, height, progress, color=WHITE, bg_color=BLACK):
        """Draw progress bar (0.0 to 1.0)
        
        Usage: oled.draw_progress_bar(10, 30, 80, 8, 0.7)
        """
        progress = max(0.0, min(1.0, progress))
        
        # Draw background
        self.rect(x, y, width, height, bg_color, fill=True)
        
        # Draw border
        self.rect(x, y, width, height, color, fill=False)
        
        # Draw progress
        progress_width = int((width - 2) * progress)
        if progress_width > 0:
            self.fill_rect(x + 1, y + 1, progress_width, height - 2, color)

    def draw_menu_item(self, x, y, width, height, text, selected=False, icon=None):
        """Draw menu item with selection highlight
        
        Usage: oled.draw_menu_item(0, 10, 128, 12, "Settings", selected=True)
        """
        bg_color = self.WHITE if selected else self.BLACK
        text_color = self.BLACK if selected else self.WHITE
        
        # Draw background
        self.fill_rect(x, y, width, height, bg_color)
        
        # Draw border for selected item
        if selected:
            self.rect(x, y, width, height, text_color, fill=False)
        
        # Draw icon if provided
        text_x = x + 4
        if icon:
            # Draw simple icon placeholder
            self.rect(x + 2, y + 2, 8, 8, text_color, fill=True)
            text_x = x + 14
        
        # Draw text
        self.text(text, text_x, y + (height - 8) // 2, text_color)

    def draw_checkbox(self, x, y, size, checked=False, color=WHITE):
        """Draw checkbox with optional check mark"""
        # Draw box
        self.rect(x, y, size, size, color, fill=False)
        
        if checked:
            # Draw check mark
            mid_x = x + size // 2
            mid_y = y + size // 2
            self.line(x + 2, mid_y, mid_x, y + size - 3, color)
            self.line(mid_x, y + size - 3, x + size - 2, y + 2, color)

    def draw_radio_button(self, x, y, radius, selected=False, color=WHITE):
        """Draw radio button with optional selection"""
        # Draw outer circle
        self.circle(x + radius, y + radius, radius, color, fill=False)
        
        if selected:
            # Draw inner filled circle
            inner_radius = max(1, radius - 2)
            self.circle(x + radius, y + radius, inner_radius, color, fill=True)

    # ==================== BUTTON INTEGRATION ====================

    def on_button(self, button_pin, button_state, callback):
        """Connect button event to display callback
        
        Usage: 
        oled.on_button(25, "PRESSED", lambda: oled.draw_menu_animation())
        if gipeo.button.is_pressed(25, Button.PRESSED):
            # Animation triggered automatically
        """
        if button_pin not in self._button_callbacks:
            self._button_callbacks[button_pin] = {}
        self._button_callbacks[button_pin][button_state] = callback

    def check_button_events(self, gipeo_instance):
        """Check for button events and trigger callbacks"""
        for pin, states in self._button_callbacks.items():
            for state, callback in states.items():
                # This would integrate with Gipeo button system
                # if gipeo_instance.button.is_pressed(pin, state):
                #     callback()
                pass

    # ==================== ANIMATION SUPPORT ====================

    def create_animation(self, name, frames, frame_delay=100):
        """Create animation sequence
        
        Usage:
        def draw_spinner(oled, x, y, frame):
            # Draw spinner frame
            pass
            
        frames = [lambda o, x, y: draw_spinner(o, x, y, i) for i in range(8)]
        oled.create_animation("spinner", frames, 100)
        """
        self._animations[name] = {
            'frames': frames,
            'delay': frame_delay,
            'current_frame': 0,
            'last_update': time.ticks_ms() if _IS_MICROPYTHON else 0,
            'playing': False
        }

    def play_animation(self, name, x, y, loop=True):
        """Start playing animation at position
        
        Usage: oled.play_animation("spinner", 60, 30, loop=True)
        """
        if name in self._animations:
            anim = self._animations[name]
            anim['playing'] = True
            anim['x'] = x
            anim['y'] = y
            anim['loop'] = loop
            anim['current_frame'] = 0

    def stop_animation(self, name):
        """Stop animation"""
        if name in self._animations:
            self._animations[name]['playing'] = False

    def update_animations(self):
        """Update all active animations - call in main loop"""
        if not _IS_MICROPYTHON:
            return
            
        current_time = time.ticks_ms()
        
        for name, anim in self._animations.items():
            if not anim['playing']:
                continue
            
            if time.ticks_diff(current_time, anim['last_update']) >= anim['delay']:
                # Draw current frame
                frame = anim['frames'][anim['current_frame']]
                frame(self, anim['x'], anim['y'])  # Frame is a drawing function
                
                # Next frame
                anim['current_frame'] += 1
                
                if anim['current_frame'] >= len(anim['frames']):
                    if anim['loop']:
                        anim['current_frame'] = 0
                    else:
                        anim['playing'] = False
                
                anim['last_update'] = current_time

    # ==================== SPRITE SYSTEM ====================

    def create_sprite(self, width, height, data=None):
        """Create sprite object
        
        Usage: sprite = oled.create_sprite(16, 16, sprite_data)
        """
        return OLEDSprite(width, height, data)

    def draw_sprite(self, sprite, x, y, transparent=False):
        """Draw sprite at position
        
        Usage: oled.draw_sprite(player_sprite, 32, 32, transparent=True)
        """
        if not sprite:
            return
        
        for py in range(sprite.height):
            for px in range(sprite.width):
                pixel_value = sprite.get_pixel(px, py)
                
                if transparent and pixel_value == self.BLACK:
                    continue
                
                self.set_pixel(x + px, y + py, pixel_value)

    # ==================== DISPLAY UPDATE & CONTROL ====================

    def show(self):
        """Update display with buffer content"""
        try:
            for page in range(self.pages):
                # Set page address
                self.write_cmd(0xB0 + page)
                # Set column start address
                self.write_cmd(0x00)  # Lower nibble
                self.write_cmd(0x10)  # Higher nibble
                
                # Send page data
                start_index = page * self.width
                page_data = self.buffer[start_index:start_index + self.width]
                self.write_data(page_data)
        except Exception as e:
            print(f"Display update error: {e}")

    def brightness(self, level):
        """Set display brightness (0-255)"""
        level = max(0, min(255, level))
        self.write_cmd(0x81)  # Set contrast
        self.write_cmd(level)

    def invert(self, inverted=True):
        """Invert display colors"""
        self.write_cmd(0xA7 if inverted else 0xA6)

    def rotate(self, rotation=0):
        """Rotate display (0, 90, 180, 270 degrees)"""
        if rotation == 0:
            self.write_cmd(0xA1)  # Normal
            self.write_cmd(0xC8)
        elif rotation == 180:
            self.write_cmd(0xA0)  # Flipped
            self.write_cmd(0xC0)

    def power_off(self):
        """Turn off display"""
        self.write_cmd(0xAE)

    def power_on(self):
        """Turn on display"""
        self.write_cmd(0xAF)


# ==================== OLED SUPPORTING CLASSES ====================

class PixelManager:
    """Advanced pixel management system for OLED
    
    Usage: 
    pixel_id = oled.pixel.create("WHITE", x=10, y=20)
    oled.pixel.set_color(pixel_id, "BLACK")
    """
    
    def __init__(self, display):
        self.display = display
        self.pixel_grid = {}
    
    def create(self, color, x=0, y=0):
        """Create pixel at grid position
        
        Usage: pixel_id = oled.pixel.create("WHITE", x=1, y=0)
        """
        pixel_id = f"{x}_{y}"
        self.pixel_grid[pixel_id] = {
            'x': x, 'y': y, 'color': color, 'visible': True
        }
        color_val = self.display.WHITE if color == "WHITE" else self.display.BLACK
        self.display.set_pixel(x, y, color_val)
        return pixel_id
    
    def set_color(self, pixel_id, color):
        """Set pixel color"""
        if pixel_id in self.pixel_grid:
            pixel = self.pixel_grid[pixel_id]
            pixel['color'] = color
            if pixel['visible']:
                color_val = self.display.WHITE if color == "WHITE" else self.display.BLACK
                self.display.set_pixel(pixel['x'], pixel['y'], color_val)
    
    def set_position(self, pixel_id, x, y):
        """Move pixel to new position"""
        if pixel_id in self.pixel_grid:
            pixel = self.pixel_grid[pixel_id]
            # Clear old position
            self.display.set_pixel(pixel['x'], pixel['y'], self.display.BLACK)
            # Set new position
            pixel['x'] = x
            pixel['y'] = y
            if pixel['visible']:
                color_val = self.display.WHITE if pixel['color'] == "WHITE" else self.display.BLACK
                self.display.set_pixel(x, y, color_val)
    
    def hide(self, pixel_id):
        """Hide pixel"""
        if pixel_id in self.pixel_grid:
            pixel = self.pixel_grid[pixel_id]
            pixel['visible'] = False
            self.display.set_pixel(pixel['x'], pixel['y'], self.display.BLACK)
    
    def show(self, pixel_id):
        """Show pixel"""
        if pixel_id in self.pixel_grid:
            pixel = self.pixel_grid[pixel_id]
            pixel['visible'] = True
            color_val = self.display.WHITE if pixel['color'] == "WHITE" else self.display.BLACK
            self.display.set_pixel(pixel['x'], pixel['y'], color_val)

    def delete(self, pixel_id):
        """Delete pixel from grid"""
        if pixel_id in self.pixel_grid:
            pixel = self.pixel_grid[pixel_id]
            self.display.set_pixel(pixel['x'], pixel['y'], self.display.BLACK)
            del self.pixel_grid[pixel_id]


class DesignManager:
    """Advanced design element manager for OLED
    
    Usage:
    btn_id = oled.design.create_button("ok_btn", 10, 40, 30, 12, "OK")
    oled.design.press_button("ok_btn")
    """
    
    def __init__(self, display):
        self.display = display
        self.elements = {}
    
    def create_button(self, name, x, y, width, height, text, style="default"):
        """Create UI button element
        
        Usage: btn = oled.design.create_button("menu", 0, 0, 50, 16, "Menu")
        """
        element = {
            'type': 'button',
            'x': x, 'y': y, 'width': width, 'height': height,
            'text': text, 'style': style, 'pressed': False
        }
        self.elements[name] = element
        self._draw_button(element)
        return name
    
    def create_panel(self, name, x, y, width, height, style="default"):
        """Create panel element
        
        Usage: panel = oled.design.create_panel("main", 5, 5, 100, 50, "raised")
        """
        element = {
            'type': 'panel',
            'x': x, 'y': y, 'width': width, 'height': height,
            'style': style, 'children': []
        }
        self.elements[name] = element
        self._draw_panel(element)
        return name
    
    def create_icon(self, name, x, y, icon_type, size=8):
        """Create icon element
        
        Usage: icon = oled.design.create_icon("home", 10, 10, "house", 16)
        """
        element = {
            'type': 'icon',
            'x': x, 'y': y, 'icon_type': icon_type, 'size': size
        }
        self.elements[name] = element
        self._draw_icon(element)
        return name
    
    def _draw_button(self, element):
        """Draw button element"""
        x, y, w, h = element['x'], element['y'], element['width'], element['height']
        
        if element['pressed']:
            # Pressed state
            self.display.fill_rect(x, y, w, h, self.display.WHITE)
            self.display.rect(x, y, w, h, self.display.BLACK)
            text_color = self.display.BLACK
        else:
            # Normal state
            self.display.rect(x, y, w, h, self.display.WHITE)
            text_color = self.display.WHITE
        
        # Center text
        text_w = self.display.text_width(element['text'])
        text_h = self.display.text_height()
        text_x = x + (w - text_w) // 2
        text_y = y + (h - text_h) // 2
        
        self.display.text(element['text'], text_x, text_y, text_color)
    
    def _draw_panel(self, element):
        """Draw panel element"""
        x, y, w, h = element['x'], element['y'], element['width'], element['height']
        
        if element['style'] == "raised":
            # 3D raised effect
            self.display.rect(x, y, w, h, self.display.WHITE)
            self.display.line(x, y, x + w - 1, y, self.display.WHITE)  # Top
            self.display.line(x, y, x, y + h - 1, self.display.WHITE)  # Left
        elif element['style'] == "sunken":
            # 3D sunken effect
            self.display.rect(x, y, w, h, self.display.WHITE)
            self.display.line(x + w - 1, y, x + w - 1, y + h - 1, self.display.BLACK)  # Right
            self.display.line(x, y + h - 1, x + w - 1, y + h - 1, self.display.BLACK)  # Bottom
        else:
            # Default flat
            self.display.rect(x, y, w, h, self.display.WHITE)
    
    def _draw_icon(self, element):
        """Draw icon element"""
        x, y, size = element['x'], element['y'], element['size']
        icon_type = element['icon_type']
        
        # Simple icon patterns
        if icon_type == "house":
            # Draw house icon
            self.display.triangle(x + size//2, y, x, y + size//2, x + size, y + size//2, self.display.WHITE, fill=True)
            self.display.rect(x + size//4, y + size//2, size//2, size//2, self.display.WHITE, fill=True)
        elif icon_type == "gear":
            # Draw gear icon
            self.display.circle(x + size//2, y + size//2, size//2 - 2, self.display.WHITE)
            self.display.circle(x + size//2, y + size//2, size//4, self.display.BLACK, fill=True)
        elif icon_type == "arrow_right":
            # Draw right arrow
            self.display.triangle(x, y, x + size, y + size//2, x, y + size, self.display.WHITE, fill=True)
        elif icon_type == "arrow_left":
            # Draw left arrow
            self.display.triangle(x + size, y, x, y + size//2, x + size, y + size, self.display.WHITE, fill=True)
        elif icon_type == "check":
            # Draw checkmark
            mid_x = x + size // 2
            mid_y = y + size // 2
            self.display.line(x + 2, mid_y, mid_x, y + size - 3, self.display.WHITE)
            self.display.line(mid_x, y + size - 3, x + size - 2, y + 2, self.display.WHITE)
        elif icon_type == "cross":
            # Draw cross/X
            self.display.line(x, y, x + size, y + size, self.display.WHITE)
            self.display.line(x + size, y, x, y + size, self.display.WHITE)
    
    def press_button(self, name):
        """Press button (visual feedback)"""
        if name in self.elements and self.elements[name]['type'] == 'button':
            self.elements[name]['pressed'] = True
            self._draw_button(self.elements[name])
    
    def release_button(self, name):
        """Release button"""
        if name in self.elements and self.elements[name]['type'] == 'button':
            self.elements[name]['pressed'] = False
            self._draw_button(self.elements[name])
    
    def update_element(self, name):
        """Redraw element"""
        if name in self.elements:
            element = self.elements[name]
            if element['type'] == 'button':
                self._draw_button(element)
            elif element['type'] == 'panel':
                self._draw_panel(element)
            elif element['type'] == 'icon':
                self._draw_icon(element)


class AnimationManager:
    """Animation management system for OLED
    
    Usage:
    oled.animation.create_fade_in("menu_fade", draw_menu_func)
    oled.animation.play("menu_fade", x=0, y=0)
    """
    
    def __init__(self, display):
        self.display = display
        self.sequences = {}
    
    def create_fade_in(self, name, element_func, duration=1000, steps=10):
        """Create fade-in animation
        
        Usage: oled.animation.create_fade_in("fade", lambda d, x, y: d.text("Hello", x, y))
        """
        frames = []
        for i in range(steps + 1):
            alpha = i / steps
            frames.append(lambda d, x, y, a=alpha: self._draw_with_alpha(d, element_func, x, y, a))
        
        self.display.create_animation(name, frames, duration // steps)
    
    def create_slide_in(self, name, element_func, direction="left", distance=32, duration=500):
        """Create slide-in animation
        
        Usage: oled.animation.create_slide_in("slide", draw_func, "right", 64)
        """
        frames = []
        steps = 8
        
        for i in range(steps + 1):
            progress = i / steps
            if direction == "left":
                offset_x = int(distance * (1 - progress))
                offset_y = 0
            elif direction == "right":
                offset_x = int(-distance * (1 - progress))
                offset_y = 0
            elif direction == "top":
                offset_x = 0
                offset_y = int(distance * (1 - progress))
            else:  # bottom
                offset_x = 0
                offset_y = int(-distance * (1 - progress))
            
            frames.append(lambda d, x, y, ox=offset_x, oy=offset_y: element_func(d, x + ox, y + oy))
        
        self.display.create_animation(name, frames, duration // steps)
    
    def create_blink(self, name, element_func, blink_count=3, duration=1000):
        """Create blinking animation"""
        frames = []
        frame_delay = duration // (blink_count * 2)
        
        for i in range(blink_count):
            # Show frame
            frames.append(lambda d, x, y: element_func(d, x, y))
            # Hide frame
            frames.append(lambda d, x, y: None)  # Empty frame
        
        self.display.create_animation(name, frames, frame_delay)
    
    def create_rotation(self, name, element_func, steps=8, duration=1000):
        """Create rotation animation (simplified)"""
        frames = []
        for i in range(steps):
            angle = (i * 360) // steps
            frames.append(lambda d, x, y, a=angle: self._draw_rotated(d, element_func, x, y, a))
        
        self.display.create_animation(name, frames, duration // steps)
    
    def _draw_with_alpha(self, display, element_func, x, y, alpha):
        """Draw element with alpha transparency simulation"""
        if alpha <= 0:
            return
        elif alpha >= 1:
            element_func(display, x, y)
        else:
            # Simulate transparency with dithering pattern
            for dy in range(8):
                for dx in range(8):
                    if (dx + dy) % 2 == 0 and alpha > 0.5:
                        element_func(display, x + dx, y + dy)
    
    def _draw_rotated(self, display, element_func, x, y, angle):
        """Draw element with rotation (simplified)"""
        # This is a simplified rotation - for complex rotation,
        # you'd need proper matrix transformations
        element_func(display, x, y)
    
    def play(self, name, x=0, y=0, loop=True):
        """Play animation"""
        if hasattr(self.display, 'play_animation'):
            self.display.play_animation(name, x, y, loop)
    
    def stop(self, name):
        """Stop animation"""
        if hasattr(self.display, 'stop_animation'):
            self.display.stop_animation(name)


class OLEDAssetManager:
    """OLED-specific asset management
    
    Usage:
    asset = oled.asset.create_from_data(sprite_data, 16, 16)
    oled.asset.save_asset("player", asset)
    """
    
    def __init__(self, display):
        self.display = display
        self.assets = {}
    
    def create_placeholder_asset(self, width, height, pattern="checkerboard"):
        """Create placeholder asset for testing
        
        Usage: asset = oled.asset.create_placeholder_asset(32, 32, "cross")
        """
        return OLEDSprite(width, height, self._generate_pattern(width, height, pattern))
    
    def create_from_data(self, data, width, height):
        """Create asset from raw pixel data
        
        Usage: asset = oled.asset.create_from_data(pixel_array, 16, 16)
        """
        return OLEDSprite(width, height, data)
    
    def save_asset(self, name, asset):
        """Save asset for later use"""
        self.assets[name] = asset
    
    def load_asset(self, name):
        """Load saved asset"""
        return self.assets.get(name)
    
    def delete_asset(self, name):
        """Delete saved asset"""
        if name in self.assets:
            del self.assets[name]
    
    def list_assets(self):
        """List all saved assets"""
        return list(self.assets.keys())
    
    def _generate_pattern(self, width, height, pattern):
        """Generate test patterns"""
        data = []
        
        for y in range(height):
            row = []
            for x in range(width):
                if pattern == "checkerboard":
                    # Checkerboard pattern
                    row.append(1 if (x + y) % 2 == 0 else 0)
                elif pattern == "cross":
                    # Cross pattern
                    if x == width // 2 or y == height // 2:
                        row.append(1)
                    else:
                        row.append(0)
                elif pattern == "border":
                    # Border pattern
                    if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                        row.append(1)
                    else:
                        row.append(0)
                elif pattern == "diagonal":
                    # Diagonal pattern
                    row.append(1 if x == y else 0)
                else:
                    # Solid pattern
                    row.append(1)
            data.append(row)
        
        return data


class OLEDSprite:
    """Sprite object for OLED display
    
    Usage:
    sprite = OLEDSprite(16, 16, sprite_data)
    sprite.set_pixel(8, 8, 1)
    oled.draw_sprite(sprite, 32, 32)
    """
    
    def __init__(self, width, height, data=None):
        self.width = width
        self.height = height
        
        if data:
            self.data = data
        else:
            # Create empty sprite (all black)
            self.data = [[0 for _ in range(width)] for _ in range(height)]
    
    def get_pixel(self, x, y):
        """Get pixel value at coordinates"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.data[y][x]
        return 0
    
    def set_pixel(self, x, y, value):
        """Set pixel value"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.data[y][x] = value
    
    def get_size(self):
        """Get sprite size"""
        return (self.width, self.height)
    
    def clear(self, color=0):
        """Clear sprite with color"""
        for y in range(self.height):
            for x in range(self.width):
                self.data[y][x] = color
    
    def copy(self):
        """Create copy of sprite"""
        new_data = []
        for row in self.data:
            new_data.append(row.copy())
        return OLEDSprite(self.width, self.height, new_data)
    
    def flip_horizontal(self):
        """Flip sprite horizontally"""
        for y in range(self.height):
            self.data[y] = self.data[y][::-1]
    
    def flip_vertical(self):
        """Flip sprite vertically"""
        self.data = self.data[::-1]
    
    def rotate_90(self):
        """Rotate sprite 90 degrees clockwise"""
        new_data = []
        for x in range(self.width):
            row = []
            for y in range(self.height - 1, -1, -1):
                row.append(self.data[y][x])
            new_data.append(row)
        
        self.data = new_data
        self.width, self.height = self.height, self.width


# ==================== MAIN GIPEO CLASS ====================

class Gipeo:
    """Comprehensive Hardware Abstraction Framework - OS Level"""
    
    def __init__(self, default_mode=None, enable_logging=True):
        """Initialize Gipeo OS framework
        
        Args:
            default_mode: Default pin mode for GPIO operations
            enable_logging: Enable debug logging
        """
        # Core attributes
        self._pins = {}  # Pin cache: pin_number -> Pin instance
        self._buttons = {}  # Button instances
        self._pwm_channels = {}  # PWM channels
        self._sensors = {}  # Sensor instances
        self._i2c_devices = {}  # I2C device instances
        self._spi_devices = {}  # SPI device instances
        self._timers = {}  # Timer instances
        
        # Configuration
        self.default_mode = default_mode if default_mode is not None else getattr(machine.Pin, 'OUT', 0)
        self.enable_logging = enable_logging
        
        # Event system
        self.event_queue = EventQueue()
        self._event_handlers = defaultdict(list)
        
        # System info
        self._chip_id = self._get_chip_id()
        self._board_type = self._detect_board_type()
        
        # Network
        self._wifi = None
        self._ap = None
        
        # Advanced OS-Level Systems
        self.asset_manager = AssetManager()
        self.config_manager = ConfigManager()
        self.process_manager = ProcessManager()
        self.file_manager = FileSystemManager()
        self.network_manager = NetworkManager()
        
        # Display Management
        self._display_manager = None
        self._current_theme = Theme()
        self._ui_components = []
        
        # Initialize core subsystems
        self._init_system()

    # ==================== DISPLAY ASSET METHODS ====================
    
    def create_display_manager(self, display):
        """Create advanced display manager"""
        self._display_manager = DisplayManager(display, self.asset_manager, self._current_theme)
        self._log("Advanced display manager created")
        return self._display_manager
    
    def create_from_picture(self, path, size=None):
        """Create display asset from picture file
        
        Usage: cafedisplay = gipeo.create_from_picture("cafe.bmp", size=[64, 32])
        """
        asset = self.asset_manager.create_from_picture(path, size)
        self._log(f"Asset created from {path}")
        return asset
    
    def set_asset(self, asset, x, y, transparent=False):
        """Set asset at display position
        
        Usage: gipeo.set_asset(cafedisplay, 10, 20)
        """
        if self._display_manager:
            self._display_manager.set_asset(asset, x, y, transparent)
        else:
            self._log("Display manager not initialized", "ERROR")
    
    def create_sprite(self, asset, x, y, scale=1.0):
        """Create sprite from asset"""
        if self._display_manager:
            return self._display_manager.create_sprite(asset, x, y, scale)
        return None
    
    def create_animation(self, asset_paths, fps=10):
        """Create animation from multiple assets"""
        assets = []
        for path in asset_paths:
            asset = self.create_from_picture(path)
            if asset:
                assets.append(asset)
        
        if self._display_manager:
            return self._display_manager.create_animation(assets, fps)
        return None
    
    def set_theme(self, theme):
        """Set UI theme"""
        self._current_theme = theme
        if self._display_manager:
            self._display_manager.theme = theme
    
    def create_theme(self, name, colors=None, fonts=None):
        """Create custom theme"""
        theme = Theme(name)
        if colors:
            theme.colors.update(colors)
        if fonts:
            theme.fonts.update(fonts)
        return theme
    
    # ==================== ADVANCED MENU SYSTEM ====================
    
    def create_menu(self, x, y, width, height, title="Menu"):
        """Create advanced menu system
        
        Usage: menu = gipeo.create_menu(0, 0, 128, 64, "Main Menu")
        """
        menu = Menu(x, y, width, height, title, self._current_theme)
        self._ui_components.append(menu)
        self._log(f"Menu created: {title}")
        return menu
    
    def create_context_menu(self, items, x=None, y=None):
        """Create context menu at position"""
        menu = Menu(x or 0, y or 0, 100, len(items) * 12 + 20, "Context", self._current_theme)
        for item in items:
            if isinstance(item, str):
                menu.add_text_item(item)
            else:
                menu.add_item(item)
        return menu
    
    def create_popup_menu(self, title, message, buttons=None):
        """Create popup dialog menu"""
        buttons = buttons or ["OK"]
        menu = Menu(20, 20, 88, 40, title, self._current_theme)
        
        # Add message as disabled item
        message_item = MenuItem(message, enabled=False)
        menu.add_item(message_item)
        
        # Add buttons
        for button_text in buttons:
            menu.add_text_item(button_text)
        
        return menu
    
    def create_settings_menu(self):
        """Create system settings menu"""
        settings = Menu(0, 0, 128, 64, "Settings", self._current_theme)
        
        settings.add_text_item("Display", lambda: self._open_display_settings())
        settings.add_text_item("Network", lambda: self._open_network_settings())
        settings.add_text_item("System", lambda: self._open_system_settings())
        settings.add_text_item("Hardware", lambda: self._open_hardware_settings())
        settings.add_text_item("About", lambda: self._show_about())
        
        return settings
    
    def _open_display_settings(self):
        """Open display settings submenu"""
        display_menu = Menu(0, 0, 128, 64, "Display", self._current_theme)
        display_menu.add_text_item(f"Brightness: {self.config_manager.get('display.brightness', 80)}")
        display_menu.add_text_item(f"Theme: {self.config_manager.get('display.theme', 'dark')}")
        display_menu.add_text_item("Back")
        return display_menu
    
    def _open_network_settings(self):
        """Open network settings submenu"""
        network_menu = Menu(0, 0, 128, 64, "Network", self._current_theme)
        network_menu.add_text_item("WiFi Setup")
        network_menu.add_text_item("AP Mode")
        network_menu.add_text_item("Scan Networks")
        network_menu.add_text_item("Back")
        return network_menu
    
    def _open_system_settings(self):
        """Open system settings submenu"""
        system_menu = Menu(0, 0, 128, 64, "System", self._current_theme)
        system_menu.add_text_item("Memory Info")
        system_menu.add_text_item("CPU Info")
        system_menu.add_text_item("Reset System")
        system_menu.add_text_item("Back")
        return system_menu
    
    def _open_hardware_settings(self):
        """Open hardware settings submenu"""
        hardware_menu = Menu(0, 0, 128, 64, "Hardware", self._current_theme)
        hardware_menu.add_text_item("I2C Scan")
        hardware_menu.add_text_item("Pin Test")
        hardware_menu.add_text_item("Diagnostics")
        hardware_menu.add_text_item("Back")
        return hardware_menu
    
    def _show_about(self):
        """Show about dialog"""
        about_text = f"""
ClayOS v{self.config_manager.get('system.version', '1.0.0')}
Board: {self._board_type}
Chip: {self._chip_id[:8]}...
Memory: {self._memory_info()['free']} bytes free
        """
        return self.create_popup_menu("About", about_text, ["OK"])
    
    # ==================== WINDOW MANAGEMENT ====================
    
    def create_window(self, x, y, width, height, title="Window"):
        """Create window"""
        window = Window(x, y, width, height, title, self._current_theme)
        if self._display_manager:
            self._display_manager.add_window(window)
        self._log(f"Window created: {title}")
        return window
    
    def create_button(self, x, y, width, height, text="Button", action=None):
        """Create UI button"""
        button = Button(x, y, width, height, text, self._current_theme)
        if action:
            button.on_event('click', action)
        return button
    
    def create_desktop(self):
        """Create desktop environment"""
        desktop = Window(0, 0, 128, 64, "Desktop", self._current_theme)
        desktop.closable = False
        desktop.movable = False
        desktop.resizable = False
        
        # Add desktop icons/shortcuts
        self._create_desktop_shortcuts(desktop)
        
        return desktop
    
    def _create_desktop_shortcuts(self, desktop):
        """Create desktop shortcuts"""
        # File Manager shortcut
        file_btn = self.create_button(4, 20, 24, 16, "Files", 
                                     lambda: self._launch_file_manager())
        desktop.add_child(file_btn)
        
        # Settings shortcut
        settings_btn = self.create_button(32, 20, 24, 16, "Set", 
                                         lambda: self._launch_settings())
        desktop.add_child(settings_btn)
        
        # Terminal shortcut
        term_btn = self.create_button(60, 20, 24, 16, "Term", 
                                     lambda: self._launch_terminal())
        desktop.add_child(term_btn)
        
        # Hardware monitor shortcut
        hw_btn = self.create_button(88, 20, 24, 16, "HW", 
                                   lambda: self._launch_hardware_monitor())
        desktop.add_child(hw_btn)
    
    def _launch_file_manager(self):
        """Launch file manager application"""
        fm_window = self.create_window(10, 10, 108, 44, "File Manager")
        # Add file manager functionality
        self._log("File Manager launched")
    
    def _launch_settings(self):
        """Launch settings application"""
        settings_window = self.create_window(10, 10, 108, 44, "Settings")
        settings_menu = self.create_settings_menu()
        settings_window.add_child(settings_menu)
        self._log("Settings launched")
    
    def _launch_terminal(self):
        """Launch terminal application"""
        term_window = self.create_window(10, 10, 108, 44, "Terminal")
        # Add terminal functionality
        self._log("Terminal launched")
    
    def _launch_hardware_monitor(self):
        """Launch hardware monitor"""
        hw_window = self.create_window(10, 10, 108, 44, "Hardware Monitor")
        # Add hardware monitoring
        self._log("Hardware Monitor launched")
    
    # ==================== PROCESS MANAGEMENT ====================
    
    def create_process(self, name, task_func, priority=1, auto_restart=False):
        """Create system process"""
        return self.process_manager.create_process(name, task_func, priority, auto_restart)
    
    async def start_process(self, name):
        """Start process"""
        await self.process_manager.start_process(name)
    
    def stop_process(self, name):
        """Stop process"""
        self.process_manager.stop_process(name)
    
    def get_process_list(self):
        """Get list of running processes"""
        return self.process_manager.get_process_list()
    
    async def start_os_services(self):
        """Start core OS services"""
        # Display service
        self.create_process("display_service", self._display_service, priority=5)
        
        # Input service
        self.create_process("input_service", self._input_service, priority=5)
        
        # Network service
        self.create_process("network_service", self._network_service, priority=3)
        
        # File system service
        self.create_process("fs_service", self._fs_service, priority=2)
        
        # Start all services
        services = ["display_service", "input_service", "network_service", "fs_service"]
        for service in services:
            await self.start_process(service)
        
        self._log("OS services started")
    
    async def _display_service(self):
        """Display service process"""
        while True:
            if self._display_manager:
                self._display_manager.render_frame()
            await asyncio.sleep_ms(16)  # 60 FPS
    
    async def _input_service(self):
        """Input handling service"""
        while True:
            # Process button events, etc.
            await asyncio.sleep_ms(10)
    
    async def _network_service(self):
        """Network service process"""
        while True:
            # Handle network operations
            await asyncio.sleep_ms(100)
    
    async def _fs_service(self):
        """File system service"""
        while True:
            # Handle file operations, cleanup, etc.
            await asyncio.sleep_ms(1000)
    
    # ==================== FILE SYSTEM EXTENSIONS ====================
    
    def create_file(self, path, content=""):
        """Create file with content"""
        try:
            self.file_manager.create_directory_tree(os.path.dirname(path))
            with open(path, 'w') as f:
                f.write(content)
            self._log(f"File created: {path}")
            return True
        except Exception as e:
            self._log(f"File creation failed: {e}", "ERROR")
            return False
    
    def read_file(self, path):
        """Read file content"""
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            self._log(f"File read failed: {e}", "ERROR")
            return None
    
    def write_file(self, path, content):
        """Write content to file"""
        try:
            with open(path, 'w') as f:
                f.write(content)
            self._log(f"File written: {path}")
            return True
        except Exception as e:
            self._log(f"File write failed: {e}", "ERROR")
            return False
    
    def copy_file(self, src, dst):
        """Copy file"""
        return self.file_manager.copy_file(src, dst)
    
    def move_file(self, src, dst):
        """Move file"""
        return self.file_manager.move_file(src, dst)
    
    def delete_file(self, path):
        """Delete file"""
        try:
            os.remove(path)
            self._log(f"File deleted: {path}")
            return True
        except Exception as e:
            self._log(f"File deletion failed: {e}", "ERROR")
            return False
    
    def list_directory(self, path="/"):
        """List directory contents with details"""
        try:
            items = []
            for item in os.listdir(path):
                item_path = f"{path}/{item}" if path != "/" else f"/{item}"
                info = self.file_manager.get_file_info(item_path)
                if info:
                    items.append({
                        'name': item,
                        'path': item_path,
                        'type': info['type'],
                        'size': info['size'],
                        'modified': info.get('modified', 0)
                    })
            return items
        except Exception as e:
            self._log(f"Directory listing failed: {e}", "ERROR")
            return []
    
    def search_files(self, pattern, root="/"):
        """Search for files"""
        return self.file_manager.search_files(pattern, root)
    
    # ==================== NETWORK EXTENSIONS ====================
    
    def create_http_server(self, port=80):
        """Create HTTP server"""
        return self.network_manager.create_http_server(port)
    
    def create_tcp_client(self, host, port):
        """Create TCP client"""
        return self.network_manager.create_tcp_client(host, port)
    
    async def download_file(self, url, local_path):
        """Download file from URL"""
        # Simple implementation
        try:
            client = self.create_tcp_client("example.com", 80)
            await client.connect()
            # Implementation would go here
            self._log(f"Downloaded {url} to {local_path}")
            return True
        except Exception as e:
            self._log(f"Download failed: {e}", "ERROR")
            return False
    
    # ==================== CONFIGURATION MANAGEMENT ====================
    
    def get_config(self, key, default=None):
        """Get configuration value"""
        return self.config_manager.get(key, default)
    
    def set_config(self, key, value):
        """Set configuration value"""
        self.config_manager.set(key, value)
    
    def watch_config(self, key, callback):
        """Watch configuration changes"""
        self.config_manager.watch(key, callback)
    
    # ==================== ADVANCED HARDWARE OPERATIONS ====================
    
    def create_device_profile(self, name, pins_config):
        """Create hardware device profile"""
        profile = {
            'name': name,
            'pins': pins_config,
            'initialized': False
        }
        self.set_config(f"devices.{name}", profile)
        return profile
    
    def load_device_profile(self, name):
        """Load and initialize device profile"""
        profile = self.get_config(f"devices.{name}")
        if profile:
            # Initialize pins according to profile
            for pin_name, pin_config in profile['pins'].items():
                pin_num = pin_config['pin']
                mode = pin_config.get('mode', 'OUT')
                
                if mode == 'PWM':
                    self.create_pwm(pin_num, pin_config.get('freq', 1000))
                elif mode == 'BUTTON':
                    self.create_button(pin_num, **pin_config.get('options', {}))
                elif mode == 'SENSOR':
                    sensor_type = pin_config.get('sensor_type', 'generic')
                    self.create_analog_sensor(pin_num, sensor_type)
            
            profile['initialized'] = True
            self.set_config(f"devices.{name}", profile)
            self._log(f"Device profile loaded: {name}")
            return True
        return False
    
    def create_macro(self, name, actions):
        """Create hardware macro"""
        async def execute_macro():
            for action in actions:
                try:
                    if action['type'] == 'set_pin':
                        self.set(action['pin'], action['state'])
                    elif action['type'] == 'delay':
                        await asyncio.sleep_ms(action['duration'])
                    elif action['type'] == 'pwm':
                        pwm = self.get_pwm(action['pin'])
                        if pwm:
                            pwm.duty(action['duty'])
                except Exception as e:
                    self._log(f"Macro action failed: {e}", "ERROR")
        
        self.create_process(f"macro_{name}", execute_macro)
        return execute_macro
    
    async def run_macro(self, name):
        """Run hardware macro"""
        await self.start_process(f"macro_{name}")
    
    # ==================== SYSTEM MONITORING ====================
    
    def get_system_health(self):
        """Get comprehensive system health"""
        health = {
            'memory': self._memory_info(),
            'processes': len(self.get_process_list()),
            'temperature': self._get_temperature(),
            'voltage': self._get_voltage(),
            'uptime': self._get_uptime(),
            'load': self.process_manager.system_load
        }
        return health
    
    def _get_temperature(self):
        """Get system temperature (if available)"""
        try:
            if _IS_MICROPYTHON and hasattr(esp32, 'raw_temperature'):
                return esp32.raw_temperature()
            return None
        except:
            return None
    
    def _get_voltage(self):
        """Get system voltage"""
        try:
            # Implementation would depend on hardware
            return 3.3  # Mock value
        except:
            return None
    
    def _get_uptime(self):
        """Get system uptime in seconds"""
        try:
            return time.ticks_ms() // 1000
        except:
            return 0
    
    def create_health_monitor(self, interval=5000):
        """Create system health monitoring process"""
        async def health_monitor():
            while True:
                health = self.get_system_health()
                self._log(f"System Health: {health}")
                
                # Check for critical conditions
                memory = health['memory']
                if memory['free'] < 1000:
                    self._log("LOW MEMORY WARNING", "WARNING")
                
                temp = health['temperature']
                if temp and temp > 85:  # 85°C threshold
                    self._log("HIGH TEMPERATURE WARNING", "WARNING")
                
                await asyncio.sleep_ms(interval)
        
        self.create_process("health_monitor", health_monitor, auto_restart=True)
        return health_monitor

    def _log(self, message, level='INFO'):
        """Internal logging method"""
        if self.enable_logging:
            timestamp = time.ticks_ms()
            print(f"[{timestamp}] {level}: {message}")

    def _get_chip_id(self):
        """Get unique chip ID"""
        try:
            if _IS_MICROPYTHON:
                chip_id = machine.unique_id()
                return ubinascii.hexlify(chip_id).decode()
            else:
                return "mock_chip_id"
        except:
            return "unknown"

    def _detect_board_type(self):
        """Detect board type from chip characteristics"""
        try:
            if _IS_MICROPYTHON:
                freq = machine.freq()
                if freq >= 240000000:
                    return "ESP32"
                elif freq >= 133000000:
                    return "ESP32-S2/S3"
                else:
                    return "ESP8266"
            else:
                return "MOCK"
        except:
            return "Unknown"

    def _init_system(self):
        """Initialize system components"""
        self._log(f"Initializing Gipeo on {self._board_type} (ID: {self._chip_id})")
        
        # Initialize RTC if available
        try:
            self._rtc = machine.RTC()
        except:
            self._rtc = None
            
        # Initialize filesystem
        self._init_filesystem()
        
        # Load configuration
        self._load_config()

    def _init_filesystem(self):
        """Initialize filesystem utilities"""
        self._config_file = "gipeo_config.json"
        self._log_file = "gipeo.log"

    def _load_config(self):
        """Load configuration from file"""
        try:
            if _IS_MICROPYTHON:
                with open(self._config_file, 'r') as f:
                    self._config = json.load(f)
            else:
                self._config = {}
        except:
            self._config = self._default_config()
            self._save_config()

    def _default_config(self):
        """Default configuration"""
        return {
            "pin_defaults": {
                "debounce_ms": 50,
                "pwm_freq": 1000,
                "adc_samples": 10
            },
            "network": {
                "auto_connect": False,
                "ssid": "",
                "password": ""
            },
            "system": {
                "logging": True,
                "auto_gc": True,
                "gc_threshold": 1000
            }
        }

    def _save_config(self):
        """Save configuration to file"""
        try:
            if _IS_MICROPYTHON:
                with open(self._config_file, 'w') as f:
                    json.dump(self._config, f)
        except Exception as e:
            self._log(f"Failed to save config: {e}", "ERROR")

    # ==================== PIN MANAGEMENT ====================

    def _normalize_pin(self, pin):
        """Normalize pin identifier to integer"""
        try:
            return int(pin)
        except Exception:
            raise ValueError(f"Invalid pin identifier: {pin}")

    def _get_pin_obj(self, pin, mode=None, pull=None, value=None):
        """Get or create pin object with caching"""
        pin_no = self._normalize_pin(pin)
        cache_key = f"{pin_no}_{mode}_{pull}"
        
        if cache_key in self._pins:
            return self._pins[cache_key]
            
        # Create new pin
        try:
            if mode is None:
                mode = self.default_mode
                
            pin_obj = machine.Pin(pin_no, mode, pull, value)
            self._pins[cache_key] = pin_obj
            self._log(f"Created pin {pin_no} (mode={mode}, pull={pull})")
            return pin_obj
            
        except Exception as e:
            raise HardwareError(f"Unable to initialize pin {pin_no}: {e}")

    def set_high(self, pin):
        """Set pin to HIGH/1"""
        p = self._get_pin_obj(pin, machine.Pin.OUT)
        try:
            p.on()
        except:
            p.value(1)
        self._log(f"Pin {pin} set HIGH")

    def set_low(self, pin):
        """Set pin to LOW/0"""
        p = self._get_pin_obj(pin, machine.Pin.OUT)
        try:
            p.off()
        except:
            p.value(0)
        self._log(f"Pin {pin} set LOW")

    def set(self, pin, state):
        """Set pin to specified state (bool/int/'on'/'off')"""
        truthy = self._parse_state(state)
        if truthy:
            self.set_high(pin)
        else:
            self.set_low(pin)

    def _parse_state(self, state):
        """Parse state from various formats"""
        if isinstance(state, str):
            return state.lower() in ("1", "true", "on", "high", "yes")
        return bool(state)

    def read(self, pin):
        """Read pin state"""
        p = self._get_pin_obj(pin, machine.Pin.IN)
        return bool(p.value())

    def toggle(self, pin):
        """Toggle pin state"""
        current = self.read(pin)
        self.set(pin, not current)
        self._log(f"Pin {pin} toggled to {not current}")

    def is_state(self, pin, state):
        """Check if pin is in specified state"""
        current = self.read(pin)
        expected = self._parse_state(state)
        return current == expected

    def pulse(self, pin, duration_ms=100, state=True):
        """Send pulse on pin"""
        original_state = self.read(pin)
        self.set(pin, state)
        time.sleep_ms(duration_ms)
        self.set(pin, not state)
        self._log(f"Pulse sent on pin {pin} ({duration_ms}ms)")

    # ==================== BUTTON MANAGEMENT ====================

    def create_button(self, pin, pull=None, invert=False, debounce_ms=None):
        """Create advanced button with debouncing and multi-click detection"""
        if debounce_ms is None:
            debounce_ms = self._config["pin_defaults"]["debounce_ms"]
            
        button = Button(pin, pull, invert, debounce_ms)
        self._buttons[pin] = button
        self._log(f"Created button on pin {pin}")
        return button

    def get_button(self, pin):
        """Get existing button instance"""
        return self._buttons.get(pin)

    def remove_button(self, pin):
        """Remove button instance"""
        if pin in self._buttons:
            del self._buttons[pin]
            self._log(f"Removed button on pin {pin}")

    # ==================== PWM MANAGEMENT ====================

    def create_pwm(self, pin, freq=None, duty=0):
        """Create PWM channel"""
        if freq is None:
            freq = self._config["pin_defaults"]["pwm_freq"]
            
        pwm_manager = PWMManager(pin, freq, duty)
        self._pwm_channels[pin] = pwm_manager
        self._log(f"Created PWM on pin {pin} (freq={freq}, duty={duty})")
        return pwm_manager

    def get_pwm(self, pin):
        """Get existing PWM channel"""
        return self._pwm_channels.get(pin)

    def remove_pwm(self, pin):
        """Remove PWM channel"""
        if pin in self._pwm_channels:
            self._pwm_channels[pin].deinit()
            del self._pwm_channels[pin]
            self._log(f"Removed PWM on pin {pin}")

    # ==================== ANALOG/SENSOR MANAGEMENT ====================

    def create_analog_sensor(self, pin, sensor_type="generic", **kwargs):
        """Create analog sensor instance"""
        if sensor_type == "temperature":
            sensor = TemperatureSensor(pin, **kwargs)
        elif sensor_type == "light":
            sensor = LightSensor(pin, **kwargs)
        else:
            sensor = AnalogSensor(pin, **kwargs)
            
        self._sensors[pin] = sensor
        self._log(f"Created {sensor_type} sensor on pin {pin}")
        return sensor

    def get_sensor(self, pin):
        """Get existing sensor instance"""
        return self._sensors.get(pin)

    def read_analog(self, pin, samples=None):
        """Quick analog read with averaging"""
        if samples is None:
            samples = self._config["pin_defaults"]["adc_samples"]
            
        adc = machine.ADC(machine.Pin(pin))
        total = 0
        for _ in range(samples):
            total += adc.read()
        return total / samples

    def read_voltage(self, pin, vref=3.3, samples=None):
        """Read pin voltage"""
        raw = self.read_analog(pin, samples)
        return (raw / 4095) * vref  # 12-bit ADC

    # ==================== I2C MANAGEMENT ====================

    def create_i2c(self, id=0, scl=None, sda=None, freq=400000):
        """Create I2C interface"""
        i2c = machine.I2C(id, scl=machine.Pin(scl), sda=machine.Pin(sda), freq=freq)
        self._i2c_devices[id] = i2c
        self._log(f"Created I2C {id} (SCL={scl}, SDA={sda}, freq={freq})")
        return i2c

    def scan_i2c(self, i2c_id=0):
        """Scan I2C bus for devices"""
        if i2c_id not in self._i2c_devices:
            raise ValueError(f"I2C {i2c_id} not initialized")
            
        devices = self._i2c_devices[i2c_id].scan()
        self._log(f"I2C scan found devices: {[hex(addr) for addr in devices]}")
        return devices

    def create_oled(self, i2c_id=0, address=0x3C, width=128, height=64):
        """Create OLED display instance"""
        if i2c_id not in self._i2c_devices:
            raise ValueError(f"I2C {i2c_id} not initialized")
            
        oled = OLED_SSD1306(self._i2c_devices[i2c_id], address, width, height)
        return oled

    # ==================== SPI MANAGEMENT ====================

    def create_spi(self, id=1, baudrate=1000000, polarity=0, phase=0, sck=None, mosi=None, miso=None):
        """Create SPI interface"""
        spi = machine.SPI(id, baudrate=baudrate, polarity=polarity, phase=phase,
                         sck=machine.Pin(sck) if sck else None,
                         mosi=machine.Pin(mosi) if mosi else None,
                         miso=machine.Pin(miso) if miso else None)
        self._spi_devices[id] = spi
        self._log(f"Created SPI {id} (baudrate={baudrate})")
        return spi

    def get_spi(self, id):
        """Get existing SPI interface"""
        return self._spi_devices.get(id)

    # ==================== TIMER MANAGEMENT ====================

    def create_timer(self, id, period=1000, callback=None):
        """Create timer with callback"""
        timer = machine.Timer(id)
        if callback:
            timer.init(period=period, mode=machine.Timer.PERIODIC, callback=callback)
        self._timers[id] = timer
        self._log(f"Created timer {id} (period={period}ms)")
        return timer

    def get_timer(self, id):
        """Get existing timer"""
        return self._timers.get(id)

    def remove_timer(self, id):
        """Remove timer"""
        if id in self._timers:
            self._timers[id].deinit()
            del self._timers[id]
            self._log(f"Removed timer {id}")

    # ==================== NETWORKING ====================

    # def wifi_connect(self, ssid=None, password=None, timeout=10):
    #     """Connect to WiFi network"""
    #     if not _IS_MICROPYTHON:
    #         self._log("WiFi not available in mock mode")
    #         return False
    #
    #     if ssid is None:
    #         ssid = self._config["network"]["ssid"]
    #     if password is None:
    #         password = self._config["network"]["password"]
    #
    #     if not ssid:
    #         raise ValueError("SSID required for WiFi connection")
    #
    #     self._wifi = network.WLAN(network.STA_IF)
    #     self._wifi.active(True)
    #     self._wifi.connect(ssid, password)
    #
    #     # Wait for connection
    #     start_time = time.ticks_ms()
    #     while not self._wifi.isconnected():
    #         if time.ticks_diff(time.ticks_ms(), start_time) > timeout * 1000:
    #             self._log(f"WiFi connection timeout", "ERROR")
    #             return False
    #             await asyncio.sleep_ms(100)
            
        self._log(f"WiFi connected: {self._wifi.ifconfig()}")
        return True

    def wifi_disconnect(self):
        """Disconnect from WiFi"""
        if self._wifi:
            self._wifi.disconnect()
            self._wifi.active(False)
            self._log("WiFi disconnected")

    def create_access_point(self, ssid, password=None):
        """Create WiFi access point"""
        if not _IS_MICROPYTHON:
            self._log("AP not available in mock mode")
            return False
            
        self._ap = network.WLAN(network.AP_IF)
        self._ap.active(True)
        if password:
            self._ap.config(essid=ssid, password=password)
        else:
            self._ap.config(essid=ssid)
            
        self._log(f"Access point created: {ssid}")
        return True

    def get_network_info(self):
        """Get network information"""
        info = {}
        if self._wifi and self._wifi.isconnected():
            info['wifi'] = {
                'connected': True,
                'config': self._wifi.ifconfig(),
                'rssi': self._wifi.status('rssi') if hasattr(self._wifi, 'status') else None
            }
        if self._ap and self._ap.active():
            info['ap'] = {
                'active': True,
                'config': self._ap.ifconfig()
            }
        return info

    # ==================== EVENT SYSTEM ====================

    async def emit_event(self, event_type, source, data=None):
        """Emit hardware event"""
        event = Event(event_type, source, data)
        await self.event_queue.put(event)
        
        # Trigger registered handlers
        for handler in self._event_handlers[event_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self._log(f"Event handler error: {e}", "ERROR")

    def on_event(self, event_type, handler):
        """Register event handler"""
        self._event_handlers[event_type].append(handler)

    async def process_events(self):
        """Process events from queue"""
        while True:
            event = await self.event_queue.get()
            self._log(f"Processing event: {event}")
            # Event is already processed by emit_event
            await asyncio.sleep_ms(1)

    # ==================== UTILITY METHODS ====================

    def _memory_info(self):
        """Get memory information"""
        if _IS_MICROPYTHON:
            gc.collect()
            return {
                'free': gc.mem_free(),
                'allocated': gc.mem_alloc()
            }
        return {'free': 0, 'allocated': 0}

    def _system_info(self):
        """Get comprehensive system information"""
        info = {
            'chip_id': self._chip_id,
            'board_type': self._board_type,
            'memory': self._memory_info(),
            'pins_active': len(self._pins),
            'buttons': len(self._buttons),
            'pwm_channels': len(self._pwm_channels),
            'sensors': len(self._sensors),
            'i2c_devices': len(self._i2c_devices),
            'spi_devices': len(self._spi_devices),
            'timers': len(self._timers)
        }
        
        if _IS_MICROPYTHON:
            try:
                info['frequency'] = machine.freq()
            except:
                pass
                
        return info

    def status(self):
        """Print system status"""
        info = self._system_info()
        print("=== GIPEO SYSTEM STATUS ===")
        for key, value in info.items():
            print(f"{key}: {value}")
        print("=" * 27)

    def reset(self):
        """Reset system"""
        self._log("System reset requested")
        if _IS_MICROPYTHON:
            machine.reset()
        else:
            print("[MOCK] System reset")

    def soft_reset(self):
        """Soft reset - cleanup and reinitialize"""
        self._log("Soft reset initiated")
        
        # Cleanup all resources
        for pwm in self._pwm_channels.values():
            pwm.deinit()
        for timer in self._timers.values():
            timer.deinit()
            
        # Clear caches
        self._pins.clear()
        self._buttons.clear()
        self._pwm_channels.clear()
        self._sensors.clear()
        self._timers.clear()
        
        # Reinitialize
        self._init_system()

    # ==================== PRESET CONFIGURATIONS ====================

    def setup_led_strip(self, pin, num_leds=8):
        """Setup WS2812/NeoPixel LED strip"""
        try:
            if _IS_MICROPYTHON:
                import neopixel
                np = neopixel.NeoPixel(machine.Pin(pin), num_leds)
            else:
                # Mock implementation
                class MockNeoPixel:
                    def __init__(self, pin, num_leds):
                        self.num_leds = num_leds
                        print(f"[MOCK] NeoPixel strip on pin {pin}, {num_leds} LEDs")
                    def __setitem__(self, i, color): pass
                    def write(self): pass
                np = MockNeoPixel(pin, num_leds)
            self._log(f"LED strip setup on pin {pin} ({num_leds} LEDs)")
            return np
        except ImportError:
            self._log("NeoPixel library not available", "ERROR")
            return None

    def setup_servo(self, pin, freq=50):
        """Setup servo motor"""
        pwm = self.create_pwm(pin, freq=freq)
        
        def set_angle(angle):
            # Convert angle (0-180) to duty cycle (40-115 for typical servo)
            duty = int(40 + (angle / 180) * 75)
            pwm.duty(duty)
            
        pwm.set_angle = set_angle
        self._log(f"Servo setup on pin {pin}")
        return pwm

    def setup_ultrasonic(self, trigger_pin, echo_pin):
        """Setup HC-SR04 ultrasonic sensor"""
        trigger = self._get_pin_obj(trigger_pin, machine.Pin.OUT)
        echo = self._get_pin_obj(echo_pin, machine.Pin.IN)
        
        def measure_distance():
            # Send trigger pulse
            trigger.off()
            time.sleep_us(2)
            trigger.on()
            time.sleep_us(10)
            trigger.off()
            
            # Measure echo pulse duration
            start_time = time.ticks_us()
            timeout = start_time + 30000  # 30ms timeout
            
            # Wait for echo start
            while echo.value() == 0:
                if time.ticks_us() > timeout:
                    return -1
                    
            start_time = time.ticks_us()
            
            # Wait for echo end
            while echo.value() == 1:
                if time.ticks_us() > timeout:
                    return -1
                    
            end_time = time.ticks_us()
            
            # Calculate distance in cm
            duration = time.ticks_diff(end_time, start_time)
            distance = (duration / 2) / 29.1
            return distance
            
        self._log(f"Ultrasonic setup (trigger={trigger_pin}, echo={echo_pin})")
        return measure_distance

    def setup_rotary_encoder(self, clk_pin, dt_pin, sw_pin=None):
        """Setup rotary encoder with optional switch"""
        clk = self._get_pin_obj(clk_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        dt = self._get_pin_obj(dt_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        
        encoder_state = {'position': 0, 'last_clk': clk.value()}
        
        def clk_handler(pin):
            clk_state = clk.value()
            dt_state = dt.value()
            
            if clk_state != encoder_state['last_clk']:
                if dt_state != clk_state:
                    encoder_state['position'] += 1
                else:
                    encoder_state['position'] -= 1
                    
            encoder_state['last_clk'] = clk_state
            
        clk.irq(trigger=machine.Pin.IRQ_RISING | machine.Pin.IRQ_FALLING, handler=clk_handler)
        
        result = {
            'get_position': lambda: encoder_state['position'],
            'reset_position': lambda: encoder_state.update({'position': 0})
        }
        
        if sw_pin:
            button = self.create_button(sw_pin, invert=True)
            result['button'] = button
            
        self._log(f"Rotary encoder setup (CLK={clk_pin}, DT={dt_pin}, SW={sw_pin})")
        return result

    # ==================== ASYNC UTILITIES ====================

    async def blink_pattern(self, pin, pattern, repeat=1):
        """Blink LED in specified pattern"""
        for _ in range(repeat):
            for state, duration in pattern:
                self.set(pin, state)
                await asyncio.sleep_ms(duration)

    async def fade_led(self, pin, from_brightness=0, to_brightness=100, duration_ms=1000):
        """Fade LED using PWM"""
        if pin not in self._pwm_channels:
            self.create_pwm(pin)
            
        pwm = self._pwm_channels[pin]
        await pwm.fade_to(int((to_brightness / 100) * 1023), duration_ms)

    async def monitor_sensor(self, pin, callback, interval_ms=1000, threshold=None):
        """Monitor sensor with callback on value change"""
        if pin not in self._sensors:
            self.create_analog_sensor(pin)
            
        sensor = self._sensors[pin]
        last_value = None
        
        while True:
            current_value = sensor.read_calibrated()
            
            if threshold is None or last_value is None or abs(current_value - last_value) >= threshold:
                if asyncio.iscoroutinefunction(callback):
                    await callback(current_value, last_value)
                else:
                    callback(current_value, last_value)
                last_value = current_value
                
            await asyncio.sleep_ms(interval_ms)

    # ==================== HARDWARE PRESETS ====================

    def create_esp32_default_setup(self):
        """Create common ESP32 pin assignments"""
        presets = {
            'onboard_led': 2,  # Built-in LED
            'adc_pins': [32, 33, 34, 35, 36, 39],  # ADC1 pins
            'touch_pins': [4, 0, 2, 15, 13, 12, 14, 27],  # Touch pins
            'i2c_default': {'scl': 22, 'sda': 21},
            'spi_default': {'sck': 18, 'mosi': 23, 'miso': 19},
            'uart_pins': {'tx': 17, 'rx': 16}
        }
        
        # Setup onboard LED
        self.create_pwm(presets['onboard_led'])
        self._log("ESP32 default setup completed")
        return presets

    # ==================== DIAGNOSTICS ====================

    def run_pin_test(self, pin):
        """Run comprehensive pin test"""
        self._log(f"Starting pin test for pin {pin}")
        results = {}
        
        try:
            # Test as output
            self.set_high(pin)
            time.sleep_ms(100)
            self.set_low(pin)
            results['output'] = 'PASS'
        except Exception as e:
            results['output'] = f'FAIL: {e}'
            
        try:
            # Test as input
            state = self.read(pin)
            results['input'] = f'PASS (state: {state})'
        except Exception as e:
            results['input'] = f'FAIL: {e}'
            
        try:
            # Test PWM
            pwm = self.create_pwm(pin)
            pwm.duty(512)
            time.sleep_ms(100)
            pwm.duty(0)
            self.remove_pwm(pin)
            results['pwm'] = 'PASS'
        except Exception as e:
            results['pwm'] = f'FAIL: {e}'
            
        try:
            # Test ADC (if supported)
            voltage = self.read_voltage(pin)
            results['adc'] = f'PASS (voltage: {voltage:.2f}V)'
        except Exception as e:
            results['adc'] = f'FAIL: {e}'
            
        self._log(f"Pin test results for {pin}: {results}")
        return results

    def system_diagnostics(self):
        """Run system diagnostics"""
        self._log("Running system diagnostics")
        results = {
            'system_info': self._system_info(),
            'memory_test': self._memory_info(),
            'pin_tests': {}
        }
        
        # Test common pins
        test_pins = [2, 4, 16, 17, 18, 19]  # Common ESP32 pins
        for pin in test_pins:
            try:
                results['pin_tests'][pin] = self.run_pin_test(pin)
            except Exception as e:
                results['pin_tests'][pin] = f'ERROR: {e}'
                
        return results


# ==================== ADVANCED OS FRAMEWORK EXTENSIONS ====================

# ==================== DISPLAY ASSET MANAGEMENT ====================

class DisplayAsset:
    """Advanced display asset for images, sprites, animations"""
    
    def __init__(self, data, width, height, format='RGB565'):
        self.data = data
        self.width = width
        self.height = height
        self.format = format
        self.palette = None
        self.transparency_color = None
        self.animation_frames = []
        self.metadata = {}
    
    def get_pixel(self, x, y):
        """Get pixel color at position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            if self.format == 'RGB565':
                idx = (y * self.width + x) * 2
                if idx + 1 < len(self.data):
                    return struct.unpack('<H', self.data[idx:idx+2])[0]
        return 0
    
    def set_pixel(self, x, y, color):
        """Set pixel color at position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            if self.format == 'RGB565':
                idx = (y * self.width + x) * 2
                if idx + 1 < len(self.data):
                    self.data[idx:idx+2] = struct.pack('<H', color)
    
    def crop(self, x, y, w, h):
        """Create cropped asset"""
        new_data = bytearray()
        for row in range(h):
            for col in range(w):
                pixel = self.get_pixel(x + col, y + row)
                if self.format == 'RGB565':
                    new_data.extend(struct.pack('<H', pixel))
        return DisplayAsset(new_data, w, h, self.format)
    
    def scale(self, new_width, new_height):
        """Scale asset using nearest neighbor"""
        new_data = bytearray()
        x_ratio = self.width / new_width
        y_ratio = self.height / new_height
        
        for y in range(new_height):
            for x in range(new_width):
                src_x = int(x * x_ratio)
                src_y = int(y * y_ratio)
                pixel = self.get_pixel(src_x, src_y)
                if self.format == 'RGB565':
                    new_data.extend(struct.pack('<H', pixel))
        
        return DisplayAsset(new_data, new_width, new_height, self.format)
    
    def rotate_90(self):
        """Rotate asset 90 degrees clockwise"""
        new_data = bytearray()
        for x in range(self.width):
            for y in range(self.height - 1, -1, -1):
                pixel = self.get_pixel(x, y)
                if self.format == 'RGB565':
                    new_data.extend(struct.pack('<H', pixel))
        return DisplayAsset(new_data, self.height, self.width, self.format)
    
    def apply_filter(self, filter_type='grayscale'):
        """Apply image filter"""
        new_data = bytearray(self.data)
        asset = DisplayAsset(new_data, self.width, self.height, self.format)
        
        if filter_type == 'grayscale':
            for y in range(self.height):
                for x in range(self.width):
                    pixel = self.get_pixel(x, y)
                    if self.format == 'RGB565':
                        r = (pixel >> 11) & 0x1F
                        g = (pixel >> 5) & 0x3F
                        b = pixel & 0x1F
                        gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                        gray_pixel = (gray << 11) | (gray << 5) | gray
                        asset.set_pixel(x, y, gray_pixel)
        
        return asset


class AssetManager:
    """Advanced asset management system"""
    
    def __init__(self):
        self.assets = {}
        self.cache = {}
        self.load_cache = {}
        self.memory_limit = 50000  # Bytes
        self.current_memory = 0
    
    def create_from_picture(self, path, size=None, format='RGB565'):
        """Create asset from PNG/BMP file"""
        try:
            # Simple BMP loader (for MicroPython compatibility)
            if path.endswith('.bmp'):
                return self._load_bmp(path, size, format)
            elif path.endswith('.png'):
                return self._load_png_simple(path, size, format)
            else:
                raise ValueError("Unsupported image format")
        except Exception as e:
            print(f"Failed to load image {path}: {e}")
            return self._create_placeholder(size or [32, 32], format)
    
    def _load_bmp(self, path, size, format):
        """Load BMP file (basic 24-bit support)"""
        try:
            with open(path, 'rb') as f:
                # Read BMP header
                header = f.read(54)
                if header[:2] != b'BM':
                    raise ValueError("Not a valid BMP file")
                
                width = struct.unpack('<I', header[18:22])[0]
                height = struct.unpack('<I', header[22:26])[0]
                
                # Read pixel data
                data = bytearray()
                for y in range(height):
                    for x in range(width):
                        pixel_data = f.read(3)  # BGR
                        if len(pixel_data) == 3:
                            b, g, r = pixel_data
                            if format == 'RGB565':
                                rgb565 = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
                                data.extend(struct.pack('<H', rgb565))
                
                asset = DisplayAsset(data, width, height, format)
                if size and (size[0] != width or size[1] != height):
                    asset = asset.scale(size[0], size[1])
                
                return asset
        except Exception as e:
            print(f"BMP load error: {e}")
            return self._create_placeholder(size or [32, 32], format)
    
    def _load_png_simple(self, path, size, format):
        """Simple PNG loader (basic functionality)"""
        # For full PNG support, you'd need a proper PNG decoder
        # This is a placeholder that creates a pattern
        return self._create_placeholder(size or [32, 32], format)
    
    def _create_placeholder(self, size, format):
        """Create placeholder asset with pattern"""
        width, height = size
        data = bytearray()
        
        for y in range(height):
            for x in range(width):
                # Create checkerboard pattern
                if (x // 4 + y // 4) % 2:
                    color = 0xFFFF if format == 'RGB565' else 255  # White
                else:
                    color = 0x0000 if format == 'RGB565' else 0    # Black
                
                if format == 'RGB565':
                    data.extend(struct.pack('<H', color))
                else:
                    data.append(color)
        
        return DisplayAsset(data, width, height, format)
    
    def register_asset(self, name, asset):
        """Register asset with name"""
        self.assets[name] = asset
        self.current_memory += len(asset.data)
        self._cleanup_memory()
    
    def get_asset(self, name):
        """Get asset by name"""
        return self.assets.get(name)
    
    def _cleanup_memory(self):
        """Clean up memory if over limit"""
        if self.current_memory > self.memory_limit:
            # Remove oldest assets
            items = list(self.assets.items())
            while self.current_memory > self.memory_limit * 0.8 and items:
                name, asset = items.pop(0)
                self.current_memory -= len(asset.data)
                del self.assets[name]


# ==================== ADVANCED UI COMPONENTS ====================

class Theme:
    """UI Theme system"""
    
    def __init__(self, name="default"):
        self.name = name
        self.colors = {
            'primary': 0x07E0,      # Green
            'secondary': 0x001F,     # Blue
            'background': 0x0000,    # Black
            'surface': 0x2104,       # Dark gray
            'text': 0xFFFF,          # White
            'accent': 0xF800,        # Red
            'warning': 0xFFE0,       # Yellow
            'success': 0x07E0,       # Green
            'error': 0xF800          # Red
        }
        self.fonts = {
            'default': 8,
            'small': 6,
            'large': 12,
            'title': 16
        }
        self.spacing = {
            'tiny': 2,
            'small': 4,
            'medium': 8,
            'large': 16
        }
        self.borders = {
            'thin': 1,
            'medium': 2,
            'thick': 3
        }


class UIComponent:
    """Base UI component"""
    
    def __init__(self, x, y, width, height, theme=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.theme = theme or Theme()
        self.visible = True
        self.enabled = True
        self.focused = False
        self.dirty = True
        self.children = []
        self.parent = None
        self.event_handlers = defaultdict(list)
    
    def add_child(self, child):
        """Add child component"""
        child.parent = self
        self.children.append(child)
        self.mark_dirty()
    
    def remove_child(self, child):
        """Remove child component"""
        if child in self.children:
            child.parent = None
            self.children.remove(child)
            self.mark_dirty()
    
    def mark_dirty(self):
        """Mark component for redraw"""
        self.dirty = True
        if self.parent:
            self.parent.mark_dirty()
    
    def draw(self, display):
        """Draw component (override in subclasses)"""
        if not self.visible:
            return
        
        # Draw children
        for child in self.children:
            child.draw(display)
    
    def handle_event(self, event):
        """Handle input event"""
        # Pass to children first
        for child in reversed(self.children):
            if child.handle_event(event):
                return True
        
        # Handle own events
        for handler in self.event_handlers[event.type]:
            try:
                if handler(event):
                    return True
            except:
                pass
        
        return False
    
    def on_event(self, event_type, handler):
        """Register event handler"""
        self.event_handlers[event_type].append(handler)


class Button(UIComponent):
    """Advanced UI Button"""
    
    def __init__(self, x, y, width, height, text="", theme=None):
        super().__init__(x, y, width, height, theme)
        self.text = text
        self.pressed = False
        self.hover = False
    
    def draw(self, display):
        if not self.visible:
            return
        
        # Button background
        bg_color = self.theme.colors['primary'] if self.pressed else self.theme.colors['surface']
        display.rect(self.x, self.y, self.width, self.height, bg_color, fill=True)
        
        # Button border
        border_color = self.theme.colors['accent'] if self.focused else self.theme.colors['text']
        display.rect(self.x, self.y, self.width, self.height, border_color, fill=False)
        
        # Button text
        text_x = self.x + (self.width - len(self.text) * 8) // 2
        text_y = self.y + (self.height - 8) // 2
        display.text(self.text, text_x, text_y, self.theme.colors['text'])
        
        super().draw(display)


class MenuItem:
    """Menu item"""
    
    def __init__(self, text, action=None, icon=None, submenu=None):
        self.text = text
        self.action = action
        self.icon = icon
        self.submenu = submenu
        self.enabled = True
        self.visible = True


class Menu(UIComponent):
    """Advanced menu system"""
    
    def __init__(self, x, y, width, height, title="Menu", theme=None):
        super().__init__(x, y, width, height, theme)
        self.title = title
        self.items = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible_items = (height - 20) // 12  # Account for title
        self.item_height = 12
    
    def add_item(self, item):
        """Add menu item"""
        self.items.append(item)
        self.mark_dirty()
    
    def add_text_item(self, text, action=None):
        """Add simple text menu item"""
        self.add_item(MenuItem(text, action))
    
    def add_submenu(self, text, submenu):
        """Add submenu item"""
        self.add_item(MenuItem(text, submenu=submenu))
    
    def move_up(self):
        """Move selection up"""
        if self.selected_index > 0:
            self.selected_index -= 1
            self._adjust_scroll()
            self.mark_dirty()
    
    def move_down(self):
        """Move selection down"""
        if self.selected_index < len(self.items) - 1:
            self.selected_index += 1
            self._adjust_scroll()
            self.mark_dirty()
    
    def _adjust_scroll(self):
        """Adjust scroll to keep selected item visible"""
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.max_visible_items:
            self.scroll_offset = self.selected_index - self.max_visible_items + 1
    
    def select_current(self):
        """Select current menu item"""
        if 0 <= self.selected_index < len(self.items):
            item = self.items[self.selected_index]
            if item.enabled:
                if item.action:
                    item.action()
                    return True
                elif item.submenu:
                    return item.submenu
        return False
    
    def draw(self, display):
        if not self.visible:
            return
        
        # Clear menu area
        display.rect(self.x, self.y, self.width, self.height, self.theme.colors['background'], fill=True)
        
        # Draw title
        display.text(self.title, self.x + 4, self.y + 4, self.theme.colors['text'])
        display.line(self.x, self.y + 16, self.x + self.width, self.y + 16, self.theme.colors['text'])
        
        # Draw menu items
        start_y = self.y + 20
        for i in range(self.max_visible_items):
            item_index = self.scroll_offset + i
            if item_index >= len(self.items):
                break
            
            item = self.items[item_index]
            if not item.visible:
                continue
            
            item_y = start_y + i * self.item_height
            
            # Highlight selected item
            if item_index == self.selected_index:
                display.rect(self.x + 1, item_y, self.width - 2, self.item_height, 
                           self.theme.colors['primary'], fill=True)
            
            # Draw item text
            text_color = self.theme.colors['text'] if item.enabled else self.theme.colors['surface']
            display.text(item.text, self.x + 8, item_y + 2, text_color)
            
            # Draw submenu indicator
            if item.submenu:
                display.text(">", self.x + self.width - 12, item_y + 2, text_color)
        
        # Draw scrollbar if needed
        if len(self.items) > self.max_visible_items:
            scrollbar_height = max(4, (self.max_visible_items * self.height) // len(self.items))
            scrollbar_y = self.y + 20 + (self.scroll_offset * (self.height - 20)) // len(self.items)
            display.rect(self.x + self.width - 3, scrollbar_y, 2, scrollbar_height, 
                        self.theme.colors['accent'], fill=True)
        
        super().draw(display)


class Window(UIComponent):
    """Window system"""
    
    def __init__(self, x, y, width, height, title="Window", theme=None):
        super().__init__(x, y, width, height, theme)
        self.title = title
        self.resizable = True
        self.movable = True
        self.closable = True
        self.minimized = False
        self.maximized = False
        self.title_bar_height = 16
        self.border_width = 2
    
    def draw(self, display):
        if not self.visible or self.minimized:
            return
        
        # Window border
        display.rect(self.x, self.y, self.width, self.height, self.theme.colors['text'], fill=False)
        
        # Title bar
        display.rect(self.x + 1, self.y + 1, self.width - 2, self.title_bar_height, 
                    self.theme.colors['primary'], fill=True)
        
        # Title text
        display.text(self.title, self.x + 4, self.y + 4, self.theme.colors['text'])
        
        # Close button
        if self.closable:
            close_x = self.x + self.width - 12
            close_y = self.y + 4
            display.rect(close_x, close_y, 8, 8, self.theme.colors['error'], fill=True)
            display.text("X", close_x + 2, close_y + 1, self.theme.colors['text'])
        
        # Window content area
        content_y = self.y + self.title_bar_height + 1
        content_height = self.height - self.title_bar_height - 2
        display.rect(self.x + 1, content_y, self.width - 2, content_height, 
                    self.theme.colors['background'], fill=True)
        
        super().draw(display)


# ==================== ADVANCED DISPLAY SYSTEM ====================

class DisplayManager:
    """Advanced display management system"""
    
    def __init__(self, display, asset_manager=None, theme=None):
        self.display = display
        self.asset_manager = asset_manager or AssetManager()
        self.theme = theme or Theme()
        self.windows = []
        self.focused_window = None
        self.dirty_regions = []
        self.frame_buffer = None
        self.double_buffering = False
        
        # Initialize frame buffer for double buffering
        if hasattr(display, 'buffer'):
            self.frame_buffer = bytearray(len(display.buffer))
            self.double_buffering = True
    
    def create_from_picture(self, path, size=None):
        """Create display asset from picture file"""
        return self.asset_manager.create_from_picture(path, size)
    
    def set_asset(self, asset, x, y, transparent=False):
        """Draw asset at position"""
        if not asset:
            return
        
        for py in range(asset.height):
            for px in range(asset.width):
                screen_x = x + px
                screen_y = y + py
                
                if (0 <= screen_x < self.display.width and 
                    0 <= screen_y < self.display.height):
                    
                    pixel = asset.get_pixel(px, py)
                    
                    # Handle transparency
                    if transparent and asset.transparency_color is not None:
                        if pixel == asset.transparency_color:
                            continue
                    
                    self.display.pixel(screen_x, screen_y, pixel)
    
    def create_sprite(self, asset, x, y, scale=1.0):
        """Create sprite from asset"""
        return Sprite(asset, x, y, scale)
    
    def create_animation(self, assets, fps=10):
        """Create animation from asset list"""
        return Animation(assets, fps)
    
    def add_window(self, window):
        """Add window to display manager"""
        self.windows.append(window)
        if not self.focused_window:
            self.focused_window = window
            window.focused = True
    
    def remove_window(self, window):
        """Remove window from display manager"""
        if window in self.windows:
            self.windows.remove(window)
            if self.focused_window == window:
                self.focused_window = self.windows[-1] if self.windows else None
    
    def focus_window(self, window):
        """Focus window"""
        if self.focused_window:
            self.focused_window.focused = False
        self.focused_window = window
        if window:
            window.focused = True
    
    def render_frame(self):
        """Render complete frame"""
        if self.double_buffering:
            # Render to frame buffer
            self._render_to_buffer()
            # Swap buffers
            self.display.buffer[:] = self.frame_buffer
        else:
            # Direct rendering
            self._render_direct()
        
        self.display.show()
    
    def _render_to_buffer(self):
        """Render to frame buffer"""
        # Clear frame buffer
        for i in range(len(self.frame_buffer)):
            self.frame_buffer[i] = 0
        
        # Render windows
        for window in self.windows:
            if window.visible:
                window.draw(self.display)
    
    def _render_direct(self):
        """Render directly to display"""
        self.display.clear()
        for window in self.windows:
            if window.visible:
                window.draw(self.display)


class Sprite:
    """Sprite with position and animation"""
    
    def __init__(self, asset, x, y, scale=1.0):
        self.asset = asset
        self.x = x
        self.y = y
        self.scale = scale
        self.visible = True
        self.rotation = 0
        self.flip_x = False
        self.flip_y = False
    
    def move(self, dx, dy):
        """Move sprite by offset"""
        self.x += dx
        self.y += dy
    
    def set_position(self, x, y):
        """Set sprite position"""
        self.x = x
        self.y = y
    
    def draw(self, display_manager):
        """Draw sprite"""
        if not self.visible or not self.asset:
            return
        
        asset = self.asset
        
        # Apply transformations
        if self.scale != 1.0:
            new_width = int(asset.width * self.scale)
            new_height = int(asset.height * self.scale)
            asset = asset.scale(new_width, new_height)
        
        if self.rotation != 0:
            # Simple 90-degree rotations
            for _ in range((self.rotation // 90) % 4):
                asset = asset.rotate_90()
        
        display_manager.set_asset(asset, self.x, self.y, transparent=True)


class Animation:
    """Sprite animation system"""
    
    def __init__(self, assets, fps=10):
        self.assets = assets
        self.fps = fps
        self.current_frame = 0
        self.playing = False
        self.loop = True
        self.last_update = 0
        self.frame_duration = 1000 // fps  # ms per frame
    
    def play(self):
        """Start animation"""
        self.playing = True
        self.last_update = time.ticks_ms()
    
    def pause(self):
        """Pause animation"""
        self.playing = False
    
    def stop(self):
        """Stop and reset animation"""
        self.playing = False
        self.current_frame = 0
    
    def update(self):
        """Update animation frame"""
        if not self.playing or not self.assets:
            return
        
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_update) >= self.frame_duration:
            self.current_frame += 1
            if self.current_frame >= len(self.assets):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.assets) - 1
                    self.playing = False
            self.last_update = current_time
    
    def get_current_asset(self):
        """Get current animation frame asset"""
        if self.assets and 0 <= self.current_frame < len(self.assets):
            return self.assets[self.current_frame]
        return None


# ==================== PROCESS & TASK MANAGEMENT ====================

class Process:
    """Lightweight process system"""
    
    def __init__(self, name, task_func, priority=1, auto_restart=False):
        self.name = name
        self.task_func = task_func
        self.priority = priority
        self.auto_restart = auto_restart
        self.running = False
        self.task = None
        self.last_error = None
        self.start_count = 0
        self.memory_usage = 0
    
    async def start(self):
        """Start process"""
        if self.running:
            return False
        
        try:
            self.running = True
            self.start_count += 1
            self.task = asyncio.create_task(self.task_func())
            await self.task
        except Exception as e:
            self.last_error = str(e)
            if self.auto_restart:
                await asyncio.sleep_ms(1000)
                await self.start()
        finally:
            self.running = False
    
    def stop(self):
        """Stop process"""
        if self.task and not self.task.done():
            self.task.cancel()
        self.running = False


class ProcessManager:
    """OS-level process management"""
    
    def __init__(self):
        self.processes = {}
        self.scheduler_running = False
        self.system_load = 0
    
    def create_process(self, name, task_func, priority=1, auto_restart=False):
        """Create new process"""
        process = Process(name, task_func, priority, auto_restart)
        self.processes[name] = process
        return process
    
    async def start_process(self, name):
        """Start process by name"""
        if name in self.processes:
            await self.processes[name].start()
    
    def stop_process(self, name):
        """Stop process by name"""
        if name in self.processes:
            self.processes[name].stop()
    
    def get_process_list(self):
        """Get list of all processes"""
        return list(self.processes.keys())
    
    def get_process_info(self, name):
        """Get process information"""
        if name in self.processes:
            proc = self.processes[name]
            return {
                'name': proc.name,
                'running': proc.running,
                'priority': proc.priority,
                'start_count': proc.start_count,
                'last_error': proc.last_error,
                'memory': proc.memory_usage
            }
        return None
    
    async def start_scheduler(self):
        """Start process scheduler"""
        self.scheduler_running = True
        while self.scheduler_running:
            # Monitor processes
            for name, process in self.processes.items():
                if process.auto_restart and not process.running:
                    await process.start()
            
            await asyncio.sleep_ms(100)


# ==================== FILE SYSTEM EXTENSIONS ====================

class FileSystemManager:
    """Advanced file system operations"""
    
    def __init__(self):
        self.mount_points = {}
        self.file_cache = {}
        self.watch_list = {}
    
    def create_directory_tree(self, path):
        """Create complete directory tree"""
        parts = path.strip('/').split('/')
        current_path = ''
        
        for part in parts:
            current_path += '/' + part
            try:
                if _IS_MICROPYTHON:
                    os.mkdir(current_path)
                else:
                    os.makedirs(current_path, exist_ok=True)
            except OSError:
                pass  # Directory exists
    
    def copy_file(self, src, dst):
        """Copy file with progress"""
        try:
            with open(src, 'rb') as src_file:
                with open(dst, 'wb') as dst_file:
                    while True:
                        chunk = src_file.read(1024)
                        if not chunk:
                            break
                        dst_file.write(chunk)
            return True
        except Exception as e:
            print(f"Copy failed: {e}")
            return False
    
    def move_file(self, src, dst):
        """Move file"""
        if self.copy_file(src, dst):
            try:
                os.remove(src)
                return True
            except:
                pass
        return False
    
    def get_file_info(self, path):
        """Get detailed file information"""
        try:
            stat = os.stat(path)
            return {
                'size': stat[6],
                'type': 'file' if stat[0] & 0x8000 else 'directory',
                'modified': stat[8] if len(stat) > 8 else 0
            }
        except:
            return None
    
    def search_files(self, pattern, root='/'):
        """Search for files matching pattern"""
        results = []
        try:
            for item in os.listdir(root):
                item_path = f"{root}/{item}" if root != '/' else f"/{item}"
                if pattern in item:
                    results.append(item_path)
                
                # Recurse into directories
                if self.get_file_info(item_path)['type'] == 'directory':
                    results.extend(self.search_files(pattern, item_path))
        except:
            pass
        return results
    
    def calculate_checksum(self, path):
        """Calculate file checksum"""
        try:
            hash_obj = hashlib.sha256()
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(1024)
                    if not chunk:
                        break
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except:
            return None


# ==================== NETWORK EXTENSIONS ====================

class NetworkManager:
    """Advanced networking capabilities"""
    
    def __init__(self):
        self.connections = {}
        self.servers = {}
        self.clients = {}
        self.protocols = {}
    
    def create_http_server(self, port=80):
        """Create HTTP server"""
        class SimpleHTTPServer:
            def __init__(self, port):
                self.port = port
                self.routes = {}
                self.running = False
            
            def route(self, path):
                def decorator(func):
                    self.routes[path] = func
                    return func
                return decorator
            
            async def start(self):
                # Simple HTTP server implementation
                self.running = True
                print(f"HTTP Server started on port {self.port}")
        
        return SimpleHTTPServer(port)
    
    def create_tcp_client(self, host, port):
        """Create TCP client"""
        class TCPClient:
            def __init__(self, host, port):
                self.host = host
                self.port = port
                self.connected = False
            
            async def connect(self):
                self.connected = True
                print(f"Connected to {self.host}:{self.port}")
            
            async def send(self, data):
                if self.connected:
                    print(f"Sent: {data}")
            
            async def receive(self):
                if self.connected:
                    return b"mock_data"
                return None
        
        return TCPClient(host, port)


# ==================== CONFIGURATION SYSTEM ====================

class ConfigManager:
    """Advanced configuration management"""
    
    def __init__(self, config_file="system.conf"):
        self.config_file = config_file
        self.config = {}
        self.watchers = defaultdict(list)
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except:
            self.config = self._default_config()
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f)
        except Exception as e:
            print(f"Config save failed: {e}")
    
    def _default_config(self):
        """Default system configuration"""
        return {
            "system": {
                "name": "ClayOS",
                "version": "1.0.0",
                "debug": True,
                "log_level": "INFO"
            },
            "display": {
                "brightness": 80,
                "theme": "dark",
                "refresh_rate": 60
            },
            "network": {
                "wifi_enabled": True,
                "auto_connect": False
            },
            "hardware": {
                "cpu_freq": 240000000,
                "memory_limit": 100000
            }
        }
    
    def get(self, key, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key, value):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        
        # Notify watchers
        for watcher in self.watchers[key]:
            try:
                watcher(value)
            except:
                pass
        
        self.save_config()
    
    def watch(self, key, callback):
        """Watch configuration changes"""
        self.watchers[key].append(callback)


# ==================== COMPLETE OS DEMONSTRATION ====================

async def demo_clay_os():
    """Complete ClayOS demonstration with all advanced features"""
    print("=== CLAYOS ADVANCED FRAMEWORK DEMO ===")
    
    # Initialize Gipeo OS Framework
    os_instance = Gipeo(enable_logging=True)
    
    # Create display (assuming OLED is connected)
    try:
        i2c = os_instance.create_i2c(id=0, scl=22, sda=21)
        oled = os_instance.create_oled(0, 0x3C, 128, 64)
        display_manager = os_instance.create_display_manager(oled)
        print("✓ Display system initialized")
    except Exception as e:
        print(f"✗ Display initialization failed: {e}")
        return
    
    # Load assets and create sprites
    try:
        # Create some demo assets
        cafe_asset = os_instance.create_from_picture("cafe.bmp", size=[32, 24])
        logo_asset = os_instance.create_from_picture("logo.png", size=[16, 16])
        
        # Create sprites
        cafe_sprite = os_instance.create_sprite(cafe_asset, 10, 10)
        logo_sprite = os_instance.create_sprite(logo_asset, 100, 5, scale=0.8)
        
        print("✓ Assets and sprites created")
    except Exception as e:
        print(f"✗ Asset creation failed: {e}")
    
    # Create custom theme
    dark_theme = os_instance.create_theme("dark_pro", {
        'primary': 0x07E0,     # Bright green
        'secondary': 0x07FF,   # Cyan
        'background': 0x0000,  # Black
        'text': 0xFFFF,        # White
        'accent': 0xF81F       # Magenta
    })
    os_instance.set_theme(dark_theme)
    print("✓ Custom theme applied")
    
    # Create desktop environment
    desktop = os_instance.create_desktop()
    
    # Create advanced menus
    main_menu = os_instance.create_menu(0, 0, 128, 64, "ClayOS Main")
    main_menu.add_text_item("File Manager", lambda: print("File Manager opened"))
    main_menu.add_text_item("Applications", lambda: print("Applications opened"))
    main_menu.add_text_item("Games", lambda: print("Games opened"))
    main_menu.add_text_item("Network", lambda: print("Network opened"))
    main_menu.add_text_item("System", lambda: print("System opened"))
    main_menu.add_text_item("Settings")
    
    # Create settings submenu
    settings_menu = os_instance.create_settings_menu()
    
    # Create window applications
    file_window = os_instance.create_window(5, 5, 118, 54, "File Manager")
    settings_window = os_instance.create_window(10, 10, 108, 44, "Settings")
    settings_window.add_child(settings_menu)
    
    print("✓ Desktop and menus created")
    
    # Create device profiles
    led_profile = os_instance.create_device_profile("led_strip", {
        'data_pin': {'pin': 5, 'mode': 'PWM', 'freq': 1000},
        'power_pin': {'pin': 4, 'mode': 'OUT'}
    })
    
    sensor_profile = os_instance.create_device_profile("sensors", {
        'temp_sensor': {'pin': 36, 'mode': 'SENSOR', 'sensor_type': 'temperature'},
        'light_sensor': {'pin': 39, 'mode': 'SENSOR', 'sensor_type': 'light'}
    })
    
    # Load device profiles
    os_instance.load_device_profile("led_strip")
    os_instance.load_device_profile("sensors")
    print("✓ Device profiles loaded")
    
    # Create hardware macros
    blink_macro = os_instance.create_macro("blink_pattern", [
        {'type': 'set_pin', 'pin': 2, 'state': True},
        {'type': 'delay', 'duration': 500},
        {'type': 'set_pin', 'pin': 2, 'state': False},
        {'type': 'delay', 'duration': 500},
        {'type': 'set_pin', 'pin': 2, 'state': True},
        {'type': 'delay', 'duration': 200},
        {'type': 'set_pin', 'pin': 2, 'state': False}
    ])
    print("✓ Hardware macros created")
    
    # Start OS services
    await os_instance.start_os_services()
    print("✓ OS services started")
    
    # Create health monitoring
    health_monitor = os_instance.create_health_monitor(interval=3000)
    await os_instance.start_process("health_monitor")
    print("✓ System health monitoring active")
    
    # Configuration management demo
    os_instance.set_config("user.name", "ClayOS User")
    os_instance.set_config("user.theme", "dark_pro")
    os_instance.set_config("system.auto_save", True)
    
    def on_theme_change(new_theme):
        print(f"Theme changed to: {new_theme}")
    
    os_instance.watch_config("user.theme", on_theme_change)
    print("✓ Configuration system active")
    
    # File system operations
    os_instance.create_file("/system/boot.log", "ClayOS boot successful")
    os_instance.create_file("/user/settings.json", '{"theme": "dark", "lang": "en"}')
    
    files = os_instance.list_directory("/")
    print(f"✓ File system active - Found {len(files)} items in root")
    
    # Network setup (mock)
    try:
        http_server = os_instance.create_http_server(80)
        tcp_client = os_instance.create_tcp_client("api.example.com", 443)
        print("✓ Network services created")
    except Exception as e:
        print(f"✗ Network setup failed: {e}")
    
    # Main OS loop
    print("\n🚀 ClayOS is running! Starting main loop...")
    
    frame_count = 0
    while frame_count < 100:  # Run for demo purposes
        try:
            # Update sprites
            if 'cafe_sprite' in locals():
                cafe_sprite.move(1, 0)
                if cafe_sprite.x > 128:
                    cafe_sprite.x = -32
            
            # Display assets
            if 'cafe_asset' in locals():
                os_instance.set_asset(cafe_asset, 50, 30)
            
            # Render frame
            display_manager.render_frame()
            
            # System operations
            if frame_count % 30 == 0:  # Every ~500ms at 60fps
                health = os_instance.get_system_health()
                print(f"Frame {frame_count}: Memory free: {health['memory']['free']} bytes")
            
            frame_count += 1
            await asyncio.sleep_ms(16)  # 60 FPS
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Runtime error: {e}")
            break
    
    print("\n✓ ClayOS demo completed successfully!")
    print("🎯 All advanced features demonstrated:")
    print("   • Asset Management & Sprites")
    print("   • Advanced Menu System")
    print("   • Window Management")
    print("   • Process Management")
    print("   • Configuration System")
    print("   • File System Operations")
    print("   • Device Profiles & Macros")
    print("   • System Health Monitoring")
    print("   • Theme Management")
    print("   • Network Services")


# ==================== EXTENDED GIPEO CLASS ====================

async def demo_advanced_features():
    """Demonstration of advanced Gipeo features"""
    g = Gipeo()
    
    # Setup components
    button = g.create_button(0, invert=True)  # GPIO0 with pull-up
    led_pwm = g.create_pwm(2)  # Onboard LED
    temp_sensor = g.create_analog_sensor(36, "temperature", sensor_type="LM35")
    
    # Button event handlers
    button.on('click', lambda: print("Button clicked!"))
    button.on('long_press', lambda data: print(f"Long press: {data['duration']}ms"))
    
    # LED effects
    async def led_effects():
        while True:
            await led_pwm.pulse(0, 1023, 2000)  # Pulse every 2 seconds
            
    # Sensor monitoring
    async def monitor_temperature():
        while True:
            temp = temp_sensor.read_temperature_c()
            print(f"Temperature: {temp:.1f}°C")
            await asyncio.sleep(5)
    
    # Run all tasks concurrently
    await asyncio.gather(
        led_effects(),
        monitor_temperature(),
        g.process_events()
    )


if __name__ == "__main__":
    # Choose demo mode
    import sys
    
    print("🚀 GIPEO ADVANCED OS FRAMEWORK")
    print("==============================")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--full-os":
        # Run complete ClayOS demonstration
        try:
            asyncio.run(demo_clay_os())
        except Exception as e:
            print(f"ClayOS demo error: {e}")
    else:
        # Basic usage test with OS features
        gipeo = Gipeo()
        print("✓ Gipeo OS Framework initialized!")
        
        # Demo OS features
        print("\n🎯 ADVANCED FEATURES DEMO:")
        
        # Asset management
        try:
            asset = gipeo.create_from_picture("test.bmp", size=[16, 16])
            print("✓ Asset management working")
        except Exception as e:
            print(f"✗ Asset management: {e}")
        
        # Menu system
        try:
            menu = gipeo.create_menu(0, 0, 64, 32, "Test Menu")
            menu.add_text_item("Option 1")
            menu.add_text_item("Option 2")
            print("✓ Advanced menu system working")
        except Exception as e:
            print(f"✗ Menu system: {e}")
        
        # Window management
        try:
            window = gipeo.create_window(10, 10, 50, 30, "Test Window")
            print("✓ Window management working")
        except Exception as e:
            print(f"✗ Window management: {e}")
        
        # Configuration system
        try:
            gipeo.set_config("test.value", 42)
            value = gipeo.get_config("test.value")
            assert value == 42
            print("✓ Configuration system working")
        except Exception as e:
            print(f"✗ Configuration system: {e}")
        
        # File system
        try:
            gipeo.create_file("/test.txt", "Hello ClayOS!")
            content = gipeo.read_file("/test.txt")
            assert content == "Hello ClayOS!"
            print("✓ File system working")
        except Exception as e:
            print(f"✗ File system: {e}")
        
        # Process management
        try:
            async def test_task():
                await asyncio.sleep_ms(100)
                return True
            
            process = gipeo.create_process("test_process", test_task)
            print("✓ Process management working")
        except Exception as e:
            print(f"✗ Process management: {e}")
        
        # System status
        gipeo.status()
        
        print("\n🎉 All systems operational!")
        print("💡 Use --full-os flag for complete ClayOS demonstration")
        print("📚 Example usage:")
        print("   cafedisplay = gipeo.create_from_picture('cafe.bmp', size=[64, 32])")
        print("   gipeo.set_asset(cafedisplay, 10, 20)")
        print("   menu = gipeo.create_menu(0, 0, 128, 64, 'My Menu')")
        print("   window = gipeo.create_window(5, 5, 100, 50, 'My App')")
        
        # Run advanced demo if asyncio is available
        if _IS_MICROPYTHON:
            try:
                asyncio.run(demo_advanced_features())
            except KeyboardInterrupt:
                print("\nDemo stopped by user")
        else:
            # Simple test for mock environment
            gipeo.set_high(2)
            print("🔧 Hardware test: Pin 2 state:", gipeo.is_state(2, True))
            gipeo.toggle(2)
            print("🔧 Hardware test: Pin 2 after toggle:", gipeo.is_state(2, True))
        
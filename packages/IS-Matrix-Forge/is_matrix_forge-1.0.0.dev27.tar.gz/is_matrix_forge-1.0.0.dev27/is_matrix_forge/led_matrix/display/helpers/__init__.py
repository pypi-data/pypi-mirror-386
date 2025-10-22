import time
import math
from is_matrix_forge.led_matrix.commands.map import CommandVals


def keep_image(
    controller,
    breathe: bool = False,
    breathe_fps: float = 30,
    interval: float = 0.1,
    time_between_refreshes: float = 50
):
    """
    Continuously hold the current image on-screen, optionally breathing the brightness.

    Args:
        controller: an LEDMatrixController-like object with:
            - .brightness (0-100)
            - .keep_image (bool flag you can set to False to exit)
            - .draw_grid(grid) or .render_current() to re-send the image
            - .set_brightness(value)
        breathe: if True, oscillate brightness in a sinusoidal “breathing” pattern
        breathe_fps: how many brightness steps per second when breathing
        interval: seconds between each brightness step (if breathing)
        time_between_refreshes: seconds to sleep after one full breath cycle
                                 (or between redraws if not breathing)
    """
    base_brightness = controller.brightness
    t = 0.0
    period = 1.0  # one full sine cycle = 1 second
    step = 1.0 / breathe_fps

    while controller.keep_image:
        if breathe:
            # Compute a smooth sine-based oscillation from 0→1→0
            phase = (t % period) / period            # 0.0→1.0
            fade = 0.5 * (1 - math.cos(2 * math.pi * phase))
            bri = int(round(base_brightness * fade))
            controller.set_brightness(bri)
            time.sleep(interval)
            t += interval
        else:
            # just hold at base brightness
            controller.set_brightness(base_brightness)
            time.sleep(time_between_refreshes)

        # re-draw the current image (whatever the controller is holding)
        # assume controller.draw_current() or similar:
        try:
            controller.render_current()
        except AttributeError:
            # fallback to a generic draw call
            controller.draw()


def light_leds(dev, leds):
    """Light a specific number of LEDs"""
    # Initialize a byte array with all LEDs off
    vals = [0x00 for _ in range(39)]

    # Calculate how many complete bytes we need to fill (each byte = 8 LEDs)
    complete_bytes = int(leds / 8)

    # Set all complete bytes to 0xFF (all 8 bits on)
    for byte in range(complete_bytes):
        vals[byte] = 0xFF

    # Handle the remaining LEDs (less than 8) in the last partial byte
    remaining_leds = leds % 8

    # For each remaining LED, set the corresponding bit in the last byte
    # This creates a binary pattern like 00011111 for 5 remaining LEDs
    for i in range(remaining_leds):
        vals[complete_bytes] += 1 << i

    # Send the command to the device to display the pattern
    send_command(dev, CommandVals.Draw, vals)


def render_matrix(dev, matrix):
    """Show a black/white matrix.

    Accepts matrices smaller than 9×34 and treats out-of-bounds pixels as
    "off" so that callers can render compact glyphs without padding.
    """
    # Initialize a byte array to hold the binary representation of the matrix
    # 39 bytes = 312 bits, which is enough for 9x34 = 306 pixels
    vals = [0x00 for _ in range(39)]

    # Determine provided matrix dimensions (column-major)
    width = len(matrix)
    height = len(matrix[0]) if width and isinstance(matrix[0], list) else 0

    # Iterate through each position in the 9x34 matrix
    for x in range(9):
        for y in range(34):
            # Convert 2D coordinates to a linear index
            # The matrix is stored in column-major order (y changes faster than x)
            i = x + 9 * y

            # Only read from matrix if within bounds and the pixel is on
            if (
                x < width
                and isinstance(matrix[x], list)
                and y < len(matrix[x])
                and matrix[x][y]
            ):
                # Calculate which byte in the vals array this pixel belongs to
                byte_index = int(i / 8)

                # Calculate which bit within that byte represents this pixel
                bit_position = i % 8

                # Set the corresponding bit in the appropriate byte
                # This efficiently packs 8 pixels into each byte
                vals[byte_index] = vals[byte_index] | (1 << bit_position)

    # Send the packed binary data to the device
    send_command(dev, CommandVals.Draw, vals)


from is_matrix_forge.led_matrix.hardware import (
    brightness,
    get_brightness,
    animate,
    get_animate,
    percentage, send_command,
)

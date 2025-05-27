import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons
from scipy.interpolate import interp1d
from sklearn.metrics import mean_squared_error

# Analog signal models

# Sine wave: x(t) = sin(2πft)
def sine_wave(t, f=5):
    return np.sin(2 * np.pi * f * t)

# Triangle wave: x(t) = 2 * |2*(ft - floor(ft + 0.5))| - 1
# This expression generates a unit-amplitude triangle wave with frequency f.
def triangle_wave(t, f=5):
    return 2 * np.abs(2 * (t * f - np.floor(t * f + 0.5))) - 1

# Exponentially decaying signal: x(t) = e^(-αt), where α is a positive decay constant.
def exponential_wave(t, decay=5):
    return np.exp(-decay * t)

# Dictionary of signal types
signal_types = {
    'Sine': sine_wave,
    'Triangle': triangle_wave,
    'Exponential': exponential_wave
}

# Sampling function: Sampling an analog signal
def sample_signal(signal_func, t_start, t_end, sampling_rate):
    # Sampling period: Ts = 1 / fs
    Ts = 1 / sampling_rate
    t_samples = np.arange(t_start, t_end, Ts)
    # x[n] = x(t) | t = nTs
    x_samples = signal_func(t_samples)
    return t_samples, x_samples, Ts

# ZOH: Zero-Order Hold Reconstruction
# Holds each x[n] value constant for Ts duration.
# Mathematically: x_zoh(t) = x[n]  ∀ t ∈ [nTs, (n+1)Ts)
def zoh_reconstruct(t_samples, x_samples, t_full):
    zoh = np.zeros_like(t_full)
    for i in range(len(t_samples) - 1):
        zoh[(t_full >= t_samples[i]) & (t_full < t_samples[i+1])] = x_samples[i]
    zoh[t_full >= t_samples[-1]] = x_samples[-1]  # Last sample is held for the remaining time
    return zoh

# FOH: First-Order Hold Reconstruction
# Performs linear interpolation between two consecutive samples.
# x_foh(t) = x[n] + ((x[n+1] - x[n]) / Ts) * (t - nTs)
def foh_reconstruct(t_samples, x_samples, t_full):
    foh_interp = interp1d(t_samples, x_samples, kind='linear', fill_value='extrapolate')
    return foh_interp(t_full)

# GUI Function: Interactive visualization
def interactive_gui(duration=1):
    init_freq = 5  # Initial frequency [Hz]
    init_fs = 10   # Initial sampling rate [Hz]
    init_signal = 'Sine'  # Default signal type

    # Continuous time vector (high resolution)
    t_cont = np.linspace(0, duration, 1000)

    # Update function (for GUI interaction)
    def update_plot(frequency, sampling_rate, signal_type):
        signal_func = signal_types[signal_type]
        x_cont = signal_func(t_cont, frequency)
        t_samples, x_samples, _ = sample_signal(lambda t: signal_func(t, frequency), 0, duration, sampling_rate)

        # Generate ZOH and FOH signals
        zoh = zoh_reconstruct(t_samples, x_samples, t_cont)
        foh = foh_reconstruct(t_samples, x_samples, t_cont)

        # Error calculation: MSE (Mean Squared Error)
        # MSE = (1/N) * Σ (x(t) - x_recon(t))^2
        zoh_mse = mean_squared_error(x_cont, zoh)
        foh_mse = mean_squared_error(x_cont, foh)

        return x_cont, t_samples, x_samples, zoh, foh, zoh_mse, foh_mse

    # Initial plot
    x_cont, t_samples, x_samples, zoh_rec, foh_rec, zoh_mse, foh_mse = update_plot(init_freq, init_fs, init_signal)

    # Plot layout: Two axes side by side (for ZOH and FOH)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    plt.subplots_adjust(left=0.3, bottom=0.3)

    # ZOH (Left)
    l_orig1, = ax1.plot(t_cont, x_cont, 'k--', label='Original Signal')   # Original continuous signal
    l_zoh, = ax1.plot(t_cont, zoh_rec, 'b', label='ZOH')                  # ZOH reconstruction
    l_samp1, = ax1.plot(t_samples, x_samples, 'ro', label='Samples')     # Sampled points

    # FOH (Right)
    l_orig2, = ax2.plot(t_cont, x_cont, 'k--', label='Original Signal')
    l_foh, = ax2.plot(t_cont, foh_rec, 'g', label='FOH')
    l_samp2, = ax2.plot(t_samples, x_samples, 'ro', label='Samples')

    # Titles and axis labels
    ax1.set_title(f'ZOH Reconstruction\nMSE: {zoh_mse:.4f}')
    ax2.set_title(f'FOH Reconstruction\nMSE: {foh_mse:.4f}')
    for ax in [ax1, ax2]:
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("Amplitude")
        ax.grid(True)
        ax.legend()

    # GUI components (Sliders and Radio Buttons)
    ax_fs = plt.axes([0.3, 0.2, 0.6, 0.03])   # Sampling rate slider
    ax_f = plt.axes([0.3, 0.15, 0.6, 0.03])   # Frequency slider
    ax_radio = plt.axes([0.025, 0.4, 0.2, 0.2])  # Signal type selection

    slider_fs = Slider(ax_fs, 'Sampling Rate (Hz)', 1, 50, valinit=init_fs, valstep=1)
    slider_f = Slider(ax_f, 'Signal Frequency (Hz)', 1, 20, valinit=init_freq, valstep=1)
    radio_signal = RadioButtons(ax_radio, ('Sine', 'Triangle', 'Exponential'))

    # Update function for sliders/radio
    def update(val):
        f = slider_f.val
        fs = slider_fs.val
        signal_type = radio_signal.value_selected
        x_cont, t_samples, x_samples, zoh, foh, mse_zoh, mse_foh = update_plot(f, fs, signal_type)

        # Update ZOH
        l_orig1.set_ydata(x_cont)
        l_zoh.set_ydata(zoh)
        l_samp1.set_xdata(t_samples)
        l_samp1.set_ydata(x_samples)
        ax1.set_title(f'ZOH Reconstruction\nMSE: {mse_zoh:.4f}')

        # Update FOH
        l_orig2.set_ydata(x_cont)
        l_foh.set_ydata(foh)
        l_samp2.set_xdata(t_samples)
        l_samp2.set_ydata(x_samples)
        ax2.set_title(f'FOH Reconstruction\nMSE: {mse_foh:.4f}')

        fig.canvas.draw_idle()

    # Bind events
    slider_fs.on_changed(update)
    slider_f.on_changed(update)
    radio_signal.on_clicked(update)

    plt.show()

# Run application
interactive_gui(duration=1)
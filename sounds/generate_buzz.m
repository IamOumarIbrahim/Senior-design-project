%% DMS Tier 2: Automotive Wake-Up Buzz (Fatigue / Drowsiness Alert)
% Triggers on: Yawning, rubbing eyes, hand over mouth
% Higher-pitch firm automotive warning buzz (350 Hz with rich harmonics & tactile vibration)

clear; clc;

Fs          = 48000;       % Sample rate (Hz)
dur         = 3.00;        % Standardized buzz duration (seconds)
f0          = 350.0;       % Higher base frequency (Hz, classic automotive alert range)
peak_dbfs   = -3.0;        % Peak normalization (dBFS)
n_channels  = 2;           % Stereo

N = round(dur * Fs);
t = (0 : N - 1)' / Fs;

% Rich harmonic spectrum (350 Hz, 700 Hz, 1050 Hz, 1400 Hz)
sig = 1.00 * sin(2*pi*f0*1*t) + ...
      0.60 * sin(2*pi*f0*2*t) + ...
      0.35 * sin(2*pi*f0*3*t) + ...
      0.18 * sin(2*pi*f0*4*t);

% Tactile 35 Hz amplitude vibration (dashboard/seat rumble sensation)
sig = sig .* (1.0 + 0.25 * sin(2*pi*35*t));

% 30ms raised-cosine fade-in
ramp_in_len = round(0.030 * Fs);
fade_in  = 0.5 * (1 - cos(pi * (0:ramp_in_len-1)' / ramp_in_len));
sig(1:ramp_in_len) = sig(1:ramp_in_len) .* fade_in;

% 0.25s raised-cosine fade-out
ramp_out_len = round(0.25 * Fs);
fade_out = 0.5 * (1 + cos(pi * (0:ramp_out_len-1)' / ramp_out_len));
sig(end-ramp_out_len+1:end) = sig(end-ramp_out_len+1:end) .* fade_out;

% Peak normalize and stereo export
sig = (sig / max(abs(sig))) * 10^(peak_dbfs / 20);
audio_stereo = repmat(sig, 1, n_channels);

audiowrite('fatigue_buzz.wav', audio_stereo, Fs, 'BitsPerSample', 16);
fprintf('Exported fatigue_buzz.wav (%.2fs, %d Hz, %d ch, Higher Pitch 350 Hz!)\n', ...
    size(audio_stereo,1)/Fs, Fs, n_channels);

%% DMS Tier 1: Triple Xylophone Gentle Chime (Distraction Alert)
% Triggers on: Phone use, talking, drinking, smoking
% Non-startling, pleasant, courteous 3-note ascending triad (C6 -> E6 -> G6)

clear; clc;

Fs          = 48000;       % Sample rate (Hz)
notes       = [1046.5, 1318.5, 1568.0];  % C6 -> E6 -> G6 ascending major triad (Hz)
gap_sec     = 0.10;        % 100ms interval between strikes
total_dur   = 1.50;        % Standardized duration (seconds)
peak_dbfs   = -3.0;        % Peak normalization (dBFS)
n_channels  = 2;           % Stereo

n_notes     = numel(notes);
total_samples = round(total_dur * Fs);
audio       = zeros(total_samples, 1);

% Xylophone acoustic model function (fundamental + tuned 3x overtone + clang)
synth_bar = @(f0, dur) ...
    (sin(2*pi*f0*(0:round(dur*Fs)-1)'/Fs) .* exp(-(0:round(dur*Fs)-1)'/(0.35*Fs)) + ...
     0.38 * sin(2*pi*3*f0*(0:round(dur*Fs)-1)'/Fs) .* exp(-(0:round(dur*Fs)-1)'/(0.10*Fs)) + ...
     0.15 * sin(2*pi*9.2*f0*(0:round(dur*Fs)-1)'/Fs) .* exp(-(0:round(dur*Fs)-1)'/(0.012*Fs)) + ...
     0.10 * sin(2*pi*0.5*f0*(0:round(dur*Fs)-1)'/Fs) .* exp(-(0:round(dur*Fs)-1)'/(0.020*Fs)));

att = round(0.0015 * Fs);
ramp = linspace(0, 1, att)';

for i = 1:n_notes
    rem_dur = total_dur - (i - 1) * gap_sec;
    b = synth_bar(notes(i), rem_dur);
    b(1:att) = b(1:att) .* ramp;  % 1.5ms attack to avoid clicks
    idx = round((i - 1) * gap_sec * Fs) + 1;
    audio(idx : idx + numel(b) - 1) = audio(idx : idx + numel(b) - 1) + b;
end

% Smooth 0.25s tail fade
fo = round(0.25 * Fs);
fade_out = 0.5 * (1 + cos(pi * (0:fo-1)' / fo));
audio(end-fo+1:end) = audio(end-fo+1:end) .* fade_out;

% Peak normalize and stereo export
audio = (audio / max(abs(audio))) * 10^(peak_dbfs / 20);
audio_stereo = repmat(audio, 1, n_channels);

audiowrite('distraction_chime.wav', audio_stereo, Fs, 'BitsPerSample', 16);
fprintf('Exported distraction_chime.wav (%.2fs, %d Hz, %d ch, Triple Xylophone!)\n', ...
    size(audio_stereo,1)/Fs, Fs, n_channels);

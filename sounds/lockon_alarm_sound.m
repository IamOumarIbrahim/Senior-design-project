clear; clc;

%% 1. Configurable Parameters
Fs                  = 48000;         % Sample rate (Hz)
total_dur           = 10.0;          % Total alarm duration (seconds) - adjust as needed
trans_dur           = 0.50;          % Transition period between phases (seconds)
n_channels          = 2;             % Stereo output
peak_dbfs           = -3.0;          % Peak normalization (dBFS)

% 5 Phases Definition (GTA Lock-On Acceleration Model)
% Pitch: starts at 1000 Hz, caps at 2000 Hz (Phase 4 and 5)
% Pulse Rate: 2.5 Hz -> 6.0 Hz -> 14.0 Hz -> 28.0 Hz -> Solid Tone
% Pulse On-Time: 75ms -> 65ms -> 50ms -> 25ms (silence shrinks until fusing into solid tone)
% Phase 5: 100% constant solid tone (no pulse)
phase_pitches       = [1000,  1300,  1650,  2000,  2000];   % Tone pitch in Hz
phase_pulse_rates   = [2.5,   6.0,   14.0,  28.0,  28.0];   % Pulse rate in Hz
phase_on_times      = [0.075, 0.065, 0.050, 0.025, 0.035];  % Beep pulse duration in seconds
phase_solid         = [0.0,   0.0,   0.0,   0.0,   1.0];    % Phase 5 is 1.0 (constant solid tone)

n_phases            = numel(phase_pitches);
phase_dur           = total_dur / n_phases;                 % Base duration per phase (2.0s each)

%% 2. Time Base & Smooth Transition Curves (S-Curves)
N_total     = round(total_dur * Fs);
t           = (0 : N_total - 1)' / Fs;

f_pitch     = zeros(N_total, 1);
f_rate      = zeros(N_total, 1);
t_on_curve  = zeros(N_total, 1);
solid_curve = zeros(N_total, 1);

% Fill steady-state plateaus
for i = 1:n_phases
    if i == 1
        mask = (t <= phase_dur - trans_dur / 2.0);
        f_pitch(mask)     = phase_pitches(1);
        f_rate(mask)      = phase_pulse_rates(1);
        t_on_curve(mask)  = phase_on_times(1);
        solid_curve(mask) = phase_solid(1);
    elseif i == n_phases
        mask = (t >= (n_phases - 1) * phase_dur + trans_dur / 2.0);
        f_pitch(mask)     = phase_pitches(end);
        f_rate(mask)      = phase_pulse_rates(end);
        t_on_curve(mask)  = phase_on_times(end);
        solid_curve(mask) = phase_solid(end);
    else
        mask = (t >= (i - 1) * phase_dur + trans_dur / 2.0) & ...
               (t <= i * phase_dur - trans_dur / 2.0);
        f_pitch(mask)     = phase_pitches(i);
        f_rate(mask)      = phase_pulse_rates(i);
        t_on_curve(mask)  = phase_on_times(i);
        solid_curve(mask) = phase_solid(i);
    end
end

% Apply raised-cosine (S-curve) smooth transitions across boundaries
for k = 1:(n_phases - 1)
    b       = k * phase_dur;
    t_start = b - trans_dur / 2.0;
    t_end   = b + trans_dur / 2.0;
    mask    = (t >= t_start) & (t < t_end);
    s       = 0.5 * (1.0 - cos(pi * (t(mask) - t_start) / trans_dur));
    f_pitch(mask)     = (1.0 - s) * phase_pitches(k) + s * phase_pitches(k + 1);
    f_rate(mask)      = (1.0 - s) * phase_pulse_rates(k) + s * phase_pulse_rates(k + 1);
    t_on_curve(mask)  = (1.0 - s) * phase_on_times(k) + s * phase_on_times(k + 1);
    solid_curve(mask) = (1.0 - s) * phase_solid(k) + s * phase_solid(k + 1);
end

%% 3. Continuous Synthesis
% Phase accumulation for carrier guarantees zero clicks and pure sine glide
phase_carrier = 2 * pi * cumsum(f_pitch) / Fs;
carrier       = sin(phase_carrier);

% Phase accumulation for pulse gate: pulse duty tightens and gaps shrink
phase_gate    = cumsum(f_rate) / Fs;
cycle_pos     = mod(phase_gate, 1.0);
on_ratio      = min(0.95, max(0.05, t_on_curve .* f_rate));

raw_gate        = double(cycle_pos < on_ratio);
gate_with_solid = (1.0 - solid_curve) .* raw_gate + solid_curve .* 1.0;

% Anti-click edge smoothing (1.5 ms Hann moving average)
L             = max(1, round(0.0015 * Fs));
smooth_gate   = filter(ones(1, L) / L, 1, gate_with_solid);

audio         = carrier .* smooth_gate;

%% 4. Post-Processing & Export
% Tail fade (10 ms)
fo = round(0.010 * Fs);
audio(end-fo+1:end) = audio(end-fo+1:end) .* linspace(1, 0, fo)';

% Peak normalization
peak_val = max(abs(audio));
if peak_val > 0
    audio = (audio / peak_val) * 10^(peak_dbfs / 20);
end

% Convert to stereo
audio_stereo = repmat(audio, 1, n_channels);

% Export single target WAV file
output_wav = 'lockon_alarm_sound.wav';
audiowrite(output_wav, audio_stereo, Fs, 'BitsPerSample', 16);

fprintf('=================================================================\n');
fprintf('Exported: %s (%.2f s, %d Hz, %d ch, %.1f dBFS)\n', ...
    output_wav, size(audio_stereo, 1)/Fs, Fs, n_channels, peak_dbfs);
fprintf('Transition Window: %.2f s smooth S-curve between phases\n', trans_dur);
fprintf('5 Phases Summary (%.1fs each):\n', phase_dur);
fprintf('  Phase 1: Pitch = %4d Hz | Rate = %4.1f Hz (Beep: 75ms, Gap: 325ms)\n', phase_pitches(1), phase_pulse_rates(1));
fprintf('  Phase 2: Pitch = %4d Hz | Rate = %4.1f Hz (Beep: 65ms, Gap: 102ms)\n', phase_pitches(2), phase_pulse_rates(2));
fprintf('  Phase 3: Pitch = %4d Hz | Rate = %4.1f Hz (Beep: 50ms, Gap:  21ms)\n', phase_pitches(3), phase_pulse_rates(3));
fprintf('  Phase 4: Pitch = %4d Hz | Rate = %4.1f Hz (Beep: 25ms, Gap:  11ms)\n', phase_pitches(4), phase_pulse_rates(4));
fprintf('  Phase 5: Pitch = %4d Hz | CONSTANT Solid Tone (Gap: 0ms, NO pulse)\n', phase_pitches(5));
fprintf('=================================================================\n');
import { spawnSync } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const SCRIPT_DIRECTORY = path.dirname(fileURLToPath(import.meta.url));
const REPOSITORY_DIRECTORY = path.resolve(SCRIPT_DIRECTORY, '../../..');
const AUDIO_DIRECTORY = path.resolve(SCRIPT_DIRECTORY, '../assets/audio');
const MUSIC_SOURCE = path.join(REPOSITORY_DIRECTORY, 'video uchun music', 'momotmusic-technology-ambient-201091.mp3');
const MUSIC_OUTPUT = path.join(AUDIO_DIRECTORY, 'music-30s-v2.m4a');
const IMPACT_OUTPUT = path.join(AUDIO_DIRECTORY, 'hook-impact.wav');
const WHOOSH_OUTPUT = path.join(AUDIO_DIRECTORY, 'hook-whoosh.wav');
const CAPCUT_DIRECTORY = process.env.LOCALAPPDATA
  ? path.join(process.env.LOCALAPPDATA, 'CapCut', 'Apps', '9.8.0.4213')
  : null;
const FFMPEG = process.env.FFMPEG || (CAPCUT_DIRECTORY ? path.join(CAPCUT_DIRECTORY, 'ffmpeg.exe') : 'ffmpeg');
const FFPROBE = process.env.FFPROBE || (CAPCUT_DIRECTORY ? path.join(CAPCUT_DIRECTORY, 'ffprobe.exe') : 'ffprobe');

const SAMPLE_RATE = 48_000;
const CHANNELS = 2;
const PCM_BITS = 16;
const PCM_BYTES = PCM_BITS / 8;
const WAV_HEADER_BYTES = 44;
const PCM_MAX = 2 ** (PCM_BITS - 1) - 1;
const MUSIC_START_SECONDS = 77.880;
const MUSIC_DURATION_SECONDS = 30;
const MUSIC_FADE_OUT_SECONDS = 2;
const MUSIC_BITRATE = '192k';
const TARGET_LUFS = -14;
const TARGET_TRUE_PEAK_DBTP = -1.5;
// AAC encoding can raise the measured true peak; lower the finished PCM before encoding.
const ENCODE_HEADROOM_DB = 0.3;
const TARGET_LRA = 11;
const LIMITER_LINEAR_CEILING = 0.6;
const COMMAND_BUFFER_BYTES = 32 * 1024 * 1024;

const IMPACT_DURATION_SECONDS = 1;
const IMPACT_START_HZ = 60;
const IMPACT_END_HZ = 45;
const IMPACT_PITCH_DROP_SECONDS = 0.09;
const IMPACT_DECAY_SECONDS = 0.22;
const IMPACT_ATTACK_SECONDS = 0.001;
const IMPACT_TRANSIENT_SECONDS = 0.03;
const IMPACT_NOISE_DECAY_SECONDS = 0.008;
const IMPACT_NOISE_GAIN = 0.75;
const IMPACT_PEAK_DBFS = -3;

const WHOOSH_DURATION_SECONDS = 0.35;
const WHOOSH_RISE_SECONDS = 0.30;
const WHOOSH_START_HZ = 300;
const WHOOSH_END_HZ = 6_000;
const WHOOSH_RAMP_EXPONENT = 3;
const WHOOSH_FILTER_Q = Math.SQRT1_2;
const WHOOSH_PEAK_DBFS = -6;
const NOISE_SEED = 0x4a3b2c1d;
const TWO_PI = 2 * Math.PI;

function run(binary, args) {
  console.log(`> ${[binary, ...args].map((arg) => JSON.stringify(arg)).join(' ')}`);
  const result = spawnSync(binary, args, { encoding: 'utf8', maxBuffer: COMMAND_BUFFER_BYTES });
  if (result.error) throw new Error(`${binary}: ${result.error.message}`);
  if (result.status !== 0) throw new Error(`${binary} exited ${result.status}:\n${result.stderr}`);
  return result;
}

function loudnormFilter(measurements) {
  const filters = [
    `atrim=start=0:duration=${MUSIC_DURATION_SECONDS}`,
    'asetpts=PTS-STARTPTS',
    `afade=t=out:st=${MUSIC_DURATION_SECONDS - MUSIC_FADE_OUT_SECONDS}:d=${MUSIC_FADE_OUT_SECONDS}`,
  ];
  const target = `I=${TARGET_LUFS}:TP=${TARGET_TRUE_PEAK_DBTP}:LRA=${TARGET_LRA}`;
  const measured = measurements
    ? `:measured_I=${measurements.input_i}:measured_TP=${measurements.input_tp}:measured_LRA=${measurements.input_lra}:measured_thresh=${measurements.input_thresh}:offset=${measurements.target_offset}:linear=true`
    : '';
  filters.push(`loudnorm=${target}${measured}:print_format=json`);
  if (measurements) {
    filters.push(
      `aresample=${SAMPLE_RATE}`,
      `alimiter=limit=${LIMITER_LINEAR_CEILING}:level=false:latency=true`,
      `volume=-${ENCODE_HEADROOM_DB}dB`,
      `apad=pad_dur=${MUSIC_DURATION_SECONDS}`,
      `atrim=duration=${MUSIC_DURATION_SECONDS}`,
    );
  }
  return filters.join(',');
}

function parseLoudnorm(stderr) {
  const match = stderr.match(/\{\s*"input_i"[\s\S]*?\}/);
  if (!match) throw new Error(`Missing loudnorm measurements:\n${stderr.slice(-3000)}`);
  return JSON.parse(match[0]);
}

function makeMusic() {
  const probe = run(FFPROBE, ['-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', MUSIC_SOURCE]);
  const sourceDuration = Number(probe.stdout.trim());
  if (!Number.isFinite(sourceDuration) || sourceDuration < MUSIC_START_SECONDS + MUSIC_DURATION_SECONDS) {
    throw new Error(`Music source is too short or cannot be probed: ${probe.stdout.trim()}`);
  }
  const inputArgs = ['-hide_banner', '-nostats', '-ss', MUSIC_START_SECONDS.toFixed(3), '-i', MUSIC_SOURCE];
  const firstPass = run(FFMPEG, [...inputArgs, '-af', loudnormFilter(), '-f', 'null', '-']);
  const measurements = parseLoudnorm(firstPass.stderr);
  run(FFMPEG, [
    '-y', ...inputArgs, '-af', loudnormFilter(measurements),
    '-c:a', 'aac', '-b:a', MUSIC_BITRATE, '-ar', String(SAMPLE_RATE), '-ac', String(CHANNELS),
    '-t', String(MUSIC_DURATION_SECONDS), MUSIC_OUTPUT,
  ]);
}

function makeNoise(seed) {
  let state = seed >>> 0;
  return () => {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return (state >>> 0) / 0x80000000 - 1;
  };
}

function makeImpact() {
  const sampleCount = Math.round(IMPACT_DURATION_SECONDS * SAMPLE_RATE);
  const samples = new Float64Array(sampleCount * CHANNELS);
  const noise = makeNoise(NOISE_SEED);
  for (let index = 0; index < sampleCount; index++) {
    const time = index / SAMPLE_RATE;
    const phaseCycles = IMPACT_END_HZ * time
      + (IMPACT_START_HZ - IMPACT_END_HZ) * IMPACT_PITCH_DROP_SECONDS
      * (1 - Math.exp(-time / IMPACT_PITCH_DROP_SECONDS));
    const tone = Math.sin(TWO_PI * phaseCycles)
      * (1 - Math.exp(-time / IMPACT_ATTACK_SECONDS))
      * Math.exp(-time / IMPACT_DECAY_SECONDS);
    const noiseEnvelope = time < IMPACT_TRANSIENT_SECONDS
      ? IMPACT_NOISE_GAIN * Math.exp(-time / IMPACT_NOISE_DECAY_SECONDS)
      : 0;
    for (let channel = 0; channel < CHANNELS; channel++) {
      samples[index * CHANNELS + channel] = tone + noise() * noiseEnvelope;
    }
  }
  return samples;
}

function makeHighpass() {
  let x1 = 0;
  let x2 = 0;
  let y1 = 0;
  let y2 = 0;
  return (input, cutoffHz) => {
    const omega = TWO_PI * cutoffHz / SAMPLE_RATE;
    const cosine = Math.cos(omega);
    const alpha = Math.sin(omega) / (2 * WHOOSH_FILTER_Q);
    const a0 = 1 + alpha;
    const b0 = (1 + cosine) / (2 * a0);
    const b1 = -(1 + cosine) / a0;
    const b2 = b0;
    const a1 = -2 * cosine / a0;
    const a2 = (1 - alpha) / a0;
    const output = b0 * input + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2;
    x2 = x1;
    x1 = input;
    y2 = y1;
    y1 = output;
    return output;
  };
}

function makeWhoosh() {
  const sampleCount = Math.round(WHOOSH_DURATION_SECONDS * SAMPLE_RATE);
  const samples = new Float64Array(sampleCount * CHANNELS);
  const noise = makeNoise(NOISE_SEED);
  const filters = Array.from({ length: CHANNELS }, makeHighpass);
  for (let index = 0; index < sampleCount; index++) {
    const time = index / SAMPLE_RATE;
    const progress = Math.min(time / WHOOSH_RISE_SECONDS, 1);
    const cutoff = WHOOSH_START_HZ * (WHOOSH_END_HZ / WHOOSH_START_HZ) ** progress;
    const rise = progress ** WHOOSH_RAMP_EXPONENT;
    const release = time > WHOOSH_RISE_SECONDS
      ? (WHOOSH_DURATION_SECONDS - time) / (WHOOSH_DURATION_SECONDS - WHOOSH_RISE_SECONDS)
      : 1;
    for (let channel = 0; channel < CHANNELS; channel++) {
      samples[index * CHANNELS + channel] = filters[channel](noise(), cutoff) * rise * release;
    }
  }
  return samples;
}

function encodeWav(samples, targetPeakDbfs) {
  const peak = samples.reduce((maximum, sample) => Math.max(maximum, Math.abs(sample)), 0);
  if (peak === 0) throw new Error('Synthesized audio is silent');
  const gain = 10 ** (targetPeakDbfs / 20) / peak;
  const dataBytes = samples.length * PCM_BYTES;
  const wav = Buffer.alloc(WAV_HEADER_BYTES + dataBytes);
  wav.write('RIFF', 0);
  wav.writeUInt32LE(wav.length - 8, 4);
  wav.write('WAVE', 8);
  wav.write('fmt ', 12);
  wav.writeUInt32LE(16, 16);
  wav.writeUInt16LE(1, 20);
  wav.writeUInt16LE(CHANNELS, 22);
  wav.writeUInt32LE(SAMPLE_RATE, 24);
  wav.writeUInt32LE(SAMPLE_RATE * CHANNELS * PCM_BYTES, 28);
  wav.writeUInt16LE(CHANNELS * PCM_BYTES, 32);
  wav.writeUInt16LE(PCM_BITS, 34);
  wav.write('data', 36);
  wav.writeUInt32LE(dataBytes, 40);
  for (let index = 0; index < samples.length; index++) {
    wav.writeInt16LE(Math.round(samples[index] * gain * PCM_MAX), WAV_HEADER_BYTES + index * PCM_BYTES);
  }
  return wav;
}

async function main() {
  await mkdir(AUDIO_DIRECTORY, { recursive: true });
  makeMusic();
  await writeFile(IMPACT_OUTPUT, encodeWav(makeImpact(), IMPACT_PEAK_DBFS));
  console.log(`Wrote ${IMPACT_OUTPUT}`);
  await writeFile(WHOOSH_OUTPUT, encodeWav(makeWhoosh(), WHOOSH_PEAK_DBFS));
  console.log(`Wrote ${WHOOSH_OUTPUT}`);
}

try {
  await main();
} catch (error) {
  console.error(error);
  process.exitCode = 1;
}

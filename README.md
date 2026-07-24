# Neon Player Plugins 

A curated list of awesome plugins for [Neon Player](https://docs.pupil-labs.com/neon/neon-player/) by [Pupil Labs](https://pupil-labs.com/) and the community.

Neon Player allows you to extend its functionality using Python plugins. This repository serves as a central hub to discover, share, and collaborate on these plugins.

> [!TIP]
> Check out how to [install them](https://docs.pupil-labs.com/neon/neon-player/plugin-api/) or [create them](https://docs.pupil-labs.com/neon/neon-player/develop-your-own-plugin/).


- [Neon Player Repo & API](https://github.com/pupil-labs/neon-player-beta?tab=readme-ov-file)

> [!WARNING]
> Each individual plugin listed or hosted in this repository may be subject to its own individual license, as specified by its author in the plugin's source code, documentation, or the `README.md` table. The plugins are given as-is, and Pupil Labs is not responsible for their functionality or support. 

## Contents

- [Video & External Cameras](#video--external-cameras)
  - [external_camera.py](#external_camerapy)
  - [external_camera_manual_sync.py](#external_camera_manual_syncpy)
- [Audio Processing](#audio-processing)
  - [transcribe.py](#transcribepy)
- [Data Integrations & Biometrics](#data-integrations--biometrics)
  - [gps.py](#gpspy)
- [Cloud & Synchronization](#cloud--synchronization)
  - [cloud_events.py](#cloud_eventspy)

---
- [Contributing](#contributing)
- [Code of Conduct](#code-of-conduct)
- [License](#license)

## Video & External Cameras

### [external_camera.py](./external_camera.py)

| Screenshot | Brief description / Comments | Author | Date/Version last tested | Link (if external) | License |
|--- |-------:	|--------------------------------------: |--------:	|--------------------:	|--- |
| ![external camera plugin screenshot](./assets/external_camera.webp)	| External camera plugin. Loads an external camera video and presents it in sync with the scene. | [@pupil-labs](https://github.com/pupil-labs) | 6.0.13 (24/07/26) | - | MIT |

**Detailed Description:**

Requires a `.mov` format video with `.time` file that includes timestamps for each frame. Shows the external view in a Picture-in-Picture (PiP) window that can be resized, rotated, moved around, or changed in transparency. Also adds frame scrubbing capabilities, accessible with shortcuts (`Shift + H` / `Shift + L`) and the posibility to dock it to the main window to see it side-by-side with the scene camera.

**Notes:**
We will publish a tutorial on how to generate the `.time` file while recording. For now, you can use the [external_camera_manual_sync.py](./external_camera_manual_sync.py) plugin to manually sync your external camera video and generate the `.time` file.

### [external_camera_manual_sync.py](./external_camera_manual_sync.py)

| Screenshot | Brief description / Comments | Author | Date/Version last tested | Link (if external) | License |
|--- |-------:	|--------------------------------------: |--------:	|--------------------:    |--- |
| ![external camera manual sync plugin screenshot](./assets/external_camera_manual_sync.webp)    | External camera manual sync plugin. Loads an external camera video (.mp4) and presents a slider to manually sync frames. | [@pupil-labs](https://github.com/pupil-labs) | 6.0.13 (24/07/26) | - | MIT |

**Detailed Description:**

Designed for external cameras like GoPros that have been recorded with out syncing. Use the slider to match the external frame with the scene camera. Once matched, press "Generate .time" to create a compatible synced format that can be seamlessly used with the `external_camera.py` plugin.

## Audio Processing

### [transcribe.py](./transcribe.py)

| Screenshot | Brief description / Comments | Author | Date/Version last tested | Link (if external) | License |
|--- |-------:	|--------------------------------------: |--------:	|--------------------:	|--- |
| ![transcribe plugin screenshot](./assets/transcribe.webp) | Audio Transcription & Subtitles plugin. Leverages Whisper and pyannote.audio for speech recognition and speaker diarization. | [@pupil-labs](https://github.com/pupil-labs) | 6.0.13 (24/07/26) | - | MIT |

**Detailed Description:**

This plugin also allows event creation on word boundaries (similar to the [Audio Event Annotations](https://docs.pupil-labs.com/alpha-lab/audio-event-annotations/)) but operates fully locally on your machine and directly within Neon Player. It uses Whisper for speech recognition and pyannote.audio for speaker diarization, enabling you to transcribe audio and identify different speakers in your recordings. The plugin generates a subtitle file that can be used for video playback or further analysis.

## Data Integrations & Biometrics

### [gps.py](./gps.py)

| Screenshot | Brief description / Comments | Author | Date/Version last tested | Link (if external) | License |
|--- |-------:	|--------------------------------------: |--------:	|--------------------:	|--- |
| ![gps plugin screenshot](./assets/gps.webp)	| GPS tracking and visualization plugin. Loads GPS data from Garmin/Polar devices or the Comapanion Device. | [@pupil-labs](https://github.com/pupil-labs) | 6.0.13 (24/07/26) | - | MIT |

**Detailed Description:**

Simply drop it in the recording folder. If you used our [gps-alpha-lab tool](https://docs.pupil-labs.com/alpha-lab/), no need for offset. For 3rd party such as Garmin or Polar, an added time offset bar is available. Features a map visualization with the path taken, events as landmarks on the map, and a minimap with different styles. It also features GPS Kinematics (speed and acceleration) graphs, and if loaded from Garmin, also Heart Rate (HR) and Elevation graphs.

## Cloud & Synchronization

### [cloud_events.py](./cloud_events.py)

| Screenshot | Brief description / Comments | Author | Date/Version last tested | Link (if external) | License |
|--- |-------:	|--------------------------------------: |--------:	|--------------------:	|--- |
| ![cloud-events plugin screenshot](./assets/cloud_events.webp)	| Cloud events plugin, allows to pull, push and compare events. | [@pupil-labs](https://github.com/pupil-labs) | 6.0.13 (24/07/26) | - | MIT |

**Detailed Description:**

Easily synchronize and manage your events with the cloud, enabling seamless pushing, pulling, and comparison of event data directly within the player.

## Contributing

Contributions are very welcome! Please read the [contribution guidelines](CONTRIBUTING.md) before submitting a pull request.

## License

This repository's documentation and structure are licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

**Note:** Each individual plugin may be subject to its own license, as specified in its respective table entry or source code.
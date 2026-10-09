# Andy - Modern GTK4 & Libadwaita scrcpy Wrapper

<div align="center">

![Andy Banner](assets/icon.svg)

**A modern, Wayland-native, Amberol-inspired GUI wrapper for [scrcpy](https://github.com/Genymobile/scrcpy) built with Python, GTK4, and Libadwaita.**

[![Platform](https://img.shields.io/badge/Platform-Linux%20(Wayland%20Native)-blue.svg)](#system-requirements)
[![Toolkit](https://img.shields.io/badge/GUI-GTK4%20%2F%20Libadwaita-success.svg)](#prerequisites--installation)
[![scrcpy](https://img.shields.io/badge/scrcpy-v2.0%20%7C%20v3.0%20%7C%20v5.0+-orange.svg)](https://github.com/Genymobile/scrcpy)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](#)
[![License](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)

</div>

---

## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Design Philosophy](#design-philosophy)
- [Prerequisites & Multi-Distro Installation](#prerequisites--multi-distro-installation)
  - [Debian / Ubuntu / Pop!_OS / Linux Mint](#debian--ubuntu--pop_os--linux-mint)
  - [Fedora / RHEL / CentOS Stream](#fedora--rhel--centos-stream)
  - [Arch Linux / Manjaro / EndeavourOS](#arch-linux--manjaro--endeavouros)
  - [openSUSE (Tumbleweed / Leap)](#opensuse-tumbleweed--leap)
  - [NixOS / Nix Package Manager](#nixos--nix-package-manager)
  - [Void Linux](#void-linux)
- [Quick Start: Building & Running](#quick-start-building--running)
- [Desktop Integration](#desktop-integration)
- [Android Device Configuration](#android-device-configuration)
  - [Enabling USB Debugging](#enabling-usb-debugging)
  - [Configuring Udev Rules](#configuring-udev-rules)
  - [Wireless ADB Setup](#wireless-adb-setup)
- [Command-Line Interface (CLI)](#command-line-interface-cli)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Troubleshooting](#troubleshooting)
- [Architecture & Testing](#architecture--testing)
- [License & Acknowledgments](#license--acknowledgments)

---

## Overview

**Andy** bridges the power and efficiency of `scrcpy` with the elegance of modern GNOME design. While `scrcpy` is the gold standard for high-performance Android mirroring and control over USB or Wi-Fi, memorizing dozens of CLI flags for varying workflows (gaming, webcam, presentation, device recovery) is cumbersome.

Andy solves this by wrapping `scrcpy` in an intuitive Libadwaita interface with:
- **Zero-lag execution**: `scrcpy` runs directly as an optimized native subprocess.
- **Wayland exclusive**: Built from the ground up for modern Wayland compositors (GNOME Shell, Sway, Hyprland, KDE Plasma Wayland).
- **Amberol-style aesthetic**: Borderless, seamless headerbars and floating controls that immerse directly into the application body.

---

## Key Features

### 🎮 Display & Performance
- **Dynamic Resolution Calculation**: Automatically probes device native resolution and calculates 5 proportional scaling tiers (100%, 75%, 50%, 35%, 25%).
- **Real-Time Orientation Tracking**: Actively detects device rotation (portrait vs landscape) in the background to ensure stream dimensions remain sharp.
- **Hardware Decoding (HWDEC)**: Toggle VA-API hardware acceleration or downsize fallbacks on the fly.
- **Render Fit**: Choose between `letterbox`, `stretched`, or `unscaled` rendering modes.
- **Custom Max FPS & Bitrate**: Tailor frame rates (30, 60, 90, 120 FPS) and bitrates (2 to 64 Mbps) to your connection quality.

### ⌨️ Input & Peripherals
- **Connect M/K Bridge**: Ultra-low-resource mode that forwards host Mouse and Keyboard events directly to Android without decoding or rendering heavy video frames.
- **UHID Gamepad Forwarding**: Connect your PC controller (DualSense, Xbox, Switch Pro) and forward it directly as an Android physical gamepad.
- **Custom Mouse Bindings & Key Injection**: Configurable right-click and middle-click bindings, along with legacy paste emulation for stubborn apps.

### 📹 Camera Streaming
- **Turn Your Phone into a High-Definition Linux Webcam**: Stream from front, back, or external camera sensors.
- **Camera Controls**: Adjust camera FPS, sensor digital zoom (Android 11+), and enable High-Speed capture.

### 🖥️ Virtual Display & Multitasking
- **Secondary Virtual Display**: Launch independent Android virtual screens (`--new-display`) with flexible resizing (`--flex-display`) and customizable IME keyboard policies.
- **Direct App Launch**: Specify an Android package name (`--start-app=com.example.app`) to start directly inside the mirrored window.

### ⚙️ System & Profile Management
- **Persistent Profiles**: Save custom parameter profiles (`Gaming 120Hz`, `Office Work`, `HD Webcam`, `Broken Screen`) stored under standard XDG paths (`~/.config/andy/profiles/`).
- **Inhibit System Sleep**: Automatically prevents your Linux desktop from dimming, sleeping, or activating screensavers during active mirroring sessions.
- **Native Notifications**: Dispatches desktop notifications upon screenshot capture, screen recording completion, and connection status changes.

---

## Design Philosophy

Andy adheres strictly to the **GNOME Human Interface Guidelines (HIG)**:
- **Amberol-Inspired HeaderBar**: The top titlebar is completely textless, borderless, and flat. Standard window controls (Close, Minimize, Maximize) float weightlessly on top of the window canvas.
- **GNOME Circle Theming**: Native light and dark color schemes with circular action buttons and pill status badges.
- **Permanent Slim Sidebar**: A clean 220px utility pane housing profile management, light/dark mode toggles, and system preferences without cluttering the main stream control hub.

---

## Prerequisites & Multi-Distro Installation

Andy requires **Python 3.10+**, **GTK4**, **Libadwaita (1.4+)**, **GObject Introspection**, and **scrcpy** (v2.0+ recommended; scrcpy 5.0+ for advanced display features).

Install system dependencies for your distribution below:

### Debian / Ubuntu / Pop!_OS / Linux Mint
```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-4.0 \
    gir1.2-adw-1 \
    libadwaita-1-dev \
    scrcpy \
    adb
```

### Fedora / RHEL / CentOS Stream
```bash
sudo dnf install -y \
    python3 \
    python3-pip \
    python3-gobject \
    gtk4 \
    libadwaita-devel \
    scrcpy \
    android-tools
```

### Arch Linux / Manjaro / EndeavourOS
```bash
sudo pacman -S --needed \
    python \
    python-pip \
    python-gobject \
    gtk4 \
    libadwaita \
    scrcpy \
    android-tools
```

### openSUSE (Tumbleweed / Leap)
```bash
sudo zypper in -y \
    python3 \
    python3-pip \
    python3-gobject \
    typelib-1_0-Gtk-4_0 \
    typelib-1_0-Adw-1 \
    libadwaita-devel \
    scrcpy \
    android-tools
```

### NixOS / Nix Package Manager

Run Andy in an ephemeral development shell:
```bash
nix-shell -p python3 python3Packages.pygobject3 gtk4 libadwaita scrcpy android-tools
```

Or add the following to your `shell.nix`:
```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python3
    python3Packages.pygobject3
    gtk4
    libadwaita
    scrcpy
    android-tools
  ];
  shellHook = ''
    export GDK_BACKEND=wayland
  '';
}
```

### Void Linux
```bash
sudo xbps-install -Sy \
    python3 \
    python3-pip \
    python3-gobject \
    gtk4 \
    libadwaita \
    scrcpy \
    android-tools
```

---

## Quick Start: Building & Running

1. **Clone the repository**:
   ```bash
   git clone https://github.com/WolfSekhar/Andy.git
   cd Andy
   ```

2. **Set up the virtual environment**:
   ```bash
   ./build.sh
   ```
   *This creates a Python virtual environment (`venv`) and installs PyGObject.*

3. **Launch Andy**:
   ```bash
   ./run.sh
   ```
   *The run script enforces Wayland backend (`GDK_BACKEND=wayland SDL_VIDEODRIVER=wayland`) and starts the interface.*

---

## Desktop Integration

To add Andy to your Linux application menu with full icon branding and desktop quick actions, run:

```bash
./desktop.sh
```

This installs:
- Desktop file to `~/.local/share/applications/com.wolfsekhar.Andy.desktop`
- AppStream metadata to `~/.local/share/metainfo/com.wolfsekhar.Andy.metainfo.xml`
- Vector SVG icon to `~/.local/share/icons/hicolor/scalable/apps/com.wolfsekhar.Andy.svg`
- Desktop right-click quick actions:
  - **Start Screen Mirroring**
  - **Connect Keyboard & Mouse**

---

## Android Device Configuration

### Enabling USB Debugging
1. On your Android device, navigate to **Settings > About Phone**.
2. Tap **Build Number** 7 times until Developer Options are unlocked.
3. Open **Settings > System > Developer Options**.
4. Enable **USB Debugging** (and optionally **USB Debugging (Security settings)** for input simulation).
5. Plug your phone into your computer via USB.
6. When prompted on your phone, check **Always allow from this computer** and tap **Allow**.

### Configuring Udev Rules
If your system shows `no permissions (missing udev rules?)` when running `adb devices`:

```bash
# Ubuntu/Debian
sudo apt install -y android-sdk-platform-tools-common

# Fedora / Arch / Manual
sudo bash -c 'echo "SUBSYSTEM==\"usb\", ATTR{idVendor}==\"*\", MODE=\"0666\", GROUP=\"plugdev\"" > /etc/udev/rules.d/51-android.rules'
sudo udevadm control --reload-rules
sudo udevadm trigger
sudo usermod -aG plugdev $USER
```
*(Log out and log back in for group changes to take effect).*

### Wireless ADB Setup
1. Connect phone via USB once.
2. In terminal, enable TCP mode:
   ```bash
   adb tcpip 5555
   ```
3. Disconnect USB cable and connect using phone's Wi-Fi IP address:
   ```bash
   adb connect <PHONE_IP_ADDRESS>:5555
   ```
4. Andy will immediately detect the wireless connection and display the `Wi-Fi` status chip!

---

## Command-Line Interface (CLI)

Andy includes a full single-instance CLI parser:

```bash
./run.sh [OPTIONS]
```

| Option | Description |
| :--- | :--- |
| `--start` | Immediately launch mirroring on the active or selected device |
| `--connect-mk` | Start directly in Mouse & Keyboard input bridge mode |
| `-s, --device <SERIAL>` | Target a specific Android device by ADB serial number |
| `--version` | Display Andy version information |
| `-h, --help` | Show command-line help options |

---

## Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl + Enter` | Start / Stop stream session |
| `Ctrl + S` | Save active settings profile |
| `Ctrl + R` | Refresh connected ADB devices |
| `Ctrl + ,` | Open Settings & Profiles dialog |
| `Ctrl + Q` | Quit application safely |
| `F1` | Open About Andy dialog |

---

## Troubleshooting

### Device shows as "Unauthorized"
- Disconnect USB cable, reconnect, and unlock your phone screen.
- Accept the RSA fingerprint authorization dialog on your phone.
- Run `adb devices` in terminal to confirm it says `device` instead of `unauthorized`.

### Screen appears blank or black
- Check if your device screen is locked or secured with FLAG_SECURE (banking apps / DRM content).
- If your phone screen is broken, use the **Broken Screen** profile in Andy to mirror directly without requiring display touch interactions.

### Audio is not playing
- Ensure your phone runs **Android 11 or higher** (Android 10 requires audio forwarding flags; Android 11+ supports native audio capture).
- Verify PipeWire / PulseAudio is running on your host system.

---

## Architecture & Testing

Andy is engineered with modular decoupling:
- `src/core/`: Configuration, CLI command builder, model dataclasses, and process lifecycle supervisors.
- `src/services/`: Device discovery, XDG settings/profile managers, power inhibitor service, and desktop notification service.
- `src/ui/`: Amberol-style textless headerbar, permanent slim sidebar, modular layout cards, and custom CSS styling.

### Running Automated Tests
Andy includes a comprehensive unit and integration test suite:

```bash
./venv/bin/pytest tests/ -v
```

All 117+ tests pass covering toggle states, scrcpy 5.0 flags, XDG standards, and UI widgets.

---

## License & Acknowledgments

- **License**: GNU General Public License v3.0 ([GPL-3.0](LICENSE)).
- **scrcpy**: Developed by [Genymobile](https://github.com/Genymobile/scrcpy) and Romain Vimont.
- **GNOME / Libadwaita**: Developed by the GNOME design and development team.
- **Amberol**: UI immersion and aesthetic inspiration by Emmanuele Bassi.

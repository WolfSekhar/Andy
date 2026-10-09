# Development Experience & Feature History: Andy (GTK4 scrcpy Wrapper)

This document serves as a chronological memory log of the development session, capturing the user's prompts, the architectural thinking, feature implementation details, and how we tackled various errors along the way.

---

## 1. Initial Goal: Camera Streaming and Error Handling
**Prompt:** `"stream fron camera and check that weach error measn"`

**Thinking & Implementation:**
*   **Goal:** The user wanted to use `scrcpy`'s camera streaming feature and understand why it might fail.
*   **Action:** Instead of just running it in the background, we realized the GUI needed a robust way to bubble up `scrcpy` errors. We added a background thread to capture `stderr` from the `subprocess.Popen` call and attached a `GLib.child_watch_add` to trigger a GTK `Adw.MessageDialog` when the process exited with a non-zero code. This made debugging Android-side hardware errors much easier.

## 2. Refactoring and Camera Error Investigation
**Prompt:** `"run the app and stream the front camera as testing and check why error is coming. 2. split @src/window.py to differnt smaller files accroding to funcitons for better manaegment."`

**Thinking & Implementation:**
*   **Refactoring:** `src/window.py` was growing too large (500+ lines). We split it into a modular `src/ui/ package: `window.py` (main orchestrator), `header_bar.py`, and `settings_dialog.py`.
*   **Error Encountered:** `android.hardware.camera2.CameraAccessException: The system-wide limit for number of open cameras has been reached.`
*   **How we figured it out:** By looking at the new error dialog we built in step 1, which captured the raw `scrcpy` server logs. We identified this as an Android hardware lock (another app was likely using the camera) rather than a bug in our Python code.

## 3. Fixing the Libadwaita Inheritance Crash
**Prompt:** `"run app and fix erros"`

**Thinking & Implementation:**
*   **Error Encountered:** `RuntimeError: could not create new GType: header_bar+AndyHeaderBar (subclass of AdwHeaderBar)`.
*   **How we figured it out:** Modern Libadwaita (`Adw`) marks certain widgets like `HeaderBar` as *final types*. We realized that PyGObject cannot create new GTypes from these final parents. 
*   **The Fix:** Shifted from **Inheritance** to **Composition**. We refactored `AndyHeaderBar` to be a standard Python class that *wraps* an `Adw.HeaderBar` instance (`self.widget = Adw.HeaderBar()`), bypassing the GType system's restriction.

## 4. "Connect M/K" (Mouse/Keyboard Only Mode)
**Prompt:** `"is it possible to send just mouse and keyboard input without streaming screen. if possible then create a button right side to the stream button with lable connect M/K."`

**Thinking & Implementation:**
*   **Goal:** Save bandwidth and host resources by controlling the device without a video feed.
*   **Action:** Added the UI button and created a state machine so "Stream" and "Connect M/K" buttons act exclusively (one disables the other, turning red to indicate "STOP/DISCONNECT"). Initially, we used `--no-video` and `--no-audio`.

## 5. Dynamic Resolution Calculation
**Prompt:** `"also want one more feature like when device resolution drop down is clicked it shows some predetined values. rahtern than pre default values it will acess the device display and resoulitno and calculate the available max value and minimum five level values on the fly with height and width of the deivce. if the device is rotated then the values will show interchanged resolution values for best reslults."`

**Thinking & Implementation:**
*   **Goal:** Replace hardcoded resolutions (`1920`, `1280`) with smart, device-specific aspect ratios.
*   **Action:** Implemented `get_device_resolution` via ADB. We parsed `wm size` and `dumpsys display` to get the native dimensions and current orientation. We then calculated 5 dynamic levels: Native (100%), Balanced (80%), Smooth (60%), Lite (40%), Minimal (20%). The `scrcpy` command generator was updated to extract the maximum dimension from these dynamic `WxH` strings to feed into `--max-size`.

## 6. Fixing M/K Input Focus
**Prompt:** `"when connect Connect M/K button is clicked then do one thing stream whte whoe screen with lowerst resolution availabe as possible in full screen because withou streaming mouse keyboad are not wokring."`

**Thinking & Implementation:**
*   **Error Encountered:** Mouse and keyboard inputs were being ignored when "Connect M/K" was active.
*   **How we figured it out:** We realized that by using `--no-video`, `scrcpy` doesn't create an X11/Wayland window. Without a window, the desktop environment has no "surface" to capture mouse clicks or keyboard focus to send to the device.
*   **The Fix:** Instead of no video, we created a "dummy" focus window by launching `scrcpy` with `--max-size=128` (lowest possible resolution) and `--fullscreen`. This provided the necessary GUI surface area to capture inputs without visible resource drain.

## 7. Custom Editable Parameters & UHID Debugging
**Prompt:** `"integrate a plan to also set custom values field with drop down for the max fps and max size where the value can be entered. mouse keyboard uhid is not getting toggled and set. check why"`

**Thinking & Implementation:**
*   **Custom Inputs:** Swapped `Gtk.DropDown` for `Gtk.ComboBoxText.new_with_entry()`. This allowed the UI to hold the dynamic presets while also letting the user type specific numbers (e.g., `800` or `45`).
*   **UHID Issue:** Investigated why the toggles weren't working. Found that our `AdvancedCard` intentionally disabled UHID if "Read-Only" or "Camera Mode" were selected (since inputs are incompatible with those modes). We renamed the labels to `Keyboard (HID/OTG Mode)` to clarify their function and verified the flags were passing correctly when in standard screen mode.

## 8. Background Orientation Monitoring
**Prompt:** `"also create a background process which will monitor the device portrait or landscape resoluton orientaiotn change. and show the values in accordance to what found."`

**Thinking & Implementation:**
*   **Error Encountered:** `AttributeError: 'ListStore' object has no attribute 'get_n_items'`.
*   **How we figured it out:** When trying to iterate through the `ComboBoxText` to preserve user input during a rotation refresh, we assumed it shared the same API as `Gtk.StringList`. A quick check of the GTK4 documentation revealed that `ComboBoxText` uses a `ListStore` model.
*   **The Fix:** Switched to using `model.iter_n_children(None)` and `model.iter_nth_child()` to correctly traverse the widget's internal data storage.
*   **Optimization:** Optimized the ADB call to execute `grep` directly on the Android shell (`adb shell "dumpsys display | grep mCurrentDisplayRect"`) to reduce polling overhead to almost zero.

## 9. Fixing Camera Dynamic Resolution
**Prompt:** `"while changing screen to camera the max video resiltuion setting are not automatically changing. figure out why. working perfectly detection for screen but not for camera"`

**Thinking & Implementation:**
*   **Error Encountered:** The background monitor was strictly polling the *screen* orientation, meaning the dropdown was wrong when switching to front/back cameras.
*   **How we figured it out:** Realized that camera sensors have fixed native resolutions independent of the tablet's physical rotation. 
*   **The Fix:** Added logic to parse the exact `WxH` resolution of the selected camera (e.g., `4128x3096` for back) directly from the `scrcpy --list-cameras` string. The 5 UI presets now rebuild themselves proportionally based on the camera hardware when in Camera Mode.

## 10. Desktop Integration
**Prompt:** `"create a folder called assets... create a desktop.sh script which will generate a desktop file and store iti n user local folder..."`

**Thinking & Implementation:**
*   **Goal:** Make the CLI tool feel like a native desktop app.
*   **Action:** Hand-wrote an SVG icon featuring a laptop with a phone screen, dumped it into `assets/`, and wrote a bash script to map absolute execution paths, injecting them into a standard `~/.local/share/applications/Andy.desktop` file.

## 11. Wayland Taskbar Icon Fix (GLib Program Name & Desktop ID Alignment)
**Prompt:** `"i think that when this app is lauched in wayland session its app task icon is showing a wayland icon. i think there is a word ground to fix this issue related to application."`

**Thinking & Implementation:**
*   **Root Cause:** In Wayland sessions (KDE Plasma/KWin and GNOME/Mutter), window icons are not set via X11 pixmaps (`_NET_WM_ICON`). Instead, compositors query the Wayland `app_id` (`xdg_toplevel.set_app_id`) and look for a matching desktop file `<app_id>.desktop` in `$XDG_DATA_DIRS/applications/` and theme icons in `$XDG_DATA_DIRS/icons/hicolor/`.
*   **Discovered Mismatches:**
    1. PyGObject defaults `GLib.get_prgname()` to `python3` unless explicitly overridden, causing GDK to identify windows with generic runtime properties.
    2. GTK4 `Adw.Application` set `application_id='com.wolfsekhar.Andy'`, but `desktop.sh` created `Andy.desktop` (without `StartupWMClass`), causing KWin to look for `com.wolfsekhar.Andy.desktop` and fail.
    3. The SVG icon was placed in `~/.local/share/icons/Andy.svg` instead of standard FreeDesktop theme path `hicolor/scalable/apps/com.wolfsekhar.Andy.svg`.
    4. Running directly from `./run.sh` without manual desktop script execution left no desktop registration for the compositor.
*   **The Fix:**
    1. **PyGObject Workaround:** Added `GLib.set_prgname('com.wolfsekhar.Andy')` and `GLib.set_application_name('Andy')` at the top of `src/main.py`.
    2. **Startup Registration & Signal Handling:** Connected to GApplication's `startup` and `activate` signals in `AndyApplication.__init__` (avoiding PyGObject vfunc descriptor argument mismatches), registered local assets in `Gtk.IconTheme`, set `Gtk.Window.set_default_icon_name('com.wolfsekhar.Andy')`, and added automatic desktop integration so running via `./run.sh` ensures the desktop entry and hicolor icons exist in user XDG directories.
    3. **Desktop Script Enhancement:** Updated `desktop.sh` to generate `com.wolfsekhar.Andy.desktop` with `StartupWMClass=com.wolfsekhar.Andy`, install to the standard `hicolor/scalable/apps/` directory, symlink `Andy.desktop`, and refresh desktop/icon database caches.
    4. **Window Explicit Icon:** Added `self.set_icon_name("com.wolfsekhar.Andy")` to `AndyWindow`.

---

### Key Takeaways
1. **GTK4/Libadwaita Evolution:** Moving from inheritance to composition is vital for modern GNOME development as library authors lock down base widget types.
2. **Process UX:** Silent command-line errors ruin GUI apps. Piping `stderr` to readable dialogs immediately solves the "why isn't it working?" user pain point.
3. **Hardware Quirks:** "No video" disables input capture. Sometimes the best architectural solution is a workaround (a 128px fullscreen window) rather than fighting the underlying C library.
4. **Wayland Window Identification:** On Wayland, window icons require strict end-to-end alignment between `GLib.set_prgname()`, `Gtk.Application`'s `application_id`, the `.desktop` file basename (`<app_id>.desktop`), `StartupWMClass`, and the hicolor scalable icon theme paths.

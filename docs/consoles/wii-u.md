# Wii U

Status: **prepared, not installed yet.** Module built and validated on the
bench (62 mA at 3.3 V, OTA tested, visible in Home Assistant); nothing
soldered inside the console. The test points below come from WiiUBrew and
still need to be confirmed with a multimeter.

Planned build: **bare ESP-12F + PhotoMOS AQY210EH**, no relay. See
[soft-power-buttons.md](../soft-power-buttons.md).

## Test points

Unlike most consoles, the Wii U's test points are **silkscreened on the
board itself** — look for `TPxxx` next to the pads. They are mostly on the
**underside, opposite the SoC**, so a magnifier is enough to find them, no
reference photo needed.

### Always on — to power the module

| Point | Description |
|---|---|
| **TP122** | 3.3 V always-on power rail |
| **TP114** | 3.3 V always-on rail of the disc drive |
| **TP164** | reference ground of the always-on 3.3 V |

TP122 with TP164 as ground is the pair to use for VCC / GND.

### Switched 3.3 V — candidates for the sense

WiiUBrew does not label these as on-only, so **measure before soldering**.
Ranked by how likely they are:

| Point | Description | Why |
|---|---|---|
| **TP142** | 3.3 V supply of the HDMI encoder | video only runs when the console does — first choice |
| **TP2** | 3.3 V of the disc drive | TP114 is the always-on version of the same subsystem, which suggests TP2 is the switched one |
| **TP138** | 3.3 V rail B (ground reference TP137) | |
| **TP168** | 3.3 V rail C (ground reference TP169) | |
| **TP132** | 3.3 V / 12 V power-good signal | literally a "console is powered" signal — worth exploring |

**Avoid TP139**, the Wi-Fi module supply: its enable line (TP141) comes from
the RTC, so it can stay alive in standby.

Check the sense in **every** state, including connected standby — the Wii U
stays on the network for downloads and to charge the GamePad.

One more point with a documented location, if you come across it: **TP148**
connects to the RTC, to the gate of Q1093 and to pin 13 of U1041.

Source:
[Hardware/Testpoints — WiiUBrew](https://wiiubrew.org/wiki/Hardware/Testpoints).

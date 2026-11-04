# Xbox OG (original Xbox, 2001)

Status: **working**, from Home Assistant and from the console's own power
button.

Build: **D1 mini + PhotoMOS AQY210EH**, no relay — the front power button is
a momentary push button. See
[soft-power-buttons.md](../soft-power-buttons.md).

## The power button shorts a line to ground

The button simply connects the SMC's power-button line to ground. That is
confirmed by the memory-card power-button mod, which wires pin 1 (ground) of
a controller port's memory card slot to one side of a button and the port's
unused yellow wire — soldered to the motherboard's `Power Button` point — to
the other: pressing them together powers the console on or off.

So one PhotoMOS across the two pads is all that is needed. The PhotoMOS is
the right part here because its output is a real floating contact and
polarity does not matter; a MOSFET would need the line to sit positive
relative to its source, or its body diode clamps it.

Tap the button on the **motherboard side** of the front-panel ribbon, not on
the front PCB, and run the two wires tightly together. This line is known to
pick up noise — the memory-card mod reports random power-ons with a poorly
shielded extension cable, and on the Xbox 360 Slim a worn ribbon caused
exactly that symptom.

## Power and sense depend on the board revision

Check the revision first. The PSU connector pinout differs, and so does the
standby **voltage**.

| Revision | Standby rail | Powers the D1 mini on | Sense |
|---|---|---|---|
| 1.0 / 1.1 | +3.3 V standby, pin 7 (single column of 12, pin 1 nearest the back) | its `3V3` pin | pin 8 = +3.3 V main, straight to D5 |
| 1.2 – 1.5 | +3.3 V standby, column 2 pin 6 (two columns of 10) | its `3V3` pin | column 1 pin 4 or column 2 pin 3, straight to D5 |
| 1.6 | **+5 V** standby, column 1 pins 8–10 and column 2 pin 8 | its `5V` pin | no clean main 3.3 V documented on this connector — find a switched 3.3 V elsewhere, or a switched 5 V through a divider as on the [PS4 Pro](ps4-pro.md) |

On 1.0 to 1.5 this is the most comfortable case met so far: the sense is a
real 3.3 V rail needing no divider, and the standby rail is already at the
right voltage to feed the D1 mini directly on its `3V3` pin, bypassing its
own regulator.

**The standby rail is not sized for an ESP.** It feeds the SMC and the front
panel. Measure it again with the D1 mini connected and associated to Wi-Fi,
not with a multimeter on an idle pin — the same trap as the PS4 Pro, where
the first candidate point collapsed to 2 V under load. If it sags, or if the
eject button or power-on become unreliable with the console off, move to the
main 12 V through a small buck. 100 nF close to the module either way.

## Pitfall: the ground pin

The first attempt on this console failed because the ground was taken from
the wrong pin of the PSU connector: the module came up and was visible in
Home Assistant, but the behaviour was erratic. Identify the GND pin with the
multimeter rather than by counting pins on a diagram.

## Idea, not designed yet: the eject button

The eject button also powers the console on, and opens the tray when it is
running. A second PhotoMOS across it on another free GPIO (D6 = GPIO12),
wired exactly like the power one, would give an "open the tray" button in
Home Assistant.

Sources: [Power Supply — xboxdevwiki](https://xboxdevwiki.net/Power_Supply),
[Xbox:Memory Card Power Button — ConsoleMods](https://consolemods.org/wiki/Xbox:Memory_Card_Power_Button),
[Power & Eject Button Circuit — RetroSix](https://www.retrosix.wiki/power-eject-button-circuit-xbox-original).

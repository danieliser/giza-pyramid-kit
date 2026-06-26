---
title: "A Printable Giza Construction Theory"
date: 2026-06-25
status: draft
tags:
  - 3d-printing
  - geometry
  - pyramids
  - experiments
---

# A Printable Giza Construction Theory

I wanted a physical model of a pyramid construction theory that is easier to understand with your hands than with a diagram.

The theory is not the familiar spiral-ramp story. The version I modeled is closer to the Huni Choi/DamiLee top-down idea: first build an oversized stepped working mass with switchback ramps and a broad flat platform at the top, place a small capstone, then remove the temporary material from the top down while adding the final casing stones. The removed material becomes stock for the next pyramid and other Giza works.

That is a wonderfully physical idea. It is about mass, sequence, access, sight lines, and reuse. A static pyramid does not show any of that. So I built a parametric STL kit.

## What The Model Shows

The kit breaks the construction sequence into printable and viewable stages:

- a below-grade chamber cut
- layer-by-layer stepped inner mound pieces
- temporary fill layers
- single switchback ramp layers
- notched corner landings for sight-line alignment
- a broad top work platform
- a small capstone
- removable casing rings added from the top downward
- an optional stockpile representing reused temporary material

The browser demo animates the same sequence: build upward course by course, set the capstone, dismantle the temporary ramp/fill system from the top down, and grow a reuse pile as the material comes off.

## Why Print It

The useful part of a printed model is that it makes the constraints visible.

If ramps are too thin, they become implausible. If landings do not connect, the theory stops reading as a construction system. If the top platform is too small, the capstone stage feels wrong. If chamber references float through everything, the model becomes a diagram instead of a build.

Iterating on the STL forced those questions into geometry. The ramps had to become solid. The gaps between ramp layers had to be backfilled. The chambers had to be sliced by construction course. The demo needed opacity controls because sometimes you want to see the theory as a solid pyramid, and sometimes you want an x-ray.

## Files

The project includes:

- a dependency-free Python generator
- printable STL outputs
- constructed-state STL snapshots
- a static Three.js demo
- validation checks for the generated geometry

The default model is a 160 mm finished pyramid, but a 100-120 mm footprint is probably the sweet spot for a desktop FDM printer.

## Caveat

This is a conceptual model, not archaeological proof.

That distinction matters. The point is not to settle the question of how the Great Pyramid was built. The point is to make a theory inspectable: where it feels elegant, where it strains, and what geometry it requires.

The repository is meant as a sandbox for exactly that kind of argument.


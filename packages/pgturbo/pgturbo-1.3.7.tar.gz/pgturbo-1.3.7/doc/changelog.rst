Changelog
=========

This changelog tracks changes to Pygame Turbo. For the changelog of the
original Pygame Zero, check below.


1.3.5 - 2025-09-23
------------------

This was the initial fork from Pygame Zero with different PRs being
integrated to create the first state of Pygame Turbo.

Since Turbo was forked from Pygame Zero during its unreleased version 1.3
stage, its version numbering starts from 1.3.5 to avoid confusion.


New features
''''''''''''

* A proper ``mouse`` builtin to get the state of different mouse properties
  like positions, relative movements, state of buttons being pressed and
  more. Also allows changing of visibility, cursor shape and others.


Feature enhancements
''''''''''''''''''''

* Pixel perfect collision check between two actors via
  ``actor1.collidemask(actor2)``.
* Angle and target-based movement functions for Actors, similar to what is
  possible in Scratch and other environments.
* Velocity property and movement function for Actors that only move in
  straigth lines. Also includes an intercept function to calculate necessary
  velocity to meet a target actor that also has a constant velocity.
* Create Actors from simple shapes without needing an image, via
  ``Actor.Rectangle(width, height, color)``,
  ``Actor.Ellipse(width, height, color)`` and
  ``Actor.Triangle(width, height, color)``.
* Function to check if an actor is currently withing the screen bounds:
  ``.is_onscreen()``.


Bug fixes
'''''''''

* Fixed ``music.is_playing()`` requiring an argument.
* Made actor ``width`` and ``height`` read-only properties while no solution
  for scaling actors is implemented.


Pygame Zero Changelog
---------------------

The following is the changelog of Pygame Zero leading up to the forking of
Pygame Turbo:

1.3 - unreleased
''''''''''''''''

* New: :ref:`Actors can be made transparent <transparency>` by assigning to
  ``actor.opacity`` (based on work by Rhys Puddephatt and charlesej)
* New: screen.fill() now takes ``gcolor``, creating a vertical-linear gradient
* New: a :doc:`REPL <repl>` has been added, which allows exploring a game's
  state while it is running.
* New: Added a :ref:`storage API <data-storage>`, which preserves data across
  game runs (based on work by Ian Salmons and Gustavo Ferreira)


1.2 - 2018-02-24
''''''''''''''''

* New: :ref:`Actors can be rotated <rotation>` by assigning to ``actor.angle``
* New: Actors now have :meth:`~Actor.angle_to()` and
  :meth:`~Actor.distance_to()` methods.
* New: Actors are no longer subclasses of Rect, though they provide the same
  methods/properties. However they are now provided with floating point
  precision.
* New: ``tone.play()`` function to allow playing musical notes.
* New: ``pgtrun.go()`` to allow running Pygame Turbo from an IDE (see
  :doc:`ide-mode`).
* New: show joypad icon by default
* Examples: add Asteroids example game (thanks to Ian Salmons)
* Examples: add Flappy Bird example game
* Examples: add Tetra example game (thanks to David Bern)
* Docs: Add a logo, fonts and colours to the documentation.
* Docs: Documentation for the :ref:`anchor point system for Actors <anchor>`
* Docs: Add :doc:`from-scratch` documentation
* Fix: ``on_mouse_move()`` did not correctly handle the ``buttons`` parameter.
* Fix: Error message when resource not found incorrectly named last extension
  searched.
* Fix: Drawing wrapped text would cause crashes.
* Fix: :func:`animate()` now replaces animations of the same property, rather
  than creating two animations which fight.
* Updated ptext to a revision as of 2016-11-17.
* Removed: removed undocumented British English ``centrex``, ``centrey``,
  ``centre`` attribute aliases on ZRect (because they are not Rect-compatible).

1.1 - 2015-08-03
''''''''''''''''

* Added a spell checker that will point out hook or parameter names that have
  been misspelled when the program starts.
* New ZRect built-in class, API compatible with Rect, but which accepts
  coordinates with floating point precision.
* Refactor of built-in ``keyboard`` object to fix attribute case consistency.
  This also allows querying key state by ``keys`` constants, eg.
  ``keyboard[keys.LEFT]``.
* Provide much better information when sound files are in an unsupported
  format.
* ``screen.blit()`` now accepts an image name string as well as a Surface
  object, for consistency with Actor.
* Fixed a bug with non-focusable windows and other event bugs when running in
  a virtualenv on Mac OS X.
* Actor can now be positioned by any of its border points (eg. ``topleft``,
  ``midright``) directly in the constructor.
* Added additional example games in the ``examples/`` directory.

1.0.2 - 2015-06-04
''''''''''''''''

* Fix: ensure compatibility with Python 3.2

1.0.1 - 2015-05-31
''''''''''''''''

This is a bugfix release.

* Fix: Actor is now positioned to the top left of the window if ``pos`` is
  unspecified, rather than appearing partially off-screen.

* Fix: repeating clock events can now unschedule/reschedule themselves

  Previously a callback that tried to unschedule itself would have had no
  effect, because after the callback returns it was rescheduled by the clock.

  This applies also to ``schedule_unique``.

* Fix: runner now correctly displays tracebacks from user code

* New: Eliminate redraws when nothing has changed

  Redraws will now happen only if:

      * The screen has not yet been drawn
      * You have defined an update() function
      * An input event has been fired
      * The clock has dispatched an event


1.0 - 2015-05-29
''''''''''''''''

* New: Added ``anchor`` parameter to Actor, offering control over where its
  ``pos`` attribute refers to. By default it now refers to the center.

* New: Added Ctrl-Q/⌘-Q as a hard-coded keyboard shortcut to exit a game.

* New: ``on_mouse_*`` and ``on_key_*`` receive ``IntEnum`` values as ``button``
  and ``key`` parameters, respectively. This simplifies debugging and enables
  usage like::

        if button is button.LEFT:


1.0beta1 - 2015-05-19
''''''''''''''''

Initial public (preview) release.

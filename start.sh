#!/bin/bash
# CUA-LIBRE STUDIO — comando único de arranque.
# uv aprovisiona Python y las dependencias automáticamente (research.md D9).
cd "$(dirname "$0")"
exec uv run run.py

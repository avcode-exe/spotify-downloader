@echo off
title Spotify Downloader - TUI
cd /d "%~dp0"
python spotify_downloader.py %*
pause

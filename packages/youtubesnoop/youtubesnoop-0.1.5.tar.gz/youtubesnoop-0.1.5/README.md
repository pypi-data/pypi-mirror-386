# YoutubeSnoop

[![](https://img.shields.io/pypi/v/youtubesnoop.svg)](https://pypi.org/pypi/youtubesnoop/)

A Youtube downloader of the highest quality

---

## Installation

You can install it via pip:

```bash
$ pip install youtubesnoop
```

---

## Prerequisites

* [ffmpeg](https://ffmpeg.org/) must be installed and available in your PATH.

---

## Usage

A simple command-line tool that downloads Youtube videos in the highest quality available.

Just provide a Youtube URL:

```bash
$ youtubesnoop https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

It will download single tracks to this format:

```plaintext
{title}.flac
```

### Downloading Album Playlists

Provide a playlist URL and it will create a folder for the artist and nest it with the year and album title:

```plaintext
{artist}/{year} - {albumTitle}
```

This fits my personal need to download albums from Youtube playlists.

Each track will be named like this:

```plaintext
{tracknumber}. {title}.flac
```

It will try to infer the metadata from the playlist and set it in the downloaded files. Otherwise it will prompt you for it. It uses the [mutagen](https://mutagen.readthedocs.io/en/latest/) library to set the metadata with the help of [musicbrainz](https://musicbrainz.org/) to fix any mistakes. It uses [musicbrainzngs](https://pypi.org/project/musicbrainzngs/) to download cover art as `Cover.jpg` or `Cover.png` and place it in the folder and added to the metadata of each track.

### Videos

It downloads as `flac` files per default but with the `--video` flag it will download the video as `mp4` instead.


---

## 403 Forbidden Errors

Youtube constantly changes their API. The solution is likely to upgrade the `yt-dlp` dependency that this package uses under the hood.

Run:

```bash
$ pip install --upgrade youtubesnoop
```

Or:

```bash
$ pipx upgrade yt-dlp
```

---

## Windows Note

It has been tested on Windows (Powershell) and MacOS. 

For Powershell, remember to wrap the URL in quotes to avoid issues with special characters such as `&` being interpreted.

On Windows, don't use Git Bash since `prompt_toolkit` has issues with it ANSI escape codes etc.


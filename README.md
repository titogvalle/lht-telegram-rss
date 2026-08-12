# LHT Telegram RSS bridge

Generates a podcast RSS feed from audio posts in the public Telegram channel `@lht_hn`, using TelegramRSS JSON endpoints.

## What it does

- Reads the newest 10 pages (up to 1,000 Telegram posts).
- Keeps posts that look like audio.
- Generates a standard RSS 2.0 feed with `<enclosure>` audio URLs.
- Writes the feed to `docs/lht.xml`.
- GitHub Actions can rebuild it automatically.

## GitHub Pages setup

1. Create a GitHub repository and upload these files.
2. In repository Settings → Pages, choose **GitHub Actions** as the source.
3. The workflow in `.github/workflows/update.yml` runs twice a day and publishes `docs/`.
4. Your RSS URL will be:
   `https://YOUR-USER.github.io/YOUR-REPO/lht.xml`
5. Import that URL as a podcast in ClearWave.

The generated feed uses the TelegramRSS media endpoint rather than copying the audio files into the repository.

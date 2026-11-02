# Roofing site template

A one-page roofing contractor site: sentence-split hero with a roof reel (or the client's video), services table, scroll-zoom "look closer" section, live roof-cost estimator, staircase process, service-area list, project gallery, FAQ and contact.

## Set up a new client (about 10 minutes)

1. Copy this repo for the client.
2. Open `index.html` and edit the `window.SITE` block at the top. Every name, number, price, service and town on the page comes from there.
3. Replace everything marked `SAMPLE`, especially:
   - business name, phone, email, license number
   - price per roofing square for each material (drives the estimator)
   - quote turnaround and the service-area towns
4. Hero video (optional, recommended): put the client's clip in `assets/` and set `heroVideo` and `heroPoster`.
   Compress it first:
   ```
   ffmpeg -i raw.mov -t 10 -vf "scale=1280:-2" -an -c:v libx264 -crf 28 -preset veryfast -movflags +faststart assets/hero.mp4
   ffmpeg -i assets/hero.mp4 -frames:v 1 -q:v 3 assets/hero.jpg
   ```
5. Swap the drawn placeholders ("Client photo", "Client project photo") for real job photos.
6. Have the client confirm the FAQ answers.

## Rules

- Never add reviews, ratings or stats the client didn't give you.
- Keep stock or AI footage generic (weather, sky, materials); never present it as the client's own job.

## Deploy

Static site, no build step. Import the repo in Vercel (framework preset: Other) and deploy.

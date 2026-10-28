# Atelier

A home for my watercolor, colored pencil and pastel art: a public gallery, a private studio dashboard, and AI help for titles, descriptions and palettes.

> **Status: In progress, week 1 of 8.** Nothing below is built yet. This README describes the plan and will be updated as features land.

## What it will do

- **Public gallery**: browse my artwork, filter by medium (watercolor, colored pencil, pastel) and by series.
- **Artwork detail page**: a single piece with its image and details.
- **Studio dashboard** (behind login): add and edit artworks, upload images, mark pieces as sold.
- **"AI suggest" button**: title ideas, a gallery description, and the color palette with pigment suggestions.

## Planned architecture

| Folder | Role | Stack |
| --- | --- | --- |
| [`web/`](web/) | Gallery and studio dashboard UI | React, TypeScript |
| [`api/`](api/) | REST API, auth, data, image uploads | Spring Boot 4, Java 21, MySQL |
| [`ai/`](ai/) | "AI suggest" service | Python, FastAPI, Claude API |

Planned flow: `web` talks to `api`, and `api` calls `ai` for suggestions.

## Demo

Demo video: _coming soon_

## Screenshots

_Coming soon: gallery, artwork detail, studio dashboard, AI suggest._

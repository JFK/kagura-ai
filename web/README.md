# Kagura Memory Cloud - Web Dashboard

Issue #651 - Web Admin Dashboard for Kagura Memory Cloud

## Tech Stack

- Next.js 15.1
- React 19
- TypeScript 5
- Tailwind CSS 3.4
- shadcn/ui (TBD)

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

## Production Build

```bash
# Build
npm run build

# Start production server
npm start
```

## Docker

```bash
# Build image
docker build -t kagura-web:cloud .

# Run container
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=https://memory.kagura-ai.com/api/v1 kagura-web:cloud
```

## Environment Variables

- `NEXT_PUBLIC_API_URL`: Kagura API endpoint (default: http://localhost:8080/api/v1)

## Development Status

- [x] Project setup
- [ ] OAuth2 login
- [ ] Dashboard page
- [ ] Memory management
- [ ] API Key management
- [ ] Settings & Config UI

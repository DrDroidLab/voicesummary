# Voice Summary Frontend

A modern Next.js frontend for the Voice Summary API, featuring audio playback and transcript visualization.

## Features

- 🎵 **Audio Player**: Full-featured audio player with play/pause, progress bar, and volume control
- 📋 **Call List**: Paginated list of audio calls with reverse timestamp ordering
- 📝 **Transcript Viewer**: Interactive transcript display with expandable sections
- 🎨 **Modern UI**: Clean, responsive design built with Tailwind CSS
- 📱 **Mobile Friendly**: Responsive design that works on all devices

## Screenshots

- **Call List**: Shows all calls with timestamps and call IDs
- **Audio Player**: Interactive player with progress bar and controls
- **Transcript**: Structured view of conversation data with raw JSON option

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **HTTP Client**: Native fetch API
- **TypeScript**: Full type safety

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Voice Summary API running (default: http://localhost:8000)

### Installation

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Start development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Configuration

### API Endpoint

The frontend is configured to proxy API requests to your backend. Update `next.config.js` if your API is running on a different port:

```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:8000/api/:path*', // Change this URL
    },
  ];
}
```

### Environment Variables

Create a `.env.local` file in the frontend directory if needed:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Usage

### 1. View Call List

- Calls are displayed in reverse chronological order (newest first)
- Each call shows the call ID and timestamp
- Click on any call to view details

### 2. Audio Playback

- **Play/Pause**: Click the large play button to start/stop audio
- **Progress Bar**: Click anywhere on the progress bar to seek
- **Volume Control**: Adjust volume with the slider or mute button
- **Time Display**: Shows current time and total duration

### 3. Transcript View

- **Overview**: Quick summary of call details
- **Conversation**: Structured view of the conversation
- **Raw JSON**: Complete transcript data in JSON format

## Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── globals.css        # Global styles with Tailwind
│   ├── layout.tsx         # Root layout component
│   └── page.tsx           # Main page component
├── components/             # React components
│   ├── AudioPlayer.tsx    # Audio player with controls
│   ├── CallList.tsx       # Paginated call list
│   └── TranscriptViewer.tsx # Transcript display
├── types/                  # TypeScript type definitions
│   └── call.ts            # Call data types
├── package.json            # Dependencies and scripts
├── tailwind.config.js      # Tailwind CSS configuration
└── next.config.js          # Next.js configuration
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Customization

### Styling

The UI is built with Tailwind CSS. Customize colors and styles in:

- `tailwind.config.js` - Theme configuration
- `app/globals.css` - Custom CSS classes

### Components

Each component is modular and can be easily customized:

- `AudioPlayer.tsx` - Audio controls and progress
- `CallList.tsx` - Call list display and pagination
- `TranscriptViewer.tsx` - Transcript formatting

## API Integration

The frontend integrates with these API endpoints:

- `GET /api/calls/` - List all calls with pagination
- `GET /api/calls/{id}/audio` - Download audio file
- `GET /api/calls/{id}/transcript` - Get transcript data

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

### Audio Not Playing

1. Check browser console for errors
2. Verify audio file format (MP3, WAV, etc.)
3. Ensure CORS is properly configured on the backend

### API Connection Issues

1. Verify the backend is running on the expected port
2. Check `next.config.js` proxy configuration
3. Ensure the backend API is accessible

### Build Issues

1. Clear `.next` directory: `rm -rf .next`
2. Reinstall dependencies: `rm -rf node_modules && npm install`
3. Check Node.js version compatibility

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Voice Summary system.

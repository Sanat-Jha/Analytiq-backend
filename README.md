<p align="center">
  <img src="Analytiq-frontend/src/assets/NavLogo.png" alt="Analytiq Logo" width="200"/>
</p>

<h1 align="center">Analytiq</h1>

<p align="center">
  <strong>Simple, Powerful Web Analytics for Everyone</strong>
</p>

<p align="center">
  A modern, intuitive web monitoring and performance analysis platform designed for founders, marketers, and non-technical users who want actionable insights without the complexity.
</p>

---

## Overview

Analytiq is a lightweight, privacy-conscious web analytics solution that provides essential website metrics in a beautifully designed, easy-to-understand dashboard. Unlike developer-focused tools like Google Analytics, Analytiq prioritizes simplicity and clarity, making it perfect for business owners who need quick answers about their website performance.

### Why Analytiq?

| Traditional Analytics | Analytiq |
|----------------------|----------|
| Complex setup and configuration | One-line script integration |
| Overwhelming metrics and reports | Focused, actionable insights |
| Steep learning curve | Intuitive, visual dashboard |
| Requires technical expertise | Designed for everyone |

---

## Features

### Core Analytics

- **Page Views Tracking** - Monitor total and unique page views across your entire website
- **Average Screen Time** - Understand how long visitors engage with your content
- **Bounce Rate Analysis** - Identify pages that need improvement
- **Session Duration** - Track meaningful user engagement over time

### Geographic Insights

- **Global Visitor Map** - Interactive world heatmap showing visitor distribution by country
- **Customizable Map Views** - Multiple color themes (Ocean Blue, Forest Green, Heat Map, etc.)
- **Zoom and Pan Controls** - Focus on specific regions of interest
- **Country Search** - Quickly locate and highlight specific countries
- **Export Capabilities** - Download geographic data for further analysis

### User Behavior Analytics

- **Scroll Depth Tracking** - Visualize how far users scroll on each page
- **Click Tracking** - Monitor user interactions and engagement patterns
- **Exit Rate Analysis** - Identify where users leave your site
- **Mouse Movement Heatmaps** - Understand user attention patterns

### Device and Technology Insights

- **Device Type Distribution** - Desktop, mobile, and tablet breakdown
- **Operating System Statistics** - Windows, macOS, iOS, Android, and more
- **Browser Analytics** - Chrome, Safari, Firefox, Edge usage
- **Screen Resolution Data** - Optimize for your audience's displays

### Performance Monitoring

- **Core Web Vitals** - First Contentful Paint (FCP), Largest Contentful Paint (LCP)
- **Cumulative Layout Shift** - Track visual stability
- **First Input Delay** - Monitor interactivity
- **Server Response Time** - Identify backend bottlenecks
- **Resource Caching Analysis** - Optimize asset delivery

### Traffic Source Analysis

- **Referrer Tracking** - Identify where your visitors come from
- **UTM Campaign Support** - Track marketing campaign effectiveness
- **Direct vs Organic Traffic** - Understand your traffic composition
- **Social Media Attribution** - Measure social platform performance

### AI-Powered Insights

- **Automated Analysis** - GPT-powered recommendations based on your data
- **Metric Deep Dives** - Ask questions about specific metrics in natural language
- **Trend Detection** - Automatic identification of significant patterns
- **Actionable Recommendations** - Receive prioritized suggestions for improvement

---


## Future Plan

Analytiq is currently built around a structured dashboard with contextual AI insights. The long term vision is to evolve it into a **fully AI driven observability platform using Agentic AI architecture**.

Instead of a fixed dashboard that looks the same for every user, Analytiq will dynamically generate **custom dashboards based on the nature of each business**. The system will analyze the website’s traffic patterns, user behavior, and performance metrics to automatically decide which charts and insights are most relevant. For example, an e commerce product may see conversion funnels and product interaction metrics, while a SaaS platform may see retention and feature usage analytics.

We also plan to introduce **multiple specialized AI agents** that analyze the analytics data from different perspectives. These agents will include domain experts such as an SEO agent, a growth and sales agent, and a developer performance agent. Each agent will combine the website’s analytics data with expert knowledge retrieved from a **Retrieval Augmented Generation (RAG) knowledge base**, allowing the system to provide more contextual and actionable insights.

Another key feature will be **agentic monitoring and intelligent alerts**. Instead of simple threshold based alerts, AI agents will continuously analyze incoming analytics data and detect anomalies such as sudden traffic drops, abnormal bounce rates, or performance degradation. When such events occur, the system will automatically notify the user and provide an explanation along with possible actions.

This AI architecture will be implemented using **Microsoft Azure AI Foundry**, which will power agent orchestration, reasoning pipelines, and RAG based knowledge retrieval. Azure AI services will allow Analytiq to coordinate multiple agents, process analytics data at scale, and generate dynamic insights and dashboards tailored to each company.

The long term goal is to move beyond traditional analytics dashboards and build an **AI first analytics system where users interact with intelligent agents that continuously analyze their website and help them make better business decisions.**


---
## Architecture

```
Analytiq/
├── Analytiq-backend/           # FastAPI Python Backend
│   ├── app/
│   │   ├── main.py             # Application entry point
│   │   ├── db.py               # DuckDB database operations
│   │   ├── aggregator.py       # Data aggregation logic
│   │   ├── models.py           # Pydantic data schemas
│   │   ├── api/                # REST API endpoints
│   │   │   ├── auth.py         # Authentication routes
│   │   │   ├── ingest.py       # Event ingestion
│   │   │   └── sites.py        # Site management
│   │   └── ai/                 # AI-powered features
│   │       ├── routers/        # AI API endpoints
│   │       └── services/       # LLM integration
│   └── client-side-sdk/        # Analytics tracking SDK
│       ├── main.js             # SDK entry point
│       ├── collectors/         # Data collection modules
│       ├── tracking/           # Event tracking modules
│       └── api/                # Backend communication
│
└── Analytiq-frontend/          # React Frontend Dashboard
    └── src/
        ├── pages/              # Main application views
        │   ├── Landing.jsx     # Public landing page
        │   ├── Auth.jsx        # Authentication
        │   ├── Manage.jsx      # Site management
        │   └── Dash.jsx        # Analytics dashboard
        └── components/         # Reusable UI components
            └── dashboardComponents/
                ├── charts/     # Visualization components
                ├── maps/       # Geographic visualizations
                ├── tables/     # Data tables
                └── cards/      # Metric cards
```

### Technology Stack

**Backend**
- FastAPI - High-performance Python web framework
- DuckDB - Embedded analytical database
- Pydantic - Data validation and serialization
- OpenAI GPT - AI-powered insights
- Qdrant - Vector database for semantic search

**Frontend**
- React 18 - Component-based UI framework
- Vite - Next-generation frontend tooling
- Recharts - Composable charting library
- React Simple Maps - Geographic visualizations
- Framer Motion - Fluid animations
- Tailwind CSS - Utility-first styling
- Lucide React - Modern icon library

**Client SDK**
- Vanilla JavaScript - Zero dependencies
- Modular architecture - Load only what you need
- Automatic batching - Efficient event transmission

---

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- pnpm (recommended) or npm

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd Analytiq-backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   # Create .env file
   DUCKDB_PATH=analytiq.db
   BACKEND_URL=http://127.0.0.1:8000
   FRONTEND_URL=http://localhost:3000
   OPENAI_API_KEY=your_openai_api_key  # Optional, for AI features
   ```

5. Start the backend server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd Analytiq-frontend
   ```

2. Install dependencies:
   ```bash
   pnpm install
   ```

3. Configure the API endpoint:
   ```javascript
   // src/config.js
   export const API_BASE_URL = 'http://localhost:8000';
   ```

4. Start the development server:
   ```bash
   pnpm dev
   ```

5. Access the dashboard at `http://localhost:3000`

---

## Integration Guide

### Adding Analytiq to Your Website

After creating a site in the Analytiq dashboard, add the tracking script to your website:

```html
<!-- Analytiq Analytics -->
<script>
  window.analytiqSiteId = "your-site-id";
  window.analytiqSiteKey = "your-site-key";
</script>
<script src="https://your-analytiq-backend.com/stats-config.js" defer></script>
```

Or use the dynamic loader with query parameters:

```html
<script src="https://your-analytiq-backend.com/stats-config.js?siteId=your-site-id&siteKey=your-site-key" defer></script>
```

### Custom Event Tracking

Track custom events using the global `analytiq` object:

```javascript
// Track a custom event
window.analytiq.track({
  event_type: 'button_click',
  payload: { button_id: 'signup-cta' }
});

// Track a purchase (e-commerce)
window.analytiq.trackPurchase({
  orderId: 'ORD-12345',
  total: 99.99,
  currency: 'USD',
  items: [{ id: 'PROD-1', name: 'Premium Plan' }]
});

// Track add to cart
window.analytiq.trackAddToCart({
  id: 'PROD-1',
  name: 'Premium Plan',
  price: 99.99
});

// Track site search
window.analytiq.trackSearch('analytics dashboard');
```

---

## Data Collected

Analytiq automatically collects the following data points:

### Page View Data
- URL and page title
- Referrer information
- Timestamp

### User Session Data
- Anonymous visitor ID (cookie-based)
- Session ID
- Session duration

### Device Information
- User agent
- Device type (desktop/mobile/tablet)
- Screen resolution
- Browser and version
- Operating system

### Performance Metrics
- Navigation timing
- DOM content loaded time
- First Contentful Paint
- Largest Contentful Paint
- First Input Delay

### Engagement Metrics
- Scroll depth percentage
- Time on page
- Click count
- Mouse movements
- Keyboard events

### Geographic Data
- Latitude and longitude (if available)
- Country (derived from coordinates)

---

## API Reference

### Authentication

```http
POST /api/register
POST /api/login
POST /api/logout
GET /api/me
```

### Site Management

```http
GET /api/sites
POST /api/sites
DELETE /api/sites/{site_id}
GET /api/dash/{site_id}
```

### Event Ingestion

```http
POST /ingest/
Headers:
  X-Site-Id: your-site-id
  X-Site-Key: your-site-key
```

### AI Insights

```http
POST /ai/chat
POST /ai/metric-chat
GET /api/sites/{site_id}/insights
```

---

## Dashboard Components

### Overview Section
- Summary statistics row with key metrics
- Traffic sources pie chart
- Devices donut chart
- New vs returning visitors gauge

### Geographic Section
- Interactive world heatmap
- Recent visitors map
- Top countries card

### Behavior Section
- Hourly visitors area chart
- Engagement radar chart
- Click and scroll heatmap
- Visitor journey flow

### Technology Section
- Operating systems bar chart
- Browsers bar chart
- Device distribution

### Performance Section
- Core Web Vitals gauges
- Performance timeline by page
- Event timeline chart

### Pages Section
- Page analytics table
- Campaign performance table

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DUCKDB_PATH` | Path to DuckDB database file | `analytiq.db` |
| `BACKEND_URL` | Public backend URL | `http://127.0.0.1:8000` |
| `FRONTEND_URL` | Frontend application URL | `http://localhost:3000` |
| `OPENAI_API_KEY` | OpenAI API key for AI features | - |
| `JWT_SECRET` | Secret key for JWT tokens | - |

### Frontend Configuration

Edit `src/config.js` to customize:
- API endpoints
- Theme colors
- Typography settings
- Animation parameters

---

## Deployment

### Backend (Production)

```bash
# Using Uvicorn with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# Or with Docker
docker build -t analytiq-backend .
docker run -p 8000:8000 analytiq-backend
```

### Frontend (Production)

```bash
# Build for production
pnpm build

# Preview production build
pnpm preview

# Deploy to Vercel
vercel deploy --prod
```

---

## Security

- All API endpoints are protected with JWT authentication
- Site keys are required for event ingestion
- CORS is configured for allowed origins
- Passwords are hashed using bcrypt
- No personally identifiable information (PII) is collected by default

---

## Performance

Analytiq is designed for minimal impact on your website:

- **Lightweight SDK** - Less than 15KB gzipped
- **Async loading** - Non-blocking script execution
- **Event batching** - Reduces network requests
- **Efficient database** - DuckDB for fast analytical queries
- **Lazy-loaded components** - Dashboard loads progressively

---

## Contributing

Contributions are welcome. Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

## License

This project is proprietary software. All rights reserved.

---

## Support

For questions, issues, or feature requests, please open an issue in the repository.

---

<p align="center">
  <sub>Built with precision for simplicity</sub>
</p>
